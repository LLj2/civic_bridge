#!/usr/bin/env python3
"""
Debug the init_lookup function specifically
"""
import sys
import traceback
from api_server import init_lookup

def test_init_lookup():
    """Test the init_lookup function directly"""
    print("Testing init_lookup function...")
    
    try:
        print("Calling init_lookup()...")
        lookup = init_lookup()
        print(f"SUCCESS: Lookup system initialized")
        
        print(f"Comuni cache: {lookup._comuni_cache is not None}")
        if lookup._comuni_cache is not None:
            print(f"Comuni cache length: {len(lookup._comuni_cache)}")
            print(f"Comuni cache type: {type(lookup._comuni_cache)}")
            print(f"Comuni cache dtypes: {lookup._comuni_cache.dtypes}")
            
            # Test copy operation
            try:
                print("Testing DataFrame copy...")
                copied_df = lookup._comuni_cache.copy()
                print(f"SUCCESS: DataFrame copy worked, shape: {copied_df.shape}")
            except Exception as e:
                print(f"ERROR: DataFrame copy failed: {e}")
                traceback.print_exc()
        
        print("All tests passed!")
        
    except Exception as e:
        print(f"ERROR: init_lookup failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_init_lookup()