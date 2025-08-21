#!/usr/bin/env python3
"""
Civic Bridge API Server
Fast JSON API for representative lookups
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import numpy as np
import pandas as pd
import logging
import traceback
import os
from civic_lookup import CivicLookup, clean_for_json

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy data types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

app = Flask(__name__)
app.json_encoder = NumpyEncoder
CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize lookup system
lookup_system = None

def init_lookup():
    global lookup_system
    if lookup_system is None:
        lookup_system = CivicLookup()
        lookup_system.load_data()
    return lookup_system

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'civic-bridge-api',
        'version': '1.0.0'
    })

@app.route('/static/themes.json')
def serve_themes():
    """Serve themes configuration"""
    try:
        themes_path = os.path.join('data', 'themes.json')
        with open(themes_path, 'r', encoding='utf-8') as f:
            themes_data = json.load(f)
        return jsonify(themes_data)
    except Exception as e:
        print(f"Error serving themes: {e}")
        # Return minimal fallback
        return jsonify({
            "themes": [
                {
                    "id": "generico",
                    "title": "Messaggio generico", 
                    "description": "Template base per comunicazioni generali",
                    "templates": {
                        "camera": {
                            "subject": "Cittadino di {{location}} - Richiesta",
                            "body": "Onorevole Deputato {{rep_name}},\n\n[RIGA PERSONALE OBBLIGATORIA]\n\nCordiali saluti"
                        },
                        "senato": {
                            "subject": "Cittadino di {{location}} - Richiesta", 
                            "body": "Onorevole Senatore {{rep_name}},\n\n[RIGA PERSONALE OBBLIGATORIA]\n\nDistinti saluti"
                        },
                        "eu": {
                            "subject": "Cittadino italiano - Richiesta",
                            "body": "Onorevole Europarlamentare {{rep_name}},\n\n[RIGA PERSONALE OBBLIGATORIA]\n\nCordiali saluti"
                        }
                    }
                }
            ]
        })

@app.route('/api/auth/gmail', methods=['POST'])
def auth_gmail():
    """Initiate Gmail OAuth flow"""
    try:
        # In production, this would:
        # 1. Generate OAuth URL with proper scopes
        # 2. Return redirect URL for frontend
        # 3. Handle callback with authorization code
        # 4. Exchange for access/refresh tokens
        
        # For now, simulate the OAuth flow
        oauth_url = "https://accounts.google.com/oauth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT&scope=https://www.googleapis.com/auth/gmail.send&response_type=code"
        
        return jsonify({
            'success': True,
            'auth_url': oauth_url,
            'provider': 'gmail',
            'message': 'OAuth flow initiated'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/auth/outlook', methods=['POST'])  
def auth_outlook():
    """Initiate Outlook OAuth flow"""
    try:
        # In production, this would use Microsoft Graph API
        oauth_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=YOUR_REDIRECT&scope=https://graph.microsoft.com/mail.send"
        
        return jsonify({
            'success': True,
            'auth_url': oauth_url,
            'provider': 'outlook',
            'message': 'OAuth flow initiated'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/send-email', methods=['POST'])
def send_email():
    """Send email via authenticated provider"""
    try:
        data = request.get_json()
        
        required_fields = ['to', 'subject', 'body', 'senderName', 'provider']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # In production, this would:
        # 1. Validate OAuth token
        # 2. Use Gmail API or Microsoft Graph to send email
        # 3. Return delivery confirmation
        
        # For now, simulate successful email send
        email_data = {
            'to': data['to'],
            'subject': data['subject'],
            'body': data['body'],
            'sender': data['senderName'],
            'provider': data['provider'],
            'timestamp': '2025-08-19T07:45:00Z',
            'message_id': f"civic-bridge-{hash(data['to'] + data['subject'])}"
        }
        
        logger.info(f"Email sent via {data['provider']}: {data['to']}")
        
        return jsonify({
            'success': True,
            'message': 'Email sent successfully',
            'email_data': email_data,
            'tracking': {
                'sent': True,
                'delivery_status': 'pending',
                'message_id': email_data['message_id']
            }
        })
        
    except Exception as e:
        logger.error(f"Send email error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/lookup')
def lookup_representatives():
    """
    Main lookup endpoint
    GET /api/lookup?q=Milano
    GET /api/lookup?comune=Milano
    GET /api/lookup?cap=20100
    """
    # Get query parameter
    query = request.args.get('q') or request.args.get('comune') or request.args.get('cap')
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Missing query parameter. Use ?q=comune or ?comune=nome or ?cap=xxxxx',
            'examples': [
                '/api/lookup?q=Milano',
                '/api/lookup?comune=Roma',
                '/api/lookup?cap=00100'
            ]
        }), 400
    
    try:
        logger.info(f"Lookup request: q='{query}'")
        
        lookup = init_lookup()
        result = lookup.lookup_representatives(query.strip())
        
        if result.get('success'):
            logger.info(f"Lookup successful: {result['summary']['total_representatives']} representatives found for {result['location']['comune']}")
        else:
            logger.warning(f"Lookup failed: {result.get('error', 'Unknown error')}")
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Lookup error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/autocomplete')
def autocomplete_comuni():
    """
    Autocomplete endpoint for comuni
    GET /api/autocomplete?q=rom&limit=10
    """
    query = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 1000))  # Return all matches by default
    
    if not query or len(query) < 2:
        return jsonify({
            'success': False,
            'error': 'Query must be at least 2 characters',
            'results': []
        })
    
    try:
        lookup = init_lookup()
        if lookup._comuni_cache is None:
            return jsonify({'success': False, 'error': 'Data not loaded'})
        
        query_upper = query.upper()
        
        # Use the same logic that worked in minimal test
        comuni_df = lookup._comuni_cache.copy()
        
        results = []
        comuni_data = []
        
        for idx, row in comuni_df.iterrows():
            try:
                comune_val = row.get('comune')
                if pd.isna(comune_val) or comune_val is None:
                    continue
                comune_str = str(comune_val).strip()
                if not comune_str:
                    continue
                
                comuni_data.append({
                    'comune': comune_str,
                    'provincia': clean_for_json(row.get('provincia', '')),
                    'regione': clean_for_json(row.get('regione', ''))
                })
            except Exception as e:
                continue
        
        # Search
        for comune_data in comuni_data:
            comune_name = comune_data['comune'].upper()
            
            if query_upper == comune_name:
                score = 1  # Exact match
            elif comune_name.startswith(query_upper):
                score = 2  # Starts with  
            elif query_upper in comune_name:
                score = 3  # Contains
            else:
                continue
            
            result_item = {
                'score': score,
                'comune': comune_data['comune'],
                'provincia': comune_data['provincia'],
                'regione': comune_data['regione'],
                'display': f"{comune_data['comune']} ({comune_data['provincia']}) - {comune_data['regione']}"
            }
            results.append(result_item)
        
        # Sort and limit
        results.sort(key=lambda x: x['score'])
        results = results[:limit]
        
        # Remove score
        for result in results:
            del result['score']
            
        return jsonify({
            'success': True,
            'query': query,
            'count': len(results),
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Autocomplete error: {str(e)}'
        }), 500

@app.route('/api/representatives/<level>')
def get_representatives_by_level(level):
    """
    Get representatives by institutional level
    GET /api/representatives/camera
    GET /api/representatives/senato  
    GET /api/representatives/eu
    """
    valid_levels = ['camera', 'senato', 'eu']
    if level not in valid_levels:
        return jsonify({
            'success': False,
            'error': f'Invalid level. Must be one of: {valid_levels}'
        }), 400
    
    try:
        lookup = init_lookup()
        
        representatives = []
        if level == 'camera' and lookup._deputati_cache is not None:
            for _, dep in lookup._deputati_cache.iterrows():
                representatives.append({
                    'nome': dep.get('nome', ''),
                    'cognome': dep.get('cognome', ''),
                    'gruppo_partito': dep.get('gruppo_partito', ''),
                    'collegio': dep.get('collegio', ''),
                    'email': dep.get('email_istituzionale', ''),
                    'istituzione': 'Camera dei Deputati'
                })
        
        elif level == 'senato' and lookup._senatori_cache is not None:
            for _, sen in lookup._senatori_cache.iterrows():
                representatives.append({
                    'nome': sen.get('nome', ''),
                    'cognome': sen.get('cognome', ''),
                    'gruppo_partito': sen.get('gruppo_partito', ''),
                    'regione': sen.get('regione', ''),
                    'email': sen.get('email_istituzionale', ''),
                    'istituzione': 'Senato della Repubblica'
                })
        
        elif level == 'eu' and lookup._mep_cache is not None:
            for _, mep in lookup._mep_cache.iterrows():
                representatives.append({
                    'nome': mep.get('nome', ''),
                    'cognome': mep.get('cognome', ''),
                    'gruppo_partito': mep.get('gruppo_partito', ''),
                    'circoscrizione_eu': mep.get('circoscrizione_eu', ''),
                    'email': mep.get('email_istituzionale', ''),
                    'istituzione': 'Parlamento Europeo'
                })
        
        return jsonify({
            'success': True,
            'level': level,
            'count': len(representatives),
            'representatives': representatives
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/test-autocomplete')
def test_autocomplete():
    """Minimal autocomplete test page"""
    with open('test_autocomplete_minimal.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/')
def home():
    """Simple web interface for testing"""
    html_template = '''
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Civic Bridge - Trova i tuoi rappresentanti</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 20px;
                background-color: #f5f5f5;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
                text-align: center;
            }
            .search-box {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 30px;
            }
            input[type="text"] {
                width: 100%;
                padding: 15px;
                font-size: 16px;
                border: 2px solid #ddd;
                border-radius: 5px;
                margin-bottom: 15px;
            }
            button {
                background: #667eea;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
                width: 100%;
            }
            button:hover { background: #5a67d8; }
            .results {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .representative {
                border: 1px solid #e2e8f0;
                padding: 20px;
                margin: 15px 0;
                border-radius: 8px;
                background: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                transition: box-shadow 0.2s ease;
            }
            .representative:hover {
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            .rep-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 12px;
                flex-wrap: wrap;
            }
            .rep-name {
                font-size: 18px;
                font-weight: 600;
                color: #1a202c;
                margin: 0;
            }
            .rep-party {
                color: #667eea;
                font-weight: 500;
                font-size: 14px;
                margin: 4px 0;
            }
            .rep-details {
                color: #4a5568;
                font-size: 14px;
                margin: 4px 0;
            }
            .contact-section {
                margin-top: 16px;
                padding-top: 16px;
                border-top: 1px solid #e2e8f0;
            }
            .contact-options {
                display: flex;
                gap: 12px;
                flex-wrap: wrap;
                margin-top: 12px;
            }
            .contact-btn {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 8px 16px;
                border-radius: 6px;
                text-decoration: none;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.2s ease;
                cursor: pointer;
                border: 1px solid;
            }
            .contact-btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            }
            .btn-email {
                background: #3182ce;
                color: white;
                border-color: #3182ce;
            }
            .btn-email:hover {
                background: #2c5aa0;
                color: white;
            }
            .btn-send-direct {
                background: #38a169;
                color: white;
                border-color: #38a169;
            }
            .btn-send-direct:hover {
                background: #2f855a;
                color: white;
            }
            .email-display {
                color: #4a5568;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                margin-top: 8px;
            }
            .institution { 
                color: #667eea; 
                font-weight: bold; 
            }
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 20px;
                border-radius: 8px;
                color: white;
                font-weight: 500;
                z-index: 2000;
                opacity: 0;
                transform: translateX(400px);
                transition: all 0.3s ease;
            }
            .notification.show {
                opacity: 1;
                transform: translateX(0);
            }
            .notification.success {
                background: #38a169;
            }
            .notification.error {
                background: #e53e3e;
            }
            .notification.info {
                background: #3182ce;
            }
            
            /* Message Composer Modal */
            .modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.6);
                z-index: 3000;
                display: none;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .modal-overlay.show {
                display: flex;
            }
            .message-composer {
                background: white;
                border-radius: 12px;
                width: 100%;
                max-width: 600px;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                animation: modalSlideIn 0.3s ease-out;
            }
            @keyframes modalSlideIn {
                from {
                    opacity: 0;
                    transform: translateY(30px) scale(0.95);
                }
                to {
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
            }
            .composer-header {
                padding: 24px 24px 20px;
                border-bottom: 1px solid #e2e8f0;
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
            }
            .composer-title {
                font-size: 20px;
                font-weight: 600;
                color: #1a202c;
                margin: 0;
            }
            .composer-recipient {
                font-size: 14px;
                color: #667eea;
                margin: 4px 0 0;
            }
            .close-btn {
                background: none;
                border: none;
                font-size: 24px;
                color: #a0aec0;
                cursor: pointer;
                padding: 0;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 6px;
                transition: all 0.2s ease;
            }
            .close-btn:hover {
                background: #f7fafc;
                color: #4a5568;
            }
            .composer-body {
                padding: 24px;
            }
            .form-group {
                margin-bottom: 20px;
            }
            .form-label {
                display: block;
                font-weight: 500;
                color: #374151;
                margin-bottom: 8px;
                font-size: 14px;
            }
            .form-input {
                width: 100%;
                padding: 12px 16px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-size: 14px;
                transition: border-color 0.2s ease;
                font-family: inherit;
            }
            .form-input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            .form-textarea {
                resize: vertical;
                min-height: 200px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.5;
            }
            .composer-actions {
                padding: 20px 24px;
                border-top: 1px solid #e2e8f0;
                display: flex;
                gap: 12px;
                justify-content: flex-end;
                flex-wrap: wrap;
            }
            .btn-secondary {
                background: #f7fafc;
                color: #4a5568;
                border: 2px solid #e2e8f0;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            .btn-secondary:hover {
                background: #edf2f7;
                border-color: #cbd5e0;
            }
            .btn-primary {
                background: #667eea;
                color: white;
                border: 2px solid #667eea;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
                display: inline-flex;
                align-items: center;
                gap: 8px;
            }
            .btn-primary:hover {
                background: #5a67d8;
                border-color: #5a67d8;
                transform: translateY(-1px);
            }
            .btn-primary:disabled {
                background: #a0aec0;
                border-color: #a0aec0;
                cursor: not-allowed;
                transform: none;
            }
            .oauth-section {
                background: #f7fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 20px;
            }
            .oauth-title {
                font-weight: 500;
                color: #374151;
                margin: 0 0 12px;
                font-size: 14px;
            }
            .oauth-options {
                display: flex;
                gap: 12px;
                flex-wrap: wrap;
            }
            .oauth-btn {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 8px 16px;
                border: 2px solid #e2e8f0;
                background: white;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
                text-decoration: none;
                color: #374151;
            }
            .oauth-btn:hover {
                border-color: #cbd5e0;
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .oauth-btn.gmail {
                border-color: #ea4335;
                color: #ea4335;
            }
            .oauth-btn.gmail:hover {
                background: #ea4335;
                color: white;
            }
            .oauth-btn.outlook {
                border-color: #0078d4;
                color: #0078d4;
            }
            .oauth-btn.outlook:hover {
                background: #0078d4;
                color: white;
            }
            .error { color: red; padding: 20px; }
            .loading { text-align: center; padding: 20px; }
            .autocomplete-container { position: relative; }
            .autocomplete-list {
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: white;
                border: 1px solid #ddd;
                border-top: none;
                border-radius: 0 0 5px 5px;
                max-height: 200px;
                overflow-y: auto;
                z-index: 1000;
                display: none;
            }
            .autocomplete-item {
                padding: 10px;
                cursor: pointer;
                border-bottom: 1px solid #eee;
            }
            .autocomplete-item:hover {
                background: #f0f0f0;
            }
            .autocomplete-item:last-child {
                border-bottom: none;
            }
            
            /* Institution Section Styles */
            .institution-section {
                margin: 25px 0;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                background: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            .institution-header {
                padding: 20px;
                background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                border-bottom: 1px solid #e2e8f0;
                border-radius: 10px 10px 0 0;
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: center;
                transition: all 0.2s ease;
            }
            .institution-header:hover {
                background: linear-gradient(135deg, #f1f5f9 0%, #cbd5e1 100%);
            }
            .institution-title {
                display: flex;
                align-items: center;
                gap: 12px;
                font-size: 20px;
                font-weight: 600;
                color: #1a202c;
                margin: 0;
            }
            .institution-count {
                background: #667eea;
                color: white;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 500;
            }
            .collapse-icon {
                font-size: 24px;
                color: #667eea;
                transition: transform 0.3s ease;
            }
            .institution-section.collapsed .collapse-icon {
                transform: rotate(-90deg);
            }
            .institution-content {
                padding: 0;
                overflow: hidden;
                transition: all 0.3s ease;
            }
            .institution-section.collapsed .institution-content {
                max-height: 0;
                padding: 0;
            }
            .institution-representatives {
                padding: 20px;
            }
            
            /* Enhanced Representative Cards - Compact Design */
            .representative {
                border: 1px solid #f1f5f9;
                padding: 12px 16px;
                margin: 3px 0;
                border-radius: 6px;
                background: white;
                transition: all 0.15s ease;
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                cursor: pointer;
            }
            .representative:hover {
                border-color: #e2e8f0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }
            .rep-photo {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                color: #64748b;
                flex-shrink: 0;
            }
            .rep-info {
                flex: 1;
                min-width: 0;
                line-height: 1.3;
            }
            .rep-name {
                font-size: 15px;
                font-weight: 600;
                color: #0f172a;
                margin: 0 0 2px 0;
            }
            .rep-details {
                font-size: 13px;
                color: #64748b;
                margin: 2px 0;
            }
            .rep-collegio {
                font-size: 12px;
                color: #94a3b8;
                margin: 2px 0 0 0;
            }
            .rep-contact-btn {
                background: #3b82f6;
                color: white;
                border: none;
                padding: 6px 14px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: 500;
                cursor: pointer;
                transition: background-color 0.2s ease;
                flex-shrink: 0;
                align-self: flex-start;
                margin-top: 2px;
            }
            .rep-contact-btn:hover {
                background: #2563eb;
            }
            .rep-contact-btn:disabled {
                background: #d1d5db;
                color: #9ca3af;
                cursor: not-allowed;
            }

            /* Message Composer Modal */
            .composer-modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                backdrop-filter: blur(2px);
                z-index: 1000;
                overflow-y: auto;
            }
            .composer-modal.show {
                display: flex;
                align-items: flex-start;
                justify-content: center;
                padding: 20px;
            }
            .composer-content {
                background: white;
                border-radius: 12px;
                width: 100%;
                max-width: 600px;
                margin-top: 40px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
                animation: slideUp 0.3s ease;
            }
            @keyframes slideUp {
                from { opacity: 0; transform: translateY(30px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .composer-header {
                padding: 24px 24px 16px 24px;
                border-bottom: 1px solid #f1f5f9;
            }
            .composer-title {
                font-size: 18px;
                font-weight: 600;
                color: #0f172a;
                margin: 0 0 4px 0;
            }
            .composer-subtitle {
                font-size: 13px;
                color: #64748b;
                margin: 0;
            }
            .composer-body {
                padding: 24px;
            }
            .composer-field {
                margin-bottom: 20px;
            }
            .composer-label {
                display: block;
                font-size: 14px;
                font-weight: 500;
                color: #374151;
                margin-bottom: 6px;
            }
            .composer-label.required::after {
                content: ' *';
                color: #dc2626;
            }
            .composer-select {
                width: 100%;
                padding: 10px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                cursor: pointer;
            }
            .composer-select:focus {
                outline: none;
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
            .composer-input {
                width: 100%;
                padding: 10px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
                font-family: inherit;
            }
            .composer-input:focus {
                outline: none;
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
            .composer-textarea {
                width: 100%;
                min-height: 120px;
                padding: 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
                font-family: inherit;
                line-height: 1.5;
                resize: vertical;
            }
            .composer-textarea:focus {
                outline: none;
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
            .composer-personal {
                background: #fefce8;
                border: 1px solid #facc15;
            }
            .composer-personal:focus {
                border-color: #eab308;
                box-shadow: 0 0 0 3px rgba(234, 179, 8, 0.1);
            }
            .char-counter {
                font-size: 12px;
                color: #6b7280;
                text-align: right;
                margin-top: 4px;
            }
            .char-counter.warning {
                color: #d97706;
            }
            .char-counter.error {
                color: #dc2626;
            }
            .send-method {
                margin: 16px 0;
            }
            .radio-group {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            .radio-option {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px 0;
            }
            .radio-option input[type="radio"] {
                margin: 0;
            }
            .radio-option label {
                font-size: 14px;
                color: #374151;
                cursor: pointer;
            }
            .composer-footer {
                padding: 16px 24px 24px 24px;
                border-top: 1px solid #f1f5f9;
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 12px;
            }
            .footer-note {
                font-size: 12px;
                color: #6b7280;
                flex: 1;
            }
            .footer-buttons {
                display: flex;
                gap: 12px;
            }
            .btn-secondary {
                background: #f8fafc;
                color: #475569;
                border: 1px solid #e2e8f0;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            .btn-secondary:hover {
                background: #e2e8f0;
            }
            .btn-primary {
                background: #3b82f6;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            .btn-primary:hover {
                background: #2563eb;
            }
            .btn-primary:disabled {
                background: #d1d5db;
                cursor: not-allowed;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🇮🇹 Civic Bridge</h1>
            <p>Trova i tuoi rappresentanti eletti per Comune</p>
        </div>
        
        <div class="search-box">
            <div class="autocomplete-container">
                <input type="text" id="searchInput" placeholder="Inizia a scrivere il nome del comune (es. Roma, Milano...)">
                <div id="autocompleteList" class="autocomplete-list"></div>
            </div>
            <button onclick="searchRepresentatives()">Cerca i miei rappresentanti</button>
        </div>
        
        <div id="results" class="results" style="display: none;">
            <div id="resultsContent"></div>
        </div>
        
        
        <script>
            var autocompleteTimeout;
            var selectedComune = '';
            
            function setupAutocomplete() {
                console.log('Setting up autocomplete...');
                var input = document.getElementById('searchInput');
                var list = document.getElementById('autocompleteList');
                
                if (!input) {
                    console.error('searchInput element not found!');
                    return;
                }
                if (!list) {
                    console.error('autocompleteList element not found!');
                    return;
                }
                
                console.log('Autocomplete elements found, adding event listeners...');
                
                input.addEventListener('input', function() {
                    var query = this.value.trim();
                    
                    clearTimeout(autocompleteTimeout);
                    
                    if (query.length < 2) {
                        hideAutocomplete();
                        return;
                    }
                    
                    autocompleteTimeout = setTimeout(function() {
                        fetchAutocomplete(query);
                    }, 300);
                });
                
                input.addEventListener('blur', function() {
                    // Hide after small delay to allow clicks
                    setTimeout(function() { hideAutocomplete(); }, 200);
                });
                
                input.addEventListener('focus', function() {
                    if (this.value.length >= 2) {
                        fetchAutocomplete(this.value.trim());
                    }
                });
            }
            
            function fetchAutocomplete(query) {
                fetch('/api/autocomplete?q=' + encodeURIComponent(query))
                    .then(function(response) { return response.json(); })
                    .then(function(data) {
                        console.log('Autocomplete response:', data);
                        if (data.success && data.results.length > 0) {
                            showAutocompleteResults(data.results);
                        } else {
                            hideAutocomplete();
                        }
                    })
                    .catch(function(error) {
                        console.error('Autocomplete error:', error);
                        hideAutocomplete();
                    });
            }
            
            function showAutocompleteResults(results) {
                console.log('Showing autocomplete results:', results);
                var list = document.getElementById('autocompleteList');
                list.innerHTML = '';
                
                for (let i = 0; i < results.length; i++) {
                    const result = results[i];
                    const item = document.createElement('div');
                    item.className = 'autocomplete-item';
                    item.textContent = result.display;
                    item.addEventListener('click', function () {
                        document.getElementById('searchInput').value = result.comune;
                        selectedComune = result.comune;
                        hideAutocomplete();
                        searchRepresentatives();
                    });
                    list.appendChild(item);
                }
                
                list.style.display = 'block';
                console.log('Autocomplete list shown with', results.length, 'items');
            }
            
            function hideAutocomplete() {
                document.getElementById('autocompleteList').style.display = 'none';
            }
            
            function getPartyColor(party) {
                var partyColors = {
                    "Partito Democratico": "#e53e3e",
                    "Lega": "#3182ce",
                    "Movimento 5 Stelle": "#f0ad4e",
                    "Forza Italia": "#3b82f6",
                    "Fratelli d'Italia": "#0f172a",
                    "Italia Viva": "#8b5cf6",
                    "Azione": "#10b981",
                    "Più Europa": "#f59e0b"
                };
                return partyColors[party] || "#6b7280";
            }
            
            function getPartyCode(party) {
                var partyCodes = {
                    "Partito Democratico": "PD",
                    "Lega": "Lega",
                    "Movimento 5 Stelle": "M5S",
                    "Forza Italia": "FI",
                    "Fratelli d'Italia": "FdI",
                    "Italia Viva": "IV",
                    "Azione": "Az",
                    "Più Europa": "+Eu",
                    "Alleanza Verdi e Sinistra": "AVS",
                    "Noi Moderati": "NM"
                };
                if (partyCodes[party]) return partyCodes[party];
                const p = (party || '').toString();
                return p ? p.substring(0, 3).toUpperCase() : '';
            }
            
            // Global variables for composer
            var currentThemes = [];
            var selectedRep = null;
            var selectedInstitution = null;
            let currentRepresentatives = null;
            let currentLocation = null;

            // Load themes from server
            function loadThemes() {
                fetch('/static/themes.json')
                    .then(function(response) { return response.json(); })
                    .then(function(data) {
                        currentThemes = data.themes;
                    })
                    .catch(function(error) {
                        console.error('Failed to load themes:', error);
                        // Fallback themes
                        currentThemes = [
                            {
                                id: 'corridoio_umanitario',
                                title: 'Corridoio umanitario',
                                templates: {
                                    camera: { subject: 'Corridoio umanitario Gaza', body: 'Template di emergenza...' }
                                }
                            }
                        ];
                    });
            }

            // Open composer modal
            function openComposer(repIndex, institution) {
                const map = { camera: 'camera', senato: 'senato', eu: 'eu_parliament' };
                const listKey = map[institution] || institution;

                selectedRep = (currentRepresentatives && currentRepresentatives[listKey])
                    ? currentRepresentatives[listKey][repIndex]
                    : null;
                selectedInstitution = institution; // keep the short form for templates/UI

                if (!selectedRep) {
                    console.error('Representative not found for', institution, repIndex);
                    showNotification('Impossibile aprire il compositore: rappresentante non trovato.', 'error');
                    return;
                }
                
                // Set header info
                var roleMap = { camera: 'Deputato', senato: 'Senatore', eu: 'MEP' };
                var role = roleMap[institution];
                var partyCode = getPartyCode(selectedRep.gruppo_partito);
                
                document.getElementById('composerTitle').textContent = 'Scrivi a ' + role + ' ' + selectedRep.nome + ' ' + selectedRep.cognome;
                
                var locationInfo = '';
                if (institution === 'camera') {
                    locationInfo = 'Collegio: ' + selectedRep.collegio;
                } else if (institution === 'senato') {
                    locationInfo = 'Regione: ' + selectedRep.regione;
                } else {
                    locationInfo = 'Circoscrizione: ' + selectedRep.circoscrizione_eu;
                }
                document.getElementById('composerSubtitle').textContent = locationInfo + ' · Partito: ' + partyCode;
                
                // Populate theme dropdown
                populateThemes();
                
                // Reset form
                resetComposerForm();
                
                // Show modal
                document.getElementById('composerModal').classList.add('show');
                
                // Focus first field
                document.getElementById('themeSelect').focus();
            }

            // Close composer modal
            function closeComposer() {
                document.getElementById('composerModal').classList.remove('show');
                resetComposerForm();
            }

            // Populate theme dropdown
            function populateThemes() {
                var select = document.getElementById('themeSelect');
                select.innerHTML = '<option value="">Seleziona un tema...</option>';
                
                for (var i = 0; i < currentThemes.length; i++) {
                    var theme = currentThemes[i];
                    var option = document.createElement('option');
                    option.value = theme.id;
                    option.textContent = theme.title;
                    select.appendChild(option);
                }
            }

            // Handle theme selection
            function onThemeChange() {
                const themeId = document.getElementById('themeSelect').value;
                if (!themeId) {
                    clearMessageFields();
                    return;
                }
                
                var theme = null;
                for (var i = 0; i < currentThemes.length; i++) {
                    if (currentThemes[i].id === themeId) {
                        theme = currentThemes[i];
                        break;
                    }
                }
                if (!theme || !theme.templates[selectedInstitution]) {
                    clearMessageFields();
                    return;
                }
                
                var template = theme.templates[selectedInstitution];
                
                // Replace tokens in subject and body
                var subject = replaceTokens(template.subject);
                var body = replaceTokens(template.body);
                
                document.getElementById('subjectInput').value = subject;
                document.getElementById('bodyTextarea').value = body;
                
                validateForm();
            }

            // Replace template tokens
            function replaceTokens(text) {
                var locationName = (currentLocation && currentLocation.comune) ? currentLocation.comune : '[Comune]';
                var repName = selectedRep ? (selectedRep.nome + ' ' + selectedRep.cognome) : '[Nome Rappresentante]';
                
                return (text || '')
                    .replace(/\{\{rep_name\}\}/g, repName)
                    .replace(/\{\{location\}\}/g, locationName)
                    .replace(/\{\{user_name\}\}/g, '[Il tuo nome]')
                    .replace(/\{\{custom_subject\}\}/g, '[Inserisci oggetto specifico]');
            }

            // Clear message fields
            function clearMessageFields() {
                document.getElementById('subjectInput').value = '';
                document.getElementById('bodyTextarea').value = '';
                validateForm();
            }

            // Reset entire form
            function resetComposerForm() {
                document.getElementById('themeSelect').value = '';
                document.getElementById('subjectInput').value = '';
                document.getElementById('bodyTextarea').value = '';
                document.getElementById('personalLine').value = '';
                document.getElementById('sendMailto').checked = true;
                updateCharCounter();
                validateForm();
            }

            // Update character counter for personal line
            function updateCharCounter() {
                var textarea = document.getElementById('personalLine');
                var counter = document.getElementById('personalCounter');
                var length = textarea.value.length;
                var maxLength = 300;
                
                counter.textContent = length + ' / ' + maxLength + ' caratteri';
                
                if (length > maxLength * 0.9) {
                    counter.className = 'char-counter warning';
                } else if (length > maxLength) {
                    counter.className = 'char-counter error';
                } else {
                    counter.className = 'char-counter';
                }
            }

            // Validate form and enable/disable send button
            function validateForm() {
                var theme = document.getElementById('themeSelect').value;
                var subject = document.getElementById('subjectInput').value.trim();
                var personalLine = document.getElementById('personalLine').value.trim();
                var sendButton = document.getElementById('sendButton');
                
                var isValid = theme && subject && personalLine.length >= 20;
                sendButton.disabled = !isValid;
                
                if (isValid) {
                    sendButton.textContent = 'Invia';
                } else {
                    sendButton.textContent = 'Compila tutti i campi';
                }
            }

            // Send message
            function sendMessage() {
                var sendMethod = document.querySelector('input[name="sendMethod"]:checked').value;
                var subject = document.getElementById('subjectInput').value;
                var body = document.getElementById('bodyTextarea').value;
                var personalLine = document.getElementById('personalLine').value;
                
                // Replace [RIGA PERSONALE OBBLIGATORIA] with actual personal content
                var finalBody = body.replace(/\[RIGA PERSONALE OBBLIGATORIA[^\]]*\]/g, personalLine);
                
                if (sendMethod === 'mailto') {
                    openMailClient(subject, finalBody);
                } else {
                    sendViaOAuth(subject, finalBody);
                }
            }

            // Open mail client
            function openMailClient(subject, body) {
                var email = selectedRep && selectedRep.email;
                if (!email || email === 'Non disponibile') {
                    showNotification('Email non disponibile per questo rappresentante.', 'error');
                    return;
                }
                var mailto = 'mailto:' + encodeURIComponent(email)
                           + '?subject=' + encodeURIComponent(subject)
                           + '&body=' + encodeURIComponent(body);
                try {
                    window.open(mailto, '_blank');
                    showSuccessMessage();
                } catch (error) {
                    console.error('Failed to open mail client:', error);
                    showCopyFallback(subject, body);
                }
            }

            // Send via OAuth (placeholder)
            function sendViaOAuth(subject, body) {
                alert('OAuth implementation coming soon');
                // TODO: Implement actual OAuth sending
                showSuccessMessage();
            }

            // Show success message
            function showSuccessMessage() {
                closeComposer();
                showNotification('Email preparata per ' + selectedRep.nome + ' ' + selectedRep.cognome, 'success');
            }

            // Show copy fallback
            function showCopyFallback(subject, body) {
                const text = `Oggetto: ${subject}\n\n${body}`;
                if (navigator.clipboard) {
                    navigator.clipboard.writeText(text);
                    showNotification('Testo copiato negli appunti', 'success');
                } else {
                    alert(`Impossibile aprire client email. Copia manualmente:\n\n${text}`);
                }
                closeComposer();
            }

            // Event listeners for composer
            document.addEventListener('DOMContentLoaded', function() {
                // Load themes when page loads
                loadThemes();
                
                // Theme selection change
                document.getElementById('themeSelect').addEventListener('change', onThemeChange);
                
                // Personal line character counter
                const personalLine = document.getElementById('personalLine');
                personalLine.addEventListener('input', function() {
                    updateCharCounter();
                    validateForm();
                });
                
                // Form validation on all inputs
                var formFields = ['themeSelect', 'subjectInput', 'personalLine'];
                for (var i = 0; i < formFields.length; i++) {
                    var id = formFields[i];
                    document.getElementById(id).addEventListener('change', validateForm);
                    document.getElementById(id).addEventListener('input', validateForm);
                }
                
                // Close modal when clicking outside
                document.getElementById('composerModal').addEventListener('click', function(e) {
                    if (e.target === this) {
                        closeComposer();
                    }
                });
                
                // Escape key to close
                document.addEventListener('keydown', function(e) {
                    if (e.key === 'Escape' && document.getElementById('composerModal').classList.contains('show')) {
                        closeComposer();
                    }
                });
            });
            
            function searchRepresentatives() {
                const query = document.getElementById('searchInput').value.trim();
                if (!query) {
                    alert('Inserisci il nome di un comune');
                    return;
                }
                
                const resultsDiv = document.getElementById('results');
                const contentDiv = document.getElementById('resultsContent');
                
                resultsDiv.style.display = 'block';
                contentDiv.innerHTML = '<div class="loading">Ricerca in corso...</div>';
                
                fetch('/api/lookup?q=' + encodeURIComponent(query))
                    .then(function(response) { return response.json(); })
                    .then(function(data) {
                        if (data.success) {
                            displayResults(data);
                        } else {
                            contentDiv.innerHTML = '<div class="error">Errore: ' + data.error + '</div>';
                        }
                    })
                    .catch(function(error) {
                        contentDiv.innerHTML = '<div class="error">Errore di connessione: ' + error.message + '</div>';
                    });
            }
            
            function displayResults(data) {
                const location = data.location;
                const reps = data.representatives;
                const summary = data.summary;
                
                // Store data in global variables for contact functions
                currentRepresentatives = reps;
                currentLocation = location;
                
                var html = '<h2>📍 ' + location.comune + ' (' + location.provincia + ') - ' + location.regione + '</h2>' +
                    '<p><strong>Totale rappresentanti trovati: ' + summary.total_representatives + '</strong></p>';
                
                // Camera
                if (reps.camera && reps.camera.length > 0) {
                    html += `
                    <div class="institution-section collapsed" id="camera-section">
                        <div class="institution-header" onclick="toggleSection('camera-section')">
                            <h3 class="institution-title">
                                🏛️ Camera dei Deputati
                                <span class="institution-count">${summary.deputati_count}</span>
                            </h3>
                            <span class="collapse-icon">▶</span>
                        </div>
                        <div class="institution-content">
                            <div class="institution-representatives">
                    `;
                    for (var i = 0; i < reps.camera.length; i++) {
                        var rep = reps.camera[i];
                        var partyCode = getPartyCode(rep.gruppo_partito);

                        html += `
                            <div class="representative">
                                <div class="rep-info">
                                    <div class="rep-name">${rep.nome} ${rep.cognome}</div>
                                    <div class="rep-details">Deputato · ${partyCode}</div>
                                    <div class="rep-collegio">Collegio: ${rep.collegio}</div>
                                </div>
                                <button class="rep-contact-btn"
                                        onclick="openComposer(${i}, 'camera')"
                                        ${(!rep.email || rep.email === 'Non disponibile') ? 'disabled' : ''}>
                                    Contatta
                                </button>
                            </div>`;
                    }
                    
                    html += `
                            </div>
                        </div>
                    </div>
                    `;
                }
                
                // Senato
                if (reps.senato && reps.senato.length > 0) {
                    html += `
                    <div class="institution-section collapsed" id="senato-section">
                        <div class="institution-header" onclick="toggleSection('senato-section')">
                            <h3 class="institution-title">
                                🏛️ Senato della Repubblica
                                <span class="institution-count">${summary.senatori_count}</span>
                            </h3>
                            <span class="collapse-icon">▶</span>
                        </div>
                        <div class="institution-content">
                            <div class="institution-representatives">
                    `;
                    for (var i = 0; i < reps.senato.length; i++) {
                        var rep = reps.senato[i];
                        var partyCode = getPartyCode(rep.gruppo_partito);

                        html += `
                            <div class="representative">
                                <div class="rep-info">
                                    <div class="rep-name">${rep.nome} ${rep.cognome}</div>
                                    <div class="rep-details">Senatore · ${partyCode}</div>
                                    <div class="rep-collegio">Regione: ${rep.regione}</div>
                                </div>
                                <button class="rep-contact-btn"
                                        onclick="openComposer(${i}, 'senato')"
                                        ${(!rep.email || rep.email === 'Non disponibile') ? 'disabled' : ''}>
                                    Contatta
                                </button>
                            </div>`;
                    }
                    
                    html += `
                            </div>
                        </div>
                    </div>
                    `;
                }
                
                // EU Parliament
                if (reps.eu_parliament && reps.eu_parliament.length > 0) {
                    html += `
                    <div class="institution-section collapsed" id="eu-section">
                        <div class="institution-header" onclick="toggleSection('eu-section')">
                            <h3 class="institution-title">
                                🇪🇺 Parlamento Europeo
                                <span class="institution-count">${summary.mep_count}</span>
                            </h3>
                            <span class="collapse-icon">▶</span>
                        </div>
                        <div class="institution-content">
                            <div class="institution-representatives">
                    `;
                    for (var i = 0; i < reps.eu_parliament.length; i++) {
                        var rep = reps.eu_parliament[i];
                        var partyCode = getPartyCode(rep.gruppo_partito);

                        html += `
                            <div class="representative">
                                <div class="rep-info">
                                    <div class="rep-name">${rep.nome} ${rep.cognome}</div>
                                    <div class="rep-details">MEP · ${partyCode}</div>
                                    <div class="rep-collegio">Circoscrizione: ${rep.circoscrizione_eu}</div>
                                </div>
                                <button class="rep-contact-btn"
                                        onclick="openComposer(${i}, 'eu')"
                                        ${(!rep.email || rep.email === 'Non disponibile') ? 'disabled' : ''}>
                                    Contatta
                                </button>
                            </div>`;
                    }
                    
                    html += `
                            </div>
                        </div>
                    </div>
                    `;
                }
                
                document.getElementById('resultsContent').innerHTML = html;
            }
            
            // Toggle collapsible sections
            function toggleSection(sectionId) {
                const section = document.getElementById(sectionId);
                const icon = section.querySelector('.collapse-icon');
                
                if (section.classList.contains('collapsed')) {
                    section.classList.remove('collapsed');
                    icon.textContent = '▼';
                } else {
                    section.classList.add('collapsed');
                    icon.textContent = '▶';
                }
            }
            
            // Allow Enter key to trigger search
            document.getElementById('searchInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    hideAutocomplete();
                    searchRepresentatives();
                }
            });
            
            // Initialize autocomplete
            console.log('Initializing autocomplete...');
            setupAutocomplete();
            console.log('Autocomplete initialized');
            


            
            function showNotification(message, type = 'info') {
                // Remove any existing notifications
                const existingNotifications = document.querySelectorAll('.notification');
                existingNotifications.forEach(notif => notif.remove());
                
                // Create notification element
                const notification = document.createElement('div');
                notification.className = `notification ${type}`;
                notification.textContent = message;
                
                // Add to DOM
                document.body.appendChild(notification);
                
                // Show notification
                setTimeout(() => {
                    notification.classList.add('show');
                }, 100);
                
                // Hide after 4 seconds
                setTimeout(() => {
                    notification.classList.remove('show');
                    setTimeout(() => {
                        if (notification.parentNode) {
                            notification.parentNode.removeChild(notification);
                        }
                    }, 300);
                }, 4000);
            }
        </script>
        
        <!-- Message Composer Modal -->
        <div id="composerModal" class="composer-modal">
            <div class="composer-content">
                <div class="composer-header">
                    <h2 id="composerTitle" class="composer-title">Scrivi a [Nome Cognome]</h2>
                    <p id="composerSubtitle" class="composer-subtitle">Collegio: [label] · Partito: [sigla]</p>
                </div>
                
                <div class="composer-body">
                    <!-- Theme Selection -->
                    <div class="composer-field">
                        <label class="composer-label required" for="themeSelect">Tema</label>
                        <select id="themeSelect" class="composer-select" required>
                            <option value="">Seleziona un tema...</option>
                        </select>
                    </div>
                    
                    <!-- Subject -->
                    <div class="composer-field">
                        <label class="composer-label required" for="subjectInput">Oggetto</label>
                        <input type="text" id="subjectInput" class="composer-input" required>
                    </div>
                    
                    <!-- Message Body -->
                    <div class="composer-field">
                        <label class="composer-label" for="bodyTextarea">Testo del messaggio</label>
                        <textarea id="bodyTextarea" class="composer-textarea" readonly></textarea>
                    </div>
                    
                    <!-- Personal Line (Required) -->
                    <div class="composer-field">
                        <label class="composer-label required" for="personalLine">Riga personale (obbligatoria)</label>
                        <textarea id="personalLine" class="composer-textarea composer-personal" 
                                placeholder="Aggiungi qui le tue considerazioni personali (minimo 20 caratteri)..." 
                                required minlength="20"></textarea>
                        <div id="personalCounter" class="char-counter">0 / 300 caratteri</div>
                    </div>
                    
                    <!-- Send Method -->
                    <div class="composer-field send-method">
                        <label class="composer-label">Metodo di invio</label>
                        <div class="radio-group">
                            <div class="radio-option">
                                <input type="radio" id="sendMailto" name="sendMethod" value="mailto" checked>
                                <label for="sendMailto">Apri nel mio client email</label>
                            </div>
                            <div class="radio-option">
                                <input type="radio" id="sendOAuth" name="sendMethod" value="oauth">
                                <label for="sendOAuth">Invia come me (Gmail/Outlook)</label>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="composer-footer">
                    <div class="footer-note">Non salviamo il testo della tua email.</div>
                    <div class="footer-buttons">
                        <button type="button" class="btn-secondary" onclick="closeComposer()">Annulla</button>
                        <button type="button" id="sendButton" class="btn-primary" onclick="sendMessage()" disabled>
                            Invia
                        </button>
                    </div>
                </div>
            </div>
        </div>
    
    </body>
    </html>
    '''
    return render_template_string(html_template)

if __name__ == '__main__':
    print("Starting Civic Bridge API Server...")
    print("API Endpoints:")
    print("  GET /api/lookup?q=Milano - Lookup representatives")
    print("  GET /api/representatives/camera - Get all deputies")
    print("  GET /api/representatives/senato - Get all senators")
    print("  GET /api/representatives/eu - Get all MEPs")
    print("  GET /api/health - Health check")
    print("  GET / - Web interface")
    print("\nServer starting on http://localhost:5000")
    
    app.run(debug=False, host='0.0.0.0', port=5000)