#!/usr/bin/env python3
"""
Estrazione contatti e dati biografici dei senatori
- Input: senatori.csv (colonna 'senatore' con URI contenente ID, es. http://dati.senato.it/senatore/32)
- Output: contatti_senato.csv con email e dati biografici (nome, cognome, gruppo, etc.)
"""

import argparse
import csv
import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import date
import pandas as pd

def estrai_id_senatore(senatore_uri: str) -> str:
    """Estrae l'ID numerico dall'URI del senatore"""
    if not isinstance(senatore_uri, str):
        return None
    m = re.search(r"/(\d+)$", senatore_uri)
    return m.group(1) if m else None

def fetch_data_from_senate_page(sen_id: str):
    """Estrae email e dati biografici dalla pagina ufficiale del senatore"""
    url = f"https://www.senato.it/leg/19/BGT/Schede/Attsen/{sen_id:0>8}.htm"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return {}, url
        
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        
        data = {}
        
        # Email
        m = re.search(r"[a-zA-Z0-9._%+-]+@senato\.it", text, re.IGNORECASE)
        data["email"] = m.group(0).lower() if m else None
        
        # Gruppo parlamentare - cerca "Membro Gruppo XXX"
        m = re.search(r"Membro Gruppo ([A-Z0-9-]+)", text)  # Solo sigla gruppo
        if not m:
            # Fallback: cerca pattern più lungo ma taglia alla prima parola chiave
            m = re.search(r"Membro Gruppo ([^\r\n]+)", text)
            if m:
                gruppo = m.group(1).strip()
                # Taglia alla prima parola che indica inizio di altra info
                gruppo = re.split(r"(?i)(Ministro|Sottosegretario|Commissario|Membro della|Contatti)", gruppo)[0].strip()
                data["gruppo_partito"] = gruppo
            else:
                data["gruppo_partito"] = ""
        else:
            data["gruppo_partito"] = m.group(1).strip()
        
        # Regione di elezione  
        m = re.search(r"Regione di elezione:\s*([^-\r\n]+)", text)
        if m:
            regione = m.group(1).strip()
            # Rimuovi eventuali caratteri extra
            regione = regione.split("Nato")[0].split("Nata")[0].strip()
            data["regione"] = regione
        else:
            data["regione"] = ""
        
        # Collegio - cerca "Collegio: X (dettagli)"
        m = re.search(r"Collegio:\s*([^)]+\))", text)
        data["collegio"] = m.group(1).strip() if m else ""
        
        return data, url
    except Exception:
        return {}, url

def main(input_csv, output_csv, start=0, end=None, rps=1.0):
    df = pd.read_csv(input_csv)
    if "senatore" not in df.columns:
        raise ValueError("CSV deve contenere colonna 'senatore' con URI senatore")

    # Deduplica per senatore_id per evitare duplicati
    df_unique = df.drop_duplicates(subset=["senatore"])
    
    results = []
    today = date.today().isoformat()
    processed_ids = set()

    if end is None or end > len(df_unique):
        end = len(df_unique)

    for idx, row in df_unique.iloc[start:end].iterrows():
        senatore_uri = row["senatore"]
        senatore_id = estrai_id_senatore(senatore_uri)
        if not senatore_id or senatore_id in processed_ids:
            continue
            
        processed_ids.add(senatore_id)
        data, fonte_url = fetch_data_from_senate_page(senatore_id)
        
        results.append({
            "persona_id": senatore_id,
            "nome": row.get("nome", "").strip(),
            "cognome": row.get("cognome", "").strip(),
            "inizio_mandato": row.get("inizioMandato", ""),
            "legislatura": row.get("legislatura", ""),
            "tipo_mandato": row.get("tipoMandato", ""),
            "carica": "senatore",
            "gruppo_partito": data.get("gruppo_partito", ""),
            "circoscrizione_o_collegio": data.get("collegio", ""),
            "regione": data.get("regione", ""),
            "email_istituzionale": data.get("email", "") or "",
            "email_pec": "",
            "form_contatti_url": "",
            "telefono_e164": "",
            "indirizzo_ufficio": "",
            "sito_ufficiale": fonte_url,
            "fonte_url": fonte_url,
            "fonte_data": today
        })
        print(f"Processato: {row.get('nome', '')} {row.get('cognome', '')} ({data.get('gruppo_partito', 'NO GROUP')}) -> {data.get('email', 'NO EMAIL')}")
        time.sleep(1.0 / rps)

    # Scrivi CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "persona_id","nome","cognome","inizio_mandato","legislatura","tipo_mandato","carica",
            "gruppo_partito","circoscrizione_o_collegio","regione",
            "email_istituzionale","email_pec","form_contatti_url",
            "telefono_e164","indirizzo_ufficio","sito_ufficiale","fonte_url","fonte_data"
        ])
        writer.writeheader()
        for r in results:
            writer.writerow(r)
            
    print(f"Completato! {len(results)} senatori salvati in {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estrai contatti senatori")
    parser.add_argument("--input", required=True, help="CSV input (senatori.csv)")
    parser.add_argument("--output", required=True, help="CSV output")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=None)
    parser.add_argument("--rps", type=float, default=1.0, help="Richieste per secondo")
    args = parser.parse_args()
    main(args.input, args.output, args.start, args.end, args.rps)