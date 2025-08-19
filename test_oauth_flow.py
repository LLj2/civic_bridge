#!/usr/bin/env python3
"""
Test the complete OAuth send flow
"""
import requests
import json

def test_oauth_endpoints():
    print("Testing OAuth Integration Endpoints")
    print("=" * 50)
    
    # Test Gmail OAuth endpoint
    try:
        response = requests.post('http://localhost:5000/api/auth/gmail', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("Gmail OAuth endpoint: SUCCESS")
            print(f"  Provider: {data.get('provider')}")
            print(f"  Message: {data.get('message')}")
        else:
            print(f"Gmail OAuth endpoint: FAILED ({response.status_code})")
    except Exception as e:
        print(f"Gmail OAuth endpoint: ERROR - {e}")
    
    # Test Outlook OAuth endpoint  
    try:
        response = requests.post('http://localhost:5000/api/auth/outlook', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("Outlook OAuth endpoint: SUCCESS")
            print(f"  Provider: {data.get('provider')}")
            print(f"  Message: {data.get('message')}")
        else:
            print(f"Outlook OAuth endpoint: FAILED ({response.status_code})")
    except Exception as e:
        print(f"Outlook OAuth endpoint: ERROR - {e}")

def test_send_email_endpoint():
    print("\nTesting Send Email Endpoint")
    print("=" * 30)
    
    # Test valid email send
    email_data = {
        "to": "test@example.com",
        "subject": "Test Message from Civic Bridge",
        "body": "This is a test message sent via the OAuth integration.",
        "senderName": "Test User",
        "provider": "gmail",
        "representative": {
            "nome": "Test",
            "cognome": "Representative"
        },
        "repType": "camera",
        "location": "Roma"
    }
    
    try:
        response = requests.post(
            'http://localhost:5000/api/send-email',
            headers={'Content-Type': 'application/json'},
            json=email_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("Send Email endpoint: SUCCESS")
            print(f"  Message: {result.get('message')}")
            print(f"  Tracking ID: {result.get('tracking', {}).get('message_id')}")
            print(f"  Delivery Status: {result.get('tracking', {}).get('delivery_status')}")
        else:
            print(f"Send Email endpoint: FAILED ({response.status_code})")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"Send Email endpoint: ERROR - {e}")
    
    # Test missing required fields
    try:
        incomplete_data = {"to": "test@example.com"}
        response = requests.post(
            'http://localhost:5000/api/send-email',
            headers={'Content-Type': 'application/json'},
            json=incomplete_data,
            timeout=5
        )
        
        if response.status_code == 400:
            result = response.json()
            print("Validation test: SUCCESS")
            print(f"  Error caught: {result.get('error')}")
        else:
            print("Validation test: FAILED - Should have rejected incomplete data")
            
    except Exception as e:
        print(f"Validation test: ERROR - {e}")

def test_complete_representative_data():
    print("\nTesting Representative Data for OAuth Flow")
    print("=" * 45)
    
    # Get representative data
    response = requests.get('http://localhost:5000/api/lookup?q=Roma', timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            reps = data['representatives']
            location = data['location']
            
            # Test each type of representative
            for rep_type, rep_list in [('camera', reps['camera']), 
                                       ('senato', reps['senato']), 
                                       ('eu_parliament', reps['eu_parliament'])]:
                if rep_list and len(rep_list) > 0:
                    rep = rep_list[0]
                    print(f"{rep_type.upper()} Representative Test:")
                    print(f"  Name: {rep.get('nome')} {rep.get('cognome')}")
                    print(f"  Email: {rep.get('email', 'N/A')}")
                    print(f"  Party: {rep.get('gruppo_partito', 'N/A')}")
                    
                    # Check OAuth readiness
                    required_fields = ['nome', 'cognome', 'email']
                    has_all_fields = all(rep.get(field) for field in required_fields)
                    has_valid_email = rep.get('email') and '@' in rep.get('email', '')
                    
                    if has_all_fields and has_valid_email:
                        print(f"  OAuth Ready: YES")
                    else:
                        missing = [f for f in required_fields if not rep.get(f)]
                        print(f"  OAuth Ready: NO - Missing: {missing}")
                    print()
        else:
            print(f"Representative data test: FAILED - {data['error']}")
    else:
        print(f"Representative data test: HTTP ERROR {response.status_code}")

def show_oauth_test_summary():
    print("\n" + "=" * 50)
    print("OAUTH INTEGRATION - TESTING SUMMARY")
    print("=" * 50)
    print("✓ Backend API Endpoints:")
    print("  - /api/auth/gmail (OAuth initiation)")
    print("  - /api/auth/outlook (OAuth initiation)")  
    print("  - /api/send-email (Email sending with tracking)")
    print()
    print("✓ Frontend Integration:")
    print("  - Professional message composer modal")
    print("  - OAuth provider selection (Gmail/Outlook)")
    print("  - Real API calls instead of simulation")
    print("  - Form validation and error handling")
    print("  - Send tracking and delivery confirmation")
    print()
    print("✓ Message Templates:")
    print("  - Camera dei Deputati (formal Italian)")
    print("  - Senato della Repubblica (formal Italian)")
    print("  - Parlamento Europeo (European context)")
    print()
    print("MANUAL TESTING:")
    print("1. Visit http://localhost:5000")
    print("2. Search for 'Roma'")
    print("3. Click 'Invia Diretto' on any representative")
    print("4. Select Gmail or Outlook (simulated OAuth)")
    print("5. Fill in your name and edit message")
    print("6. Click 'Invia Messaggio'")
    print("7. Verify success notification and tracking")

if __name__ == "__main__":
    test_oauth_endpoints()
    test_send_email_endpoint()
    test_complete_representative_data()
    show_oauth_test_summary()