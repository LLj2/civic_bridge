#!/usr/bin/env python3
"""
Civic Bridge - Sistema di lookup unificato
Mappa indirizzi italiani (CAP/Comune) ai rappresentanti eletti (Camera, Senato, EU)
"""

import pandas as pd
import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Any
import re
import numpy as np

def clean_for_json(obj):
    """Convert pandas/numpy types to JSON-serializable types"""
    if isinstance(obj, (np.integer, pd.Int64Dtype)):
        return int(obj)
    elif isinstance(obj, (np.floating, pd.Float64Dtype)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return ""
    elif obj is None:
        return ""
    else:
        return str(obj).strip()

class CivicLookup:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        
        # Cache per le lookup tables
        self._comuni_cache = None
        self._collegi_camera_cache = None
        self._collegi_senato_cache = None
        self._deputati_cache = None
        self._senatori_cache = None
        self._mep_cache = None
        self._eu_constituencies = None
        
    def load_data(self):
        """Carica tutti i dataset necessari"""
        print("Caricamento dati...")
        
        # Carica comuni e mappature geografiche
        self._comuni_cache = pd.read_csv(self.data_dir / "comuni.csv")
        self._collegi_camera_cache = pd.read_csv(self.data_dir / "collegi_camera.csv")
        self._collegi_senato_cache = pd.read_csv(self.data_dir / "collegi_senato.csv")
        
        # Carica rappresentanti eletti - usa i file completi estratti
        if (self.data_dir.parent / "contatti_camera.csv").exists():
            self._deputati_cache = pd.read_csv(self.data_dir.parent / "contatti_camera.csv")
        elif (self.data_dir.parent / "contatti_enhanced.csv").exists():
            self._deputati_cache = pd.read_csv(self.data_dir.parent / "contatti_enhanced.csv")
        elif (self.data_dir.parent / "test_contatti.csv").exists():
            self._deputati_cache = pd.read_csv(self.data_dir.parent / "test_contatti.csv")
            
        if (self.data_dir.parent / "contatti_senato.csv").exists():
            self._senatori_cache = pd.read_csv(self.data_dir.parent / "contatti_senato.csv")
        elif (self.data_dir.parent / "contatti_senato_clean.csv").exists():
            self._senatori_cache = pd.read_csv(self.data_dir.parent / "contatti_senato_clean.csv")
            
        if (self.data_dir.parent / "contatti_eu.csv").exists():
            self._mep_cache = pd.read_csv(self.data_dir.parent / "contatti_eu.csv")
        
        # Definizione circoscrizioni EU
        self._eu_constituencies = {
            "Nord-occidentale": ["Piemonte", "Valle d'Aosta", "Liguria", "Lombardia"],
            "Nord-orientale": ["Veneto", "Trentino-Alto Adige", "Friuli-Venezia Giulia", "Emilia-Romagna"],  
            "Centrale": ["Toscana", "Umbria", "Marche", "Lazio"],
            "Meridionale": ["Abruzzo", "Molise", "Campania", "Puglia", "Basilicata", "Calabria"],
            "Insulare": ["Sicilia", "Sardegna"]
        }
        
        print(f"Caricati: {len(self._comuni_cache)} comuni")
        print(f"Caricati: {len(self._collegi_camera_cache)} collegi Camera")  
        print(f"Caricati: {len(self._collegi_senato_cache)} collegi Senato")
        if self._deputati_cache is not None:
            print(f"Caricati: {len(self._deputati_cache)} deputati")
        if self._senatori_cache is not None:
            print(f"Caricati: {len(self._senatori_cache)} senatori")
        if self._mep_cache is not None:
            print(f"Caricati: {len(self._mep_cache)} MEP")
    
    def get_comune_info(self, search_term: str) -> Optional[Dict]:
        """Trova informazioni comune da CAP, nome comune o codice ISTAT"""
        if self._comuni_cache is None:
            return None
            
        search_term = str(search_term).strip().upper()
        
        # Cerca per CAP (se numerico)
        if search_term.isdigit():
            # TODO: implementare lookup CAP quando avremo il file cap_to_comune.csv
            pass
        
        # Cerca per nome comune - prima esatto, poi contiene
        # 1. Prova match esatto
        exact_match = self._comuni_cache[
            self._comuni_cache['comune'].str.upper() == search_term
        ]
        
        if not exact_match.empty:
            match = exact_match
        else:
            # 2. Fallback a contiene
            match = self._comuni_cache[
                self._comuni_cache['comune'].str.upper().str.contains(search_term, na=False, regex=False)
            ]
        
        if not match.empty:
            row = match.iloc[0]
            return {
                'istat_comune': clean_for_json(row['istat_comune']),
                'comune': clean_for_json(row['comune']),
                'provincia': clean_for_json(row['provincia']), 
                'regione': clean_for_json(row['regione'])
            }
        
        return None
    
    def get_camera_representatives(self, istat_comune: str) -> List[Dict]:
        """Ottieni deputati per comune"""
        if self._collegi_camera_cache is None or self._deputati_cache is None:
            return []
        
        # Trova collegio Camera per questo comune
        collegio_match = self._collegi_camera_cache[
            self._collegi_camera_cache['istat_comune'] == istat_comune
        ]
        
        if collegio_match.empty:
            return []
            
        collegio_id = collegio_match.iloc[0]['collegio_camera_id']
        
        # Trova deputati per questo collegio - handle format differences
        deputati = []
        collegio_id_upper = str(collegio_id).upper()
        
        # Extract region from collegio_id (e.g., LAZIO-P01 -> LAZIO)
        region_part = collegio_id_upper.split('-')[0]
        
        for _, deputato in self._deputati_cache.iterrows():
            deputato_collegio = str(deputato.get('collegio', '')).upper()
            
            # Match by region - if deputato collegio starts with same region
            # This handles cases like LAZIO-P01 matching LAZIO 1 - P01, LAZIO 2 - P01, etc.
            if deputato_collegio.startswith(region_part):
                deputati.append({
                    'tipo': 'deputato',
                    'nome': clean_for_json(deputato.get('nome', '')),
                    'cognome': clean_for_json(deputato.get('cognome', '')),
                    'gruppo_partito': clean_for_json(deputato.get('gruppo_partito', '')),
                    'collegio': clean_for_json(deputato.get('collegio', '')),
                    'email': clean_for_json(deputato.get('email_istituzionale', '')),
                    'form_url': clean_for_json(deputato.get('form_contatti_url', '')),
                    'istituzione': 'Camera dei Deputati'
                })
        
        return deputati
    
    def get_senato_representatives(self, regione: str) -> List[Dict]:
        """Ottieni senatori per regione"""
        if self._senatori_cache is None:
            return []
        
        senatori = []
        for _, senatore in self._senatori_cache.iterrows():
            senatore_regione = clean_for_json(senatore.get('regione', ''))
            if senatore_regione.upper() == regione.upper():
                senatori.append({
                    'tipo': 'senatore', 
                    'nome': clean_for_json(senatore.get('nome', '')),
                    'cognome': clean_for_json(senatore.get('cognome', '')),
                    'gruppo_partito': clean_for_json(senatore.get('gruppo_partito', '')),
                    'regione': clean_for_json(senatore.get('regione', '')),
                    'email': clean_for_json(senatore.get('email_istituzionale', '')),
                    'sito_ufficiale': clean_for_json(senatore.get('sito_ufficiale', '')),
                    'istituzione': 'Senato della Repubblica'
                })
        
        return senatori
    
    def get_eu_representatives(self, regione: str) -> List[Dict]:
        """Ottieni MEP per regione"""
        if self._mep_cache is None:
            return []
        
        # Trova circoscrizione EU per questa regione
        circoscrizione = None
        for circ, regioni in self._eu_constituencies.items():
            if regione in regioni:
                circoscrizione = circ
                break
        
        if not circoscrizione:
            return []
        
        mep_list = []
        for _, mep in self._mep_cache.iterrows():
            if clean_for_json(mep.get('circoscrizione_eu', '')) == circoscrizione:
                mep_list.append({
                    'tipo': 'deputato_europeo',
                    'nome': clean_for_json(mep.get('nome', '')),
                    'cognome': clean_for_json(mep.get('cognome', '')),
                    'gruppo_partito': clean_for_json(mep.get('gruppo_partito', '')),
                    'circoscrizione_eu': clean_for_json(mep.get('circoscrizione_eu', '')),
                    'email': clean_for_json(mep.get('email_istituzionale', '')),
                    'form_url': clean_for_json(mep.get('form_contatti_url', '')),
                    'istituzione': 'Parlamento Europeo'
                })
        
        return mep_list
    
    def lookup_representatives(self, search_term: str) -> Dict[str, Any]:
        """Lookup principale: restituisce tutti i rappresentanti per un dato indirizzo"""
        # Ottieni info comune
        comune_info = self.get_comune_info(search_term)
        if not comune_info:
            return {
                'success': False,
                'error': f'Comune non trovato per: {search_term}',
                'representatives': []
            }
        
        # Ottieni rappresentanti per tutti e tre i livelli
        deputati = self.get_camera_representatives(comune_info['istat_comune'])
        senatori = self.get_senato_representatives(comune_info['regione'])
        mep = self.get_eu_representatives(comune_info['regione'])
        
        result = {
            'success': True,
            'location': comune_info,
            'representatives': {
                'camera': deputati,
                'senato': senatori, 
                'eu_parliament': mep
            },
            'summary': {
                'total_representatives': len(deputati) + len(senatori) + len(mep),
                'deputati_count': len(deputati),
                'senatori_count': len(senatori),
                'mep_count': len(mep)
            }
        }
        
        return result

def main():
    """Test del sistema di lookup"""
    lookup = CivicLookup()
    lookup.load_data()
    
    # Test con alcuni comuni
    test_cases = ["Milano", "Roma", "Genova", "Agliè"]
    
    for test in test_cases:
        print(f"\n=== LOOKUP per: {test} ===")
        result = lookup.lookup_representatives(test)
        
        if result['success']:
            location = result['location']
            print(f"LOCATION: {location['comune']} ({location['provincia']}) - {location['regione']}")
            
            print(f"\nTotale rappresentanti: {result['summary']['total_representatives']}")
            
            # Camera
            if result['representatives']['camera']:
                print(f"\nCAMERA DEI DEPUTATI ({result['summary']['deputati_count']}):")
                for dep in result['representatives']['camera']:
                    print(f"  - {dep['nome']} {dep['cognome']} ({dep['gruppo_partito']}) - {dep['email']}")
            
            # Senato
            if result['representatives']['senato']:
                print(f"\nSENATO DELLA REPUBBLICA ({result['summary']['senatori_count']}):")
                for sen in result['representatives']['senato']:
                    print(f"  - {sen['nome']} {sen['cognome']} ({sen['gruppo_partito']}) - {sen['email']}")
            
            # EU Parliament
            if result['representatives']['eu_parliament']:
                print(f"\nPARLAMENTO EUROPEO ({result['summary']['mep_count']}):")
                for mep in result['representatives']['eu_parliament']:
                    print(f"  - {mep['nome']} {mep['cognome']} ({mep['gruppo_partito']}) - {mep['circoscrizione_eu']}")
        else:
            print(f"ERROR: {result['error']}")

if __name__ == "__main__":
    main()