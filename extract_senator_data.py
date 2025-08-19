
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Estrazione dati Senato (legislatura corrente) dai rawdata ufficiali
-------------------------------------------------------------------
Input:
  - data/senatori.csv   (separatore ",", prima colonna = URL univoco del senatore)
Output:
  - data/rappresentanti_senato.csv
  - data/contatti_senato.csv
  - data/senatori_arricchiti_raw.csv
Uso:
  python extract_senator_data_FIXED.py
Note:
  - Rispetta i rate‑limit (sleep tra richieste).
  - Gestisce 404/500 senza interrompere l'esecuzione.
  - Estrae i campi in modo "flessibile" perché i rawdata possono avere intestazioni diverse.
"""

import os
import re
import time
import csv
import requests
import pandas as pd
from io import StringIO
from datetime import date

INPUT_FILE = os.path.join("data", "senatori_test.csv")
OUT_RAPPR = os.path.join("data", "rappresentanti_senato.csv")
OUT_CONTATTI = os.path.join("data", "contatti_senato.csv")
OUT_RAW = os.path.join("data", "senatori_arricchiti_raw.csv")

RPS = 1.0  # richieste al secondo (1.0 = 1 request/sec)
TIMEOUT = 15

def get_first(df, candidates, default=""):
    for c in candidates:
        if c in df.columns:
            val = df[c].iloc[0]
            if pd.notna(val):
                return str(val).strip()
    return default

def fetch_rawdata_df(sen_id: str) -> pd.DataFrame | None:
    url = f"https://dati.senato.it/senatore/{sen_id}/rawdata.csv"
    try:
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code != 200:
            print(f"[WARN] {url} -> {r.status_code}")
            return None
        # Alcuni CSV possono avere separatore ',' standard
        df = pd.read_csv(StringIO(r.text))
        if df.empty:
            print(f"[WARN] {url} -> CSV vuoto")
            return None
        # Normalizza intestazioni rimuovendo spazi/BOM
        df.columns = [str(c).strip().replace("\ufeff","") for c in df.columns]
        df["_fonte_url"] = url
        return df
    except Exception as e:
        print(f"[ERR] {url} -> {e}")
        return None

def main():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"Input non trovato: {INPUT_FILE}")

    # Legge input con separatore ","
    df_in = pd.read_csv(INPUT_FILE, sep=",")
    # Se per caso l'intero header è una sola colonna, riprova senza sep
    if len(df_in.columns) == 1 and "," in df_in.columns[0]:
        df_in = pd.read_csv(INPUT_FILE)

    # Prova a determinare il nome della colonna con l'URL
    col_url = None
    for c in df_in.columns:
        if "senatore" in c.lower():
            col_url = c
            break
    if col_url is None:
        # fallback: prima colonna
        col_url = df_in.columns[0]

    print(f"[INFO] Colonna URL rilevata: {col_url}")

    rapp_rows = []
    cont_rows = []
    raw_rows = []

    today = date.today().isoformat()
    min_interval = 1.0 / max(0.01, RPS)
    t0 = 0.0

    for idx, row in df_in.iterrows():
        persona_url = str(row[col_url]).strip()
        # L'URL può essere del tipo: https://dati.senato.it/senatore/36381
        # o talvolta contenere altri valori; estrai l'ultimo segmento numerico
        m = re.search(r"/(\d+)", persona_url)
        if not m:
            print(f"[SKIP] Riga {idx}: URL non valido -> {persona_url}")
            continue
        sen_id = m.group(1)

        df_raw = fetch_rawdata_df(sen_id)
        if df_raw is None:
            continue

        # Estrazioni "flessibili"
        nome = get_first(df_raw, ["nome","Nome","firstName"], default=row.get("nome",""))
        cognome = get_first(df_raw, ["cognome","Cognome","lastName"], default=row.get("cognome",""))
        gruppo = get_first(df_raw, ["gruppo","Gruppo","gruppoParlamentare","gruppo_parlamentare"])
        collegio = get_first(df_raw, ["collegio","Collegio","circoscrizione","Circoscrizione","regioneElezione"])
        regione = get_first(df_raw, ["regione","Regione","regioneElezione","Regione di elezione"])
        inizio = get_first(df_raw, ["inizioMandato","inizio","dataInizio","start","inizio_mandato"], default=row.get("inizioMandato",""))
        fine = get_first(df_raw, ["fineMandato","fine","dataFine","end","fine_mandato"], default="")
        email = get_first(df_raw, ["email","posta","postaElettronica","mail","e_mail"])
        pec = get_first(df_raw, ["pec","postaCertificata","pec_istituzionale"])
        form = get_first(df_raw, ["form","formContatti","form_contatti","contatti"])
        telefono = get_first(df_raw, ["telefono","telefonoUfficio","telefono_e164"])
        ufficio = get_first(df_raw, ["ufficio","indirizzoUfficio","sede"])
        sito = get_first(df_raw, ["sito","sitoUfficiale","urlScheda","scheda","pagina"])
        fonte_url = get_first(df_raw, ["_fonte_url"], default=f"https://dati.senato.it/senatore/{sen_id}/rawdata.csv")

        # Rappresentanti
        rapp_rows.append({
            "persona_id": f"https://dati.senato.it/senatore/{sen_id}",
            "nome": str(nome).title(),
            "cognome": str(cognome).title(),
            "carica": "senatore",
            "gruppo_partito": gruppo,
            "circoscrizione_o_collegio": collegio,
            "regione": regione,
            "mandato_inizio": inizio,
            "mandato_fine": fine,
            "fonte_url": fonte_url,
            "fonte_data": today,
        })

        # Contatti
        cont_rows.append({
            "persona_id": f"https://dati.senato.it/senatore/{sen_id}",
            "email_istituzionale": (email or "").lower(),
            "email_pec": (pec or "").lower(),
            "form_contatti_url": form,
            "telefono_e164": telefono,
            "indirizzo_ufficio": ufficio,
            "sito_ufficiale": sito,
            "fonte_url": fonte_url,
            "fonte_data": today,
        })

        # Arricchito raw (qualche campo utile per QA)
        raw_rows.append({
            "persona_id": f"https://dati.senato.it/senatore/{sen_id}",
            "nome": nome, "cognome": cognome, "gruppo": gruppo,
            "collegio": collegio, "regione": regione,
            "inizioMandato": inizio, "fineMandato": fine,
            "email": email, "pec": pec, "form": form, "telefono": telefono,
            "ufficio": ufficio, "sito": sito, "fonte_url": fonte_url, "fonte_data": today
        })

        # rate-limit
        elapsed = time.time() - t0
        sleep_needed = min_interval - elapsed if elapsed < min_interval else 0
        if sleep_needed > 0:
            time.sleep(sleep_needed)
        t0 = time.time()

    # Salvataggi
    os.makedirs("data", exist_ok=True)
    pd.DataFrame(rapp_rows).to_csv(OUT_RAPPR, index=False, quoting=csv.QUOTE_MINIMAL)
    pd.DataFrame(cont_rows).to_csv(OUT_CONTATTI, index=False, quoting=csv.QUOTE_MINIMAL)
    pd.DataFrame(raw_rows).to_csv(OUT_RAW, index=False, quoting=csv.QUOTE_MINIMAL)

    print(f"[DONE] rappresentanti: {len(rapp_rows)}  -> {OUT_RAPPR}")
    print(f"[DONE] contatti:       {len(cont_rows)}  -> {OUT_CONTATTI}")
    print(f"[DONE] arricchiti:     {len(raw_rows)}   -> {OUT_RAW}")

if __name__ == "__main__":
    main()
