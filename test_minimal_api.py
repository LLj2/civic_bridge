#!/usr/bin/env python3
"""
Test the minimal Flask server
"""
import requests

def test_minimal():
    try:
        print("Testing minimal Flask server...")
        url = "http://127.0.0.1:5001/test-autocomplete?q=roma"
        response = requests.get(url, timeout=10)
        
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: Found {data['count']} results")
            for result in data['results'][:3]:
                print(f"  - {result['display']}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    test_minimal()