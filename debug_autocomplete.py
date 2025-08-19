#!/usr/bin/env python3
"""
Debug script for autocomplete pandas error
"""
import pandas as pd
import numpy as np
from civic_lookup import CivicLookup

def debug_autocomplete():
    print("Loading civic lookup system...")
    lookup = CivicLookup()
    lookup.load_data()
    
    if lookup._comuni_cache is None:
        print("ERROR: Comuni data not loaded")
        return
        
    print(f"Loaded {len(lookup._comuni_cache)} comuni")
    print(f"DataFrame dtypes:\n{lookup._comuni_cache.dtypes}")
    print(f"DataFrame info:")
    print(lookup._comuni_cache.info())
    
    # Check for NaN values
    print(f"\nNaN values per column:")
    print(lookup._comuni_cache.isnull().sum())
    
    # Try the problematic operations step by step
    query = "roma"
    query_upper = query.upper()
    
    print(f"\nTesting search for: {query_upper}")
    
    # Test 1: Copy dataframe
    try:
        comuni_df = lookup._comuni_cache.copy()
        print("OK DataFrame copy successful")
    except Exception as e:
        print(f"ERROR DataFrame copy failed: {e}")
        return
        
    # Test 2: Check comune column
    try:
        print(f"Comune column type: {comuni_df['comune'].dtype}")
        print(f"Sample comune values:")
        print(comuni_df['comune'].head())
        print(f"Unique values in comune column: {comuni_df['comune'].nunique()}")
    except Exception as e:
        print(f"ERROR Comune column inspection failed: {e}")
        return
        
    # Test 3: Drop NaN
    try:
        print(f"Before dropna: {len(comuni_df)} rows")
        comuni_df = comuni_df.dropna(subset=['comune'])
        print(f"After dropna: {len(comuni_df)} rows")
        print("OK dropna successful")
    except Exception as e:
        print(f"ERROR dropna failed: {e}")
        return
        
    # Test 4: String operations
    try:
        print("Testing string operations...")
        # Convert to string first
        comuni_df_test = comuni_df.copy()
        comuni_df_test['comune_str'] = comuni_df_test['comune'].astype(str)
        print("OK astype(str) successful")
        
        # Test strip
        comuni_df_test['comune_stripped'] = comuni_df_test['comune_str'].str.strip()
        print("OK str.strip() successful")
        
        # Test filter
        mask = comuni_df_test['comune_stripped'] != ''
        print(f"Filtering mask type: {type(mask)}")
        print(f"Filtering mask dtype: {mask.dtype}")
        comuni_df_filtered = comuni_df_test[mask]
        print(f"After string filter: {len(comuni_df_filtered)} rows")
        print("OK String filtering successful")
        
    except Exception as e:
        print(f"ERROR String operations failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return
        
    # Test 5: Search
    try:
        print("Testing search logic...")
        count = 0
        for _, row in comuni_df_filtered.iterrows():
            comune_name = str(row['comune']).strip().upper()
            if query_upper in comune_name:
                print(f"Found match: {comune_name}")
                count += 1
                if count >= 5:  # Limit output
                    break
        print(f"OK Search successful, found {count} matches")
        
    except Exception as e:
        print(f"ERROR Search failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return

if __name__ == "__main__":
    debug_autocomplete()