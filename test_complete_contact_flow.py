#!/usr/bin/env python3
"""
Test the complete contact flow with enhanced UI
"""
import requests
import urllib.parse

def test_contact_functionality():
    print("Testing Enhanced Contact Interface")
    print("=" * 50)
    
    # Test API functionality
    response = requests.get('http://localhost:5000/api/lookup?q=Roma', timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            location = data['location']
            summary = data['summary']
            reps = data['representatives']
            
            print(f"Location: {location['comune']} ({location['provincia']}) - {location['regione']}")
            print(f"Total Representatives: {summary['total_representatives']}")
            print(f"  Camera: {summary['deputati_count']}")
            print(f"  Senato: {summary['senatori_count']}")
            print(f"  EU: {summary['mep_count']}")
            print()
            
            # Test sample contact data
            test_representative_contacts(reps, location)
            
        else:
            print(f"ERROR: {data['error']}")
    else:
        print(f"ERROR: HTTP {response.status_code}")

def test_representative_contacts(reps, location):
    """Test contact information for different types of representatives"""
    
    # Test Camera representative
    if reps['camera'] and len(reps['camera']) > 0:
        camera_rep = reps['camera'][0]
        print("CAMERA REPRESENTATIVE TEST:")
        print(f"  Name: {camera_rep['nome']} {camera_rep['cognome']}")
        print(f"  Party: {camera_rep['gruppo_partito']}")
        print(f"  Email: {camera_rep.get('email', 'N/A')}")
        
        if camera_rep.get('email') and camera_rep['email'] != 'Non disponibile':
            test_mailto_generation(camera_rep, 'camera', location['comune'])
        print()
    
    # Test Senato representative
    if reps['senato'] and len(reps['senato']) > 0:
        senato_rep = reps['senato'][0]
        print("SENATO REPRESENTATIVE TEST:")
        print(f"  Name: {senato_rep['nome']} {senato_rep['cognome']}")
        print(f"  Party: {senato_rep['gruppo_partito']}")
        print(f"  Email: {senato_rep.get('email', 'N/A')}")
        
        if senato_rep.get('email') and senato_rep['email'] != 'Non disponibile':
            test_mailto_generation(senato_rep, 'senato', location['comune'])
        print()
    
    # Test EU representative
    if reps['eu_parliament'] and len(reps['eu_parliament']) > 0:
        eu_rep = reps['eu_parliament'][0]
        print("EU PARLIAMENT REPRESENTATIVE TEST:")
        print(f"  Name: {eu_rep['nome']} {eu_rep['cognome']}")
        print(f"  Party: {eu_rep['gruppo_partito']}")
        print(f"  Email: {eu_rep.get('email', 'N/A')}")
        
        if eu_rep.get('email') and eu_rep['email'] != 'Non disponibile':
            test_mailto_generation(eu_rep, 'eu', location['comune'])
        print()

def test_mailto_generation(rep, rep_type, location):
    """Test mailto URL generation with templates"""
    
    # Simulate the JavaScript mailto generation logic
    templates = {
        'camera': {
            'subject': f"Cittadino di {location} - Richiesta informazioni",
            'title': 'Onorevole Deputato/a'
        },
        'senato': {
            'subject': f"Cittadino di {location} - Richiesta informazioni", 
            'title': 'Onorevole Senatore/Senatrice'
        },
        'eu': {
            'subject': f"Cittadino italiano - Richiesta informazioni EU",
            'title': 'Onorevole Deputato/a Europeo/a'
        }
    }
    
    template = templates.get(rep_type, {'subject': 'Richiesta informazioni', 'title': 'Gentile Rappresentante'})
    
    subject = template['subject']
    body = f"""Gentile {template['title']} {rep['nome']} {rep['cognome']},

sono [Il tuo nome], cittadino/a di {location}.

Vi scrivo per [descrivere brevemente la questione o richiesta].

[Aggiungere qui il contenuto del messaggio]

Ringrazio per l'attenzione e resto in attesa di un riscontro.

Cordiali saluti,
[Il tuo nome]

---
Messaggio inviato tramite Civic Bridge (https://civic-bridge.it)"""
    
    # Create mailto URL
    mailto_url = f"mailto:{rep['email']}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
    
    print(f"  Mailto URL generated: {len(mailto_url)} characters")
    print(f"  Subject: {subject}")
    print(f"  Body preview: {body[:100]}...")
    print(f"  SUCCESS: Contact template ready for {rep_type.upper()} representative")

def show_manual_test_instructions():
    print("\n" + "=" * 50)
    print("MANUAL TESTING INSTRUCTIONS")
    print("=" * 50)
    print("1. Open http://localhost:5000 in your browser")
    print("2. Search for 'Roma' in the search box")
    print("3. Observe the enhanced representative cards with:")
    print("   - Professional styling and layout")
    print("   - Contact buttons for each representative")
    print("   - Email addresses displayed clearly")
    print("4. Click '📧 Apri Email Client' on any representative")
    print("5. Verify your email client opens with:")
    print("   - Pre-filled recipient email")
    print("   - Appropriate subject line")
    print("   - Professional message template")
    print("6. Click '🚀 Invia Diretto (presto)' to see placeholder message")
    print("7. Test on mobile device for responsive design")
    print("\nEXPECTED RESULTS:")
    print("- Professional, trustworthy interface")
    print("- Smooth user experience") 
    print("- Working mailto functionality")
    print("- Clear feedback notifications")

if __name__ == "__main__":
    test_contact_functionality()
    show_manual_test_instructions()