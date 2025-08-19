
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Estrazione dati Senato via SPARQL (con logging)
-----------------------------------------------
Legge `data/senatori.csv` (prima colonna = URL univoco del senatore),
interroga l'endpoint SPARQL di dati.senato.it con DESCRIBE (JSON‑LD
in primis, CSV come fallback), estrae i campi utili e genera:

- data/rappresentanti_senato.csv
- data/contatti_senato.csv

Note:
- I contatti (email/PEC/form) raramente sono in RDF: questo script lascia
  vuoti quei campi. Per popolarli servirà una seconda passata sulle pagine
  pubbliche del Senato.
- Rate‑limit di default: 1 req/sec (modificabile con --rps).
"""

import os
import re
import csv
import json
import time
import logging
import argparse
from io import StringIO
from datetime import date
from typing import Optional, Dict, Any, List

import requests
import pandas as pd

SPARQL_ENDPOINT = "https://dati.senato.it/sparql"

def setup_logging(verbosity: int = 1):
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    logging.basicConfig(level=level, format='[%(levelname)s] %(message)s')

def polite_sleep(last_t: float, rps: float) -> float:
    """Mantiene ~rps richieste/secondo (minimo intervallo tra chiamate)."""
    min_interval = 1.0 / max(0.01, rps)
    elapsed = time.time() - last_t
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    return time.time()

def read_input_csv(path: str) -> pd.DataFrame:
    """Legge il CSV di input provando separatori comuni e ripulendo header incollati."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input non trovato: {path}")
    # primo tentativo: virgola
    try:
        df = pd.read_csv(path, sep=",", dtype=str)
    except Exception:
        df = pd.read_csv(path, dtype=str)
    # header incollato? riprova senza sep
    if len(df.columns) == 1 and ("," in df.columns[0] or ";" in df.columns[0]):
        df = pd.read_csv(path, dtype=str)
    # normalizza colonne
    df.columns = [str(c).strip().replace("\ufeff","") for c in df.columns]
    return df.fillna("")

def pick_url_column(df: pd.DataFrame) -> str:
    """Sceglie la colonna che contiene l'URL del senatore (fallback: prima colonna)."""
    for c in df.columns:
        if "senatore" in c.lower():
            return c
    return df.columns[0]

def sparql_describe(entity_uri: str, accept: str) -> Optional[requests.Response]:
    """Esegue DESCRIBE sull'endpoint SPARQL restituendo la Response (o None)."""
    params = {"query": f"DESCRIBE <{entity_uri}>", "output": accept}
    headers = {"Accept": accept, "User-Agent": "civic-bridge/1.0 (data collection for QA)"}
    try:
        r = requests.get(SPARQL_ENDPOINT, params=params, headers=headers, timeout=25)
        if r.status_code == 200 and r.content:
            return r
        logging.warning(f"SPARQL {accept} -> {r.status_code} per {entity_uri}")
        return None
    except requests.RequestException as e:
        logging.error(f"SPARQL error ({accept}) {entity_uri}: {e}")
        return None

def lit(value: Any) -> str:
    """Estrae un literal da strutture JSON‑LD comuni."""
    if isinstance(value, list) and value:
        value = value[0]
    if isinstance(value, dict):
        if "@value" in value:
            return str(value["@value"])
        if "@id" in value:
            return str(value["@id"])
    if value is None:
        return ""
    return str(value)

def find_node_by_id(graph: List[Dict[str, Any]], node_id: str) -> Optional[Dict[str, Any]]:
    for obj in graph:
        if isinstance(obj, dict) and obj.get("@id") == node_id:
            return obj
    return None

def extract_from_jsonld(jld, entity_uri: str) -> Dict[str, str]:
    result = {
        "persona_id": entity_uri,
        "nome": "", "cognome": "",
        "carica": "senatore",
        "gruppo_partito": "",
        "circoscrizione_o_collegio": "",
        "regione": "",
        "mandato_inizio": "",
        "mandato_fine": ""
    }
    if not isinstance(jld, list):
        return result

    # Utility
    def lit(x):
        if isinstance(x, list) and x:
            x = x[0]
        if isinstance(x, dict):
            return x.get("@value") or x.get("@id") or ""
        return x or ""

    def find_node(node_id: str):
        for obj in jld:
            if isinstance(obj, dict) and obj.get("@id") == node_id:
                return obj
        return None

    # Trova root
    root = None
    for obj in jld:
        if isinstance(obj, dict) and obj.get("@id") == entity_uri:
            root = obj; break
    if not root:
        for obj in jld:
            if isinstance(obj, dict) and "@graph" in obj:
                for g in obj["@graph"]:
                    if g.get("@id") == entity_uri:
                        root = g; break
            if root: break
    if not root:
        return result

    # ---- Nome/Cognome: prova vari vocabolari
    name_keys = [
        "http://xmlns.com/foaf/0.1/firstName", "http://xmlns.com/foaf/0.1/givenName",
        "http://schema.org/givenName", "http://xmlns.com/foaf/0.1/name"
    ]
    surname_keys = [
        "http://xmlns.com/foaf/0.1/lastName", "http://xmlns.com/foaf/0.1/familyName",
        "http://schema.org/familyName"
    ]
    for k in name_keys:
        if k in root and not result["nome"]:
            result["nome"] = str(lit(root[k]))
    for k in surname_keys:
        if k in root and not result["cognome"]:
            result["cognome"] = str(lit(root[k]))

    # Alcune volte il nome completo sta in foaf:name -> split euristico
    if (not result["nome"] or not result["cognome"]) and "http://xmlns.com/foaf/0.1/name" in root:
        full = str(lit(root["http://xmlns.com/foaf/0.1/name"])).strip()
        parts = [p for p in re.split(r"\s+", full) if p]
        if len(parts) >= 2:
            result["nome"] = result["nome"] or parts[0]
            result["cognome"] = result["cognome"] or " ".join(parts[1:])

    # ---- Gruppo parlamentare: cerca nodo gruppo (per @id o @type o path)
    gruppo_label = ""
    candidate_group_ids = set()
    # collegamento diretto osr:gruppo
    if "http://dati.senato.it/osr/gruppo" in root:
        v = root["http://dati.senato.it/osr/gruppo"]
        if isinstance(v, list):
            for it in v:
                gid = it.get("@id")
                if gid: candidate_group_ids.add(gid)
        elif isinstance(v, dict):
            gid = v.get("@id")
            if gid: candidate_group_ids.add(gid)
    # scan dell'intero grafo per nodi “gruppo”
    for obj in jld:
        if isinstance(obj, dict):
            _id = obj.get("@id", "")
            _type = obj.get("@type", [])
            if isinstance(_type, str): _type = [_type]
            if "/gruppo" in _id or any("Gruppo" in str(t) for t in _type):
                candidate_group_ids.add(_id)

    def get_label(node):
        for key in [
            "http://www.w3.org/2000/01/rdf-schema#label", "rdfs:label",
            "http://xmlns.com/foaf/0.1/name", "label", "http://schema.org/name"
        ]:
            if key in node:
                return str(lit(node[key]))
        return ""

    for gid in candidate_group_ids:
        node = find_node(gid)
        if node:
            gruppo_label = get_label(node)
            if gruppo_label: break
    result["gruppo_partito"] = gruppo_label

    # ---- Mandato / regione / circoscrizione: segui osr:mandato oppure cerca nodi collegati
    mandato_id = None
    if "http://dati.senato.it/osr/mandato" in root:
        m = root["http://dati.senato.it/osr/mandato"]
        if isinstance(m, list) and m:
            mandato_id = m[0].get("@id")
        elif isinstance(m, dict):
            mandato_id = m.get("@id")

    def fill_from(node):
        mapping = {
            "http://dati.senato.it/osr/inizio": "mandato_inizio",
            "http://dati.senato.it/osr/fine": "mandato_fine",
            "http://dati.senato.it/osr/regioneElezione": "regione",
            "http://dati.senato.it/osr/circoscrizione": "circoscrizione_o_collegio",
        }
        for kin, kout in mapping.items():
            if kin in node and not result.get(kout):
                result[kout] = str(lit(node[kin]))

    if mandato_id:
        node = find_node(mandato_id)
        if node: fill_from(node)

    # fallback: cerca qualsiasi nodo che referenzi la persona e abbia quei campi
    for obj in jld:
        if isinstance(obj, dict):
            # euristica: il nodo contiene un riferimento all'entità principale
            if any(entity_uri in str(v) for v in obj.values()):
                fill_from(obj)

    # ulteriore fallback: alcune proprietà possono stare direttamente nel root
    fill_from(root)

    return result


def process_row(persona_url: str, rps: float) -> Dict[str, Dict[str, str]]:
    """
    Ritorna due dict: 'rappresentante' e 'contatti' per il senatore dato.
    Per i contatti lascia placeholder vuoti (da riempire in step HTML).
    """
    logging.info(f"Elaboro {persona_url}")
    # normalizza URL (primo token utile)
    persona_url = re.split(r"[,\s]", persona_url)[0]

    # Primo tentativo: JSON‑LD
    resp = sparql_describe(persona_url, "application/ld+json")
    data = None
    if resp is not None:
        try:
            jld = resp.json()
            logging.info("✓ JSON‑LD ottenuto")
            data = extract_from_jsonld(jld, persona_url)
        except json.JSONDecodeError:
            logging.warning("JSON‑LD non decodificabile, passo a CSV")
    else:
        logging.info("Nessun JSON‑LD, provo CSV")

    # Fallback CSV
    if data is None:
        resp2 = sparql_describe(persona_url, "text/csv")
        if resp2 is not None and resp2.text.strip():
            try:
                df = pd.read_csv(StringIO(resp2.text))
                logging.info(f"✓ CSV ottenuto ({len(df)} righe, {len(df.columns)} colonne)")
            except Exception as e:
                logging.error(f"CSV non leggibile: {e}")
        else:
            logging.error("✗ Nessun dato da SPARQL (né JSON‑LD né CSV)")
        # Se non ho potuto estrarre, creo un record minimale
        data = {
            "persona_id": persona_url,
            "nome": "", "cognome": "",
            "carica": "senatore",
            "gruppo_partito": "",
            "circoscrizione_o_collegio": "",
            "regione": "",
            "mandato_inizio": "",
            "mandato_fine": ""
        }

    logging.info(f"→ {data.get('nome','')} {data.get('cognome','')} "
                 f"[gruppo: {data.get('gruppo_partito','')}, regione: {data.get('regione','')}]")

    # Costruisci output
    today = date.today().isoformat()
    rappresentante = {
        "persona_id": data.get("persona_id", persona_url),
        "nome": data.get("nome",""),
        "cognome": data.get("cognome",""),
        "carica": "senatore",
        "gruppo_partito": data.get("gruppo_partito",""),
        "circoscrizione_o_collegio": data.get("circoscrizione_o_collegio",""),
        "regione": data.get("regione",""),
        "mandato_inizio": data.get("mandato_inizio",""),
        "mandato_fine": data.get("mandato_fine",""),
        "fonte_url": SPARQL_ENDPOINT,
        "fonte_data": today,
    }
    contatti = {
        "persona_id": data.get("persona_id", persona_url),
        "email_istituzionale": "",
        "email_pec": "",
        "form_contatti_url": "",
        "telefono_e164": "",
        "indirizzo_ufficio": "",
        "sito_ufficiale": "",
        "fonte_url": SPARQL_ENDPOINT,
        "fonte_data": today,
    }

    return {"rappresentante": rappresentante, "contatti": contatti}

def main():
    ap = argparse.ArgumentParser(description="Estrazione dati Senato via SPARQL (con logging)")
    ap.add_argument("--input", default=os.path.join("data","senatori.csv"), help="CSV input (default: data/senatori.csv)")
    ap.add_argument("--out-rappresentanti", default=os.path.join("data","rappresentanti_senato.csv"))
    ap.add_argument("--out-contatti", default=os.path.join("data","contatti_senato.csv"))
    ap.add_argument("--rps", type=float, default=1.0, help="Richieste per secondo (default: 1.0)")
    ap.add_argument("-v", "--verbose", action="count", default=1, help="-v info, -vv debug")
    args = ap.parse_args()

    setup_logging(args.verbose)

    df = read_input_csv(args.input)
    col_url = pick_url_column(df)
    logging.info(f"Colonna URL rilevata: {col_url}")

    rapp_rows = []
    cont_rows = []
    last_t = 0.0

    for idx, row in df.iterrows():
        persona_url = str(row[col_url]).strip()
        if not persona_url:
            logging.debug(f"[{idx}] URL vuoto, skip")
            continue
        out = process_row(persona_url, args.rps)
        rapp_rows.append(out["rappresentante"])
        cont_rows.append(out["contatti"])
        last_t = polite_sleep(last_t, args.rps)

    os.makedirs(os.path.dirname(args.out_rappresentanti), exist_ok=True)
    pd.DataFrame(rapp_rows).to_csv(args.out_rappresentanti, index=False, quoting=csv.QUOTE_MINIMAL)
    pd.DataFrame(cont_rows).to_csv(args.out_contatti, index=False, quoting=csv.QUOTE_MINIMAL)

    logging.info(f"Salvato: {args.out_rappresentanti} ({len(rapp_rows)} righe)")
    logging.info(f"Salvato: {args.out_contatti} ({len(cont_rows)} righe)")
    logging.info("Nota: per email/PEC/form serve una seconda passata HTML sulle schede senato.it")

if __name__ == "__main__":
    main()
