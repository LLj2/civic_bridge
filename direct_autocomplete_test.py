#!/usr/bin/env python3
"""
Direct test of autocomplete functionality to isolate the pandas error
"""
import sys
import traceback
import pandas as pd
from civic_lookup import CivicLookup, clean_for_json

def test_autocomplete_direct():
    """Test the exact same logic as the API server"""
    print("Testing autocomplete logic directly...")
    
    # Initialize lookup (same as server)
    try:
        lookup = CivicLookup()
        lookup.load_data()
        print(f"Lookup initialized successfully")
    except Exception as e:
        print(f"ERROR: Failed to initialize lookup: {e}")
        traceback.print_exc()
        return
    
    if lookup._comuni_cache is None:
        print("ERROR: Comuni data not loaded")
        return
    
    # Test params (same as API call)
    query = "roma"
    limit = 10
    
    print(f"Testing with query='{query}', limit={limit}")
    print(f"Comuni cache loaded: {len(lookup._comuni_cache)} entries")
    print(f"Comuni cache type: {type(lookup._comuni_cache)}")
    print(f"Comuni cache columns: {list(lookup._comuni_cache.columns)}")
    
    # Start the exact same logic as API
    query_upper = query.upper()
    
    try:
        print("Step 1: Copying DataFrame...")
        comuni_df = lookup._comuni_cache.copy()
        print(f"DataFrame copied successfully, shape: {comuni_df.shape}")
    except Exception as e:
        print(f"ERROR: Failed to copy DataFrame: {e}")
        traceback.print_exc()
        return
    
    try:
        print("Step 2: Starting search logic...")
        results = []
        
        # Convert to list of dicts to avoid pandas iteration issues
        comuni_data = []
        for idx, row in comuni_df.iterrows():
            try:
                comune_val = row.get('comune')
                if pd.isna(comune_val) or comune_val is None:
                    continue
                comune_str = str(comune_val).strip()
                if not comune_str:
                    continue
                
                comuni_data.append({
                    'comune': comune_str,
                    'provincia': clean_for_json(row.get('provincia', '')),
                    'regione': clean_for_json(row.get('regione', ''))
                })
            except Exception as e:
                print(f"WARNING: Error processing row {idx}: {e}")
                continue
        
        print(f"Step 3: Converted {len(comuni_data)} comuni to clean format")
        
        # Now search in the clean data
        for comune_data in comuni_data:
            comune_name = comune_data['comune'].upper()
            
            # Calculate relevance score
            score = None
            if comune_name == query_upper:
                score = 1  # Exact match
            elif comune_name.startswith(query_upper):
                score = 2  # Starts with
            elif query_upper in comune_name:
                score = 3  # Contains
            
            if score is not None:
                result_item = {
                    'score': score,
                    'comune': comune_data['comune'],
                    'provincia': comune_data['provincia'],
                    'regione': comune_data['regione'],
                }
                result_item['display'] = f"{result_item['comune']} ({result_item['provincia']}) - {result_item['regione']}"
                results.append(result_item)
        
        print(f"Step 4: Found {len(results)} matches")
        
        # Sort by score and take top results
        results.sort(key=lambda x: x['score'])
        results = results[:limit]
        
        # Remove score from final results
        for result in results:
            del result['score']
        
        print(f"Final results ({len(results)}):")
        for result in results[:5]:  # Show first 5
            print(f"  - {result['display']}")
        
        print("SUCCESS: Autocomplete logic completed without errors")
        
    except Exception as e:
        print(f"ERROR: Failed in search logic: {e}")
        traceback.print_exc()
        return

if __name__ == "__main__":
    test_autocomplete_direct()