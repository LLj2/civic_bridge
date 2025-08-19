#!/usr/bin/env python3
"""
Debug Flask context vs direct call
"""
import json
import numpy as np
import pandas as pd
from flask import Flask, jsonify
from civic_lookup import CivicLookup, clean_for_json

# Same JSON encoder
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

app = Flask(__name__)
app.json_encoder = NumpyEncoder

# Global lookup
lookup_system = None

def init_lookup():
    global lookup_system
    if lookup_system is None:
        lookup_system = CivicLookup()
        lookup_system.load_data()
    return lookup_system

def autocomplete_logic(query):
    """The exact same logic, extracted into a function"""
    lookup = init_lookup()
    if lookup._comuni_cache is None:
        raise Exception("Data not loaded")
    
    query_upper = query.upper()
    
    # Copy the DataFrame
    comuni_df = lookup._comuni_cache.copy()
    
    results = []
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
            continue
    
    # Search
    for comune_data in comuni_data:
        comune_name = comune_data['comune'].upper()
        
        if query_upper == comune_name:
            score = 1  # Exact match
        elif comune_name.startswith(query_upper):
            score = 2  # Starts with  
        elif query_upper in comune_name:
            score = 3  # Contains
        else:
            continue
        
        result_item = {
            'score': score,
            'comune': comune_data['comune'],
            'provincia': comune_data['provincia'],
            'regione': comune_data['regione'],
            'display': f"{comune_data['comune']} ({comune_data['provincia']}) - {comune_data['regione']}"
        }
        results.append(result_item)
    
    # Sort and limit
    results.sort(key=lambda x: x['score'])
    results = results[:10]
    
    # Remove score
    for result in results:
        del result['score']
    
    return results

@app.route('/test-within-flask')
def test_within_flask():
    """Test the same logic within Flask"""
    try:
        print("Testing autocomplete within Flask context...")
        results = autocomplete_logic("roma")
        print(f"SUCCESS within Flask: Found {len(results)} results")
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        print(f"ERROR within Flask: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def test_outside_flask():
    """Test the same logic outside Flask"""
    try:
        print("Testing autocomplete outside Flask context...")
        results = autocomplete_logic("roma")
        print(f"SUCCESS outside Flask: Found {len(results)} results")
        return results
    except Exception as e:
        print(f"ERROR outside Flask: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    print("=== Testing OUTSIDE Flask ===")
    results_outside = test_outside_flask()
    
    print("\n=== Starting Flask server ===")
    print("Visit http://127.0.0.1:5002/test-within-flask to test within Flask")
    app.run(debug=False, host='127.0.0.1', port=5002)