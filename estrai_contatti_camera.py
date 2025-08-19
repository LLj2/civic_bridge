#!/usr/bin/env python3
"""
Estrazione contatti e dati biografici dei deputati Camera
- Input: dep_bio.csv (colonna 'persona' con URI contenente id_aul, es. http://dati.camera.it/ocd/persona.rdf/p308763)
- Output: contatti.csv con email, form contatti e dati biografici (nome, cognome, gruppo, collegio, etc.)
"""

import argparse
import csv
import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import date
import pandas as pd

def estrai_id_aul(persona_uri: str) -> str:
    # estrae il numero da pNNNNN
    if not isinstance(persona_uri, str):
        return None
    m = re.search(r"p(\d+)$", persona_uri)
    return m.group(1) if m else None

def fetch_email_from_form(id_aul: str):
    url = f"https://scrivi.camera.it/scrivi?dest=deputato&id_aul={id_aul}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None, url
        soup = BeautifulSoup(r.text, "html.parser")
        # Cerca pattern email con case insensitive
        text = soup.get_text(" ", strip=True)
        m = re.search(r"[a-zA-Z0-9._%+-]+@camera\.it", text, re.IGNORECASE)
        return (m.group(0).lower() if m else None, url)
    except Exception:
        return None, url

def main(input_csv, output_csv, start=0, end=None, rps=1.0):
    df = pd.read_csv(input_csv)
    if "persona" not in df.columns:
        raise ValueError("CSV deve contenere colonna 'persona' con URI deputato")

    # Deduplica per persona_id per evitare duplicati
    df_unique = df.drop_duplicates(subset=["persona"])
    
    results = []
    today = date.today().isoformat()
    processed_ids = set()  # Tracking per sicurezza aggiuntiva

    if end is None or end > len(df_unique):
        end = len(df_unique)

    for idx, row in df_unique.iloc[start:end].iterrows():
        persona_uri = row["persona"]
        persona_id = estrai_id_aul(persona_uri)
        if not persona_id or persona_id in processed_ids:
            continue
            
        processed_ids.add(persona_id)
        email, form_url = fetch_email_from_form(persona_id)
        results.append({
            "persona_id": persona_id,
            "nome": row.get("nome", "").strip(),
            "cognome": row.get("cognome", "").strip(),
            "data_nascita": row.get("dataNascita", ""),
            "luogo_nascita": row.get("luogoNascita", ""),
            "genere": row.get("genere", ""),
            "collegio": row.get("collegio", ""),
            "gruppo_partito": row.get("nomeGruppo", ""),
            "sigla_gruppo": row.get("sigla", ""),
            "commissione": row.get("commissione", ""),
            "email_istituzionale": email or "",
            "email_pec": "",
            "form_contatti_url": form_url,
            "telefono_e164": "",
            "indirizzo_ufficio": "",
            "sito_ufficiale": row.get("pagina", ""),
            "fonte_url": form_url,
            "fonte_data": today
        })
        time.sleep(1.0 / rps)

    # Scrivi CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "persona_id","nome","cognome","data_nascita","luogo_nascita","genere",
            "collegio","gruppo_partito","sigla_gruppo","commissione",
            "email_istituzionale","email_pec","form_contatti_url",
            "telefono_e164","indirizzo_ufficio","sito_ufficiale","fonte_url","fonte_data"
        ])
        writer.writeheader()
        for r in results:
            writer.writerow(r)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estrai contatti deputati Camera")
    parser.add_argument("--input", required=True, help="CSV input (dep_bio.csv)")
    parser.add_argument("--output", required=True, help="CSV output (contatti.csv)")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=None)
    parser.add_argument("--rps", type=float, default=1.0, help="Richieste per secondo (max 1.0)")
    args = parser.parse_args()
    main(args.input, args.output, args.start, args.end, args.rps)
