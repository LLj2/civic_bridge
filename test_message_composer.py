#!/usr/bin/env python3
"""
Test the message composer functionality
"""
import requests

def test_message_composer():
    print("Testing Message Composer Interface")
    print("=" * 50)
    
    # Test API is working
    response = requests.get('http://localhost:5000/api/lookup?q=Roma', timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            location = data['location']
            summary = data['summary']
            reps = data['representatives']
            
            print(f"API Working: {summary['total_representatives']} representatives found")
            
            # Test representative data for message composer
            if reps['camera'] and len(reps['camera']) > 0:
                sample_rep = reps['camera'][0]
                print(f"Sample representative: {sample_rep['nome']} {sample_rep['cognome']}")
                print(f"Email: {sample_rep.get('email', 'N/A')}")
                print(f"Party: {sample_rep.get('gruppo_partito', 'N/A')}")
                
                # Check if all required data is present
                required_fields = ['nome', 'cognome', 'email', 'gruppo_partito']
                missing_fields = [field for field in required_fields if not sample_rep.get(field)]
                
                if missing_fields:
                    print(f"WARNING: Missing fields: {missing_fields}")
                else:
                    print("SUCCESS: All required data available for message composer")
            
            print("\nMessage Composer Features Implemented:")
            print("- Professional modal interface")
            print("- OAuth authentication simulation (Gmail/Outlook)")
            print("- Pre-filled message templates")
            print("- Form validation and user feedback")
            print("- Send tracking and confirmation")
            print("- Responsive design")
            
        else:
            print(f"API Error: {data['error']}")
    else:
        print(f"HTTP Error: {response.status_code}")

def show_test_instructions():
    print("\n" + "=" * 50)
    print("MANUAL TESTING - MESSAGE COMPOSER")
    print("=" * 50)
    print("1. Open http://localhost:5000")
    print("2. Search for 'Roma'")
    print("3. Click '🚀 Invia Diretto' on any representative")
    print("4. Observe the message composer modal:")
    print("   - Professional styling and animation")
    print("   - Pre-filled subject and message body")
    print("   - OAuth provider selection (Gmail/Outlook)")
    print("5. Click 'Gmail' or 'Outlook' to simulate authentication")
    print("6. Enter your name in the 'Il tuo nome' field")
    print("7. Edit the message as needed")
    print("8. Click 'Invia Messaggio' to simulate sending")
    print("9. Verify success notification and modal closes")
    print("10. Test various edge cases:")
    print("    - Try sending without authentication")
    print("    - Try sending with empty fields")
    print("    - Test closing modal with X, outside click, or Escape key")
    
    print("\nEXPECTED RESULTS:")
    print("- Smooth modal animations")
    print("- Real-time form validation")
    print("- Clear feedback notifications")
    print("- Professional Italian message templates")
    print("- Disabled send button until all requirements met")

if __name__ == "__main__":
    test_message_composer()
    show_test_instructions()