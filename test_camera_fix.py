#!/usr/bin/env python3
"""
Test Camera representatives fix
"""
import requests

def test_camera_fix():
    # Test Roma lookup with restarted server
    response = requests.get('http://localhost:5000/api/lookup?q=Roma', timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            summary = data['summary']
            print(f"Roma: {summary['total_representatives']} total")
            print(f"  Camera: {summary['deputati_count']}")
            print(f"  Senato: {summary['senatori_count']}")
            print(f"  EU: {summary['mep_count']}")
            
            # Show Camera representatives if any
            if data['representatives']['camera']:
                print('Camera representatives:')
                for dep in data['representatives']['camera'][:5]:
                    print(f"  - {dep['nome']} {dep['cognome']} ({dep['gruppo_partito']}) - {dep['email']}")
            else:
                print("No Camera representatives found")
        else:
            print(f"Error: {data['error']}")
    else:
        print(f"HTTP Error: {response.status_code}")

if __name__ == "__main__":
    test_camera_fix()