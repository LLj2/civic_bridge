#!/usr/bin/env python3
"""
Test multiple Italian cities to ensure the system works robustly
"""
import requests

def test_location(location):
    print(f'Testing {location}:')
    
    # Test autocomplete
    try:
        auto_resp = requests.get(f'http://localhost:5000/api/autocomplete?q={location}', timeout=5)
        if auto_resp.status_code == 200:
            auto_data = auto_resp.json()
            first_result = auto_data['results'][0]['display'] if auto_data['results'] else 'none'
            print(f'  Autocomplete: {auto_data["count"]} results, first: {first_result}')
        else:
            print(f'  Autocomplete failed: {auto_resp.status_code}')
    except Exception as e:
        print(f'  Autocomplete error: {e}')
    
    # Test lookup
    try:
        lookup_resp = requests.get(f'http://localhost:5000/api/lookup?q={location}', timeout=10)
        if lookup_resp.status_code == 200:
            lookup_data = lookup_resp.json()
            if lookup_data['success']:
                location_info = lookup_data['location']
                summary = lookup_data['summary']
                print(f'  Lookup: {summary["total_representatives"]} representatives for {location_info["comune"]} ({location_info["provincia"]}) - {location_info["regione"]}')
                print(f'    Camera: {summary["deputati_count"]}, Senato: {summary["senatori_count"]}, EU: {summary["mep_count"]}')
            else:
                print(f'  Lookup failed: {lookup_data["error"]}')
        else:
            print(f'  Lookup HTTP error: {lookup_resp.status_code}')
    except Exception as e:
        print(f'  Lookup error: {e}')
    
    print()

if __name__ == "__main__":
    print("Testing multiple Italian cities")
    print("=" * 40)
    
    test_locations = ['Roma', 'Milano', 'Napoli', 'Genova', 'Torino', 'Bologna']
    
    for location in test_locations:
        test_location(location)
    
    print("All tests completed!")