#!/usr/bin/env python3
import requests

print('Testing OAuth Endpoints:')
print('=' * 30)

# Test Gmail OAuth
try:
    response = requests.post('http://localhost:5000/api/auth/gmail', timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"Gmail OAuth: SUCCESS - {data['message']}")
    else:
        print(f"Gmail OAuth: FAILED - {response.status_code}")
except Exception as e:
    print(f'Gmail OAuth: ERROR - {e}')

# Test Outlook OAuth  
try:
    response = requests.post('http://localhost:5000/api/auth/outlook', timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"Outlook OAuth: SUCCESS - {data['message']}")
    else:
        print(f"Outlook OAuth: FAILED - {response.status_code}")
except Exception as e:
    print(f'Outlook OAuth: ERROR - {e}')

# Test Send Email
try:
    email_data = {
        'to': 'test@example.com',
        'subject': 'Test Subject', 
        'body': 'Test Body',
        'senderName': 'Test User',
        'provider': 'gmail'
    }
    response = requests.post('http://localhost:5000/api/send-email', json=email_data, timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"Send Email: SUCCESS - {data['message']}")
        print(f"  Tracking ID: {data['tracking']['message_id']}")
    else:
        print(f"Send Email: FAILED - {response.status_code}")
except Exception as e:
    print(f'Send Email: ERROR - {e}')

print('\nOAuth Integration: READY FOR TESTING!')
print('Visit http://localhost:5000 to test the complete flow')