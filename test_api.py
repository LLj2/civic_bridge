#!/usr/bin/env python3
"""
Test script for the running API server
"""

import requests
import json

def test_autocomplete():
    try:
        print("Testing autocomplete API...")
        url = "http://localhost:5000/api/autocomplete?q=roma"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Autocomplete working: {data['count']} results")
            for result in data['results'][:3]:
                print(f"  - {result['display']}")
        else:
            print(f"Autocomplete failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Connection error: {e}")

def test_lookup():
    try:
        print("\nTesting lookup API...")
        url = "http://localhost:5000/api/lookup?q=Roma"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"Lookup working: {data['summary']['total_representatives']} representatives")
                print(f"  Location: {data['location']['comune']} ({data['location']['provincia']}) - {data['location']['regione']}")
            else:
                print(f"Lookup failed: {data['error']}")
        else:
            print(f"Lookup HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"Connection error: {e}")

def test_health():
    try:
        print("\nTesting health API...")
        url = "http://localhost:5000/api/health"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Health check: {data['status']}")
        else:
            print(f"Health check failed: {response.status_code}")
            
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    print("Testing Civic Bridge API")
    print("=" * 30)
    
    test_health()
    test_autocomplete() 
    test_lookup()
    
    print("\nWeb interface: http://localhost:5000")
    print("Test autocomplete by typing 'roma' in the search box")