#!/usr/bin/env python3
"""
Test the enhanced contact interface functionality
"""
import requests

def test_enhanced_interface():
    # Test the lookup to see the enhanced interface structure
    response = requests.get('http://localhost:5000/api/lookup?q=Roma', timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            print('API working - Enhanced interface ready for testing')
            location = data['location']
            summary = data['summary']
            print(f"  Location: {location['comune']} ({location['provincia']})")
            print(f"  Representatives: {summary['total_representatives']} total")
            
            # Check if contact information is available
            camera_reps = data['representatives']['camera']
            if camera_reps and len(camera_reps) > 0:
                first_rep = camera_reps[0]
                print(f"  Sample rep: {first_rep['nome']} {first_rep['cognome']}")
                print(f"  Email available: {first_rep.get('email', 'N/A') != 'Non disponibile'}")
            
            print(f"\n🌐 Visit http://localhost:5000 to test the enhanced contact interface!")
            print('   1. Search for "Roma"')
            print('   2. Click "📧 Apri Email Client" on any representative')
            print('   3. Verify mailto opens with pre-filled message')
        else:
            print(f"ERROR API Error: {data['error']}")
    else:
        print(f"ERROR HTTP Error: {response.status_code}")

if __name__ == "__main__":
    test_enhanced_interface()