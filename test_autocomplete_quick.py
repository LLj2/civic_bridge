#!/usr/bin/env python3
import requests
try:
    response = requests.get('http://localhost:5000/api/autocomplete?q=roma', timeout=5)
    print(f'Autocomplete status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f"Results: {data['count']} found")
        if data['results']:
            print(f"First result: {data['results'][0]['display']}")
    else:
        print(f'Error response: {response.text}')
except Exception as e:
    print(f'Connection error: {e}')