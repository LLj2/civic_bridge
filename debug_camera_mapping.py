#!/usr/bin/env python3
"""
Debug Camera representatives mapping
"""
from civic_lookup import CivicLookup

def debug_camera_mapping():
    lookup = CivicLookup()
    lookup.load_data()
    
    print(f"Camera deputies loaded: {len(lookup._deputati_cache) if lookup._deputati_cache is not None else 0}")
    
    if lookup._deputati_cache is not None:
        print("Sample deputati:")
        print(lookup._deputati_cache[['nome', 'cognome', 'collegio']].head())
        print(f"Unique collegi: {lookup._deputati_cache['collegio'].nunique()}")
        print("Sample collegi values:")
        print(lookup._deputati_cache['collegio'].value_counts().head())
    
    print(f"\nCollegi Camera loaded: {len(lookup._collegi_camera_cache) if lookup._collegi_camera_cache is not None else 0}")
    
    if lookup._collegi_camera_cache is not None:
        print("Sample collegi Camera:")
        print(lookup._collegi_camera_cache.head())
        print("Unique collegio_camera_id:")
        print(lookup._collegi_camera_cache['collegio_camera_id'].value_counts().head())
    
    # Test specific mapping for Roma
    print(f"\n=== Testing Roma Camera mapping ===")
    roma_info = lookup.get_comune_info("Roma")
    if roma_info:
        print(f"Roma istat_comune: {roma_info['istat_comune']}")
        
        # Find collegio Camera for Roma
        collegio_match = lookup._collegi_camera_cache[
            lookup._collegi_camera_cache['istat_comune'] == roma_info['istat_comune']
        ]
        print(f"Roma collegio matches: {len(collegio_match)}")
        if not collegio_match.empty:
            collegio_id = collegio_match.iloc[0]['collegio_camera_id']
            print(f"Roma collegio_camera_id: {collegio_id}")
            
            # Find deputati for this collegio
            deputati = lookup._deputati_cache[
                lookup._deputati_cache['collegio'].astype(str).str.upper() == str(collegio_id).upper()
            ]
            print(f"Deputati found for collegio {collegio_id}: {len(deputati)}")
            if len(deputati) > 0:
                print(deputati[['nome', 'cognome', 'collegio']].head())

if __name__ == "__main__":
    debug_camera_mapping()