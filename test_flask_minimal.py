#!/usr/bin/env python3
"""
Minimal Flask test to isolate the pandas/Flask interaction issue
"""
import json
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from civic_lookup import CivicLookup, clean_for_json

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy data types"""
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

# Global lookup system
lookup_system = None

def init_lookup():
    global lookup_system
    if lookup_system is None:
        lookup_system = CivicLookup()
        lookup_system.load_data()
    return lookup_system

@app.route('/test-autocomplete')
def test_autocomplete():
    """Minimal autocomplete test endpoint"""
    query = request.args.get('q', 'roma')
    
    try:
        print(f"Starting test autocomplete for: {query}")
        
        lookup = init_lookup()
        if lookup._comuni_cache is None:
            return jsonify({'error': 'Data not loaded'})
        
        print(f"Data loaded: {len(lookup._comuni_cache)} comuni")
        
        query_upper = query.upper()
        
        # Use the same logic that worked in direct test
        comuni_df = lookup._comuni_cache.copy()
        print(f"DataFrame copied: {comuni_df.shape}")
        
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
                print(f"Warning: Error processing row {idx}: {e}")
                continue
        
        print(f"Converted {len(comuni_data)} comuni to clean format")
        
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
        
        print(f"Found {len(results)} matches")
        
        # Sort and limit
        results.sort(key=lambda x: x['score'])
        results = results[:10]
        
        # Remove score
        for result in results:
            del result['score']
            
        print(f"Returning {len(results)} results")
        
        return jsonify({
            'success': True,
            'query': query,
            'count': len(results),
            'results': results
        })
        
    except Exception as e:
        print(f"Error in test autocomplete: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting minimal Flask test server...")
    app.run(debug=True, host='127.0.0.1', port=5001)