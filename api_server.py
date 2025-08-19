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
    limit = min(int(request.args.get('limit', 10)), 50)  # Max 50 results
    
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
        
        <!-- Message Composer Modal -->
        <div id="messageComposerModal" class="modal-overlay">
            <div class="message-composer">
                <div class="composer-header">
                    <div>
                        <h3 class="composer-title">Invia messaggio diretto</h3>
                        <div class="composer-recipient" id="composerRecipient"></div>
                    </div>
                    <button class="close-btn" onclick="closeMessageComposer()">&times;</button>
                </div>
                
                <div class="composer-body">
                    <div class="oauth-section">
                        <div class="oauth-title">Scegli il tuo provider email:</div>
                        <div class="oauth-options">
                            <button class="oauth-btn gmail" onclick="authenticateEmail('gmail')">
                                <span>📧</span> Gmail
                            </button>
                            <button class="oauth-btn outlook" onclick="authenticateEmail('outlook')">
                                <span>📧</span> Outlook
                            </button>
                        </div>
                        <div id="authStatus" style="margin-top: 12px; font-size: 13px; color: #4a5568;"></div>
                    </div>
                    
                    <form id="messageForm">
                        <div class="form-group">
                            <label class="form-label" for="senderName">Il tuo nome *</label>
                            <input type="text" id="senderName" class="form-input" placeholder="Mario Rossi" required>
                        </div>
                        
                        <div class="form-group" style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 12px; margin: 16px 0;">
                            <label style="display: flex; align-items: center; gap: 8px; font-weight: 500; color: #856404;">
                                <input type="checkbox" id="testMode" style="margin: 0;"> 
                                🧪 Modalità Test - Invia a me invece che al rappresentante
                            </label>
                            <div id="testEmailInput" style="display: none; margin-top: 8px;">
                                <input type="email" id="testEmail" class="form-input" placeholder="tua-email@example.com" style="font-size: 13px;">
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label" for="messageSubject">Oggetto</label>
                            <input type="text" id="messageSubject" class="form-input" readonly>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label" for="messageBody">Messaggio *</label>
                            <textarea id="messageBody" class="form-input form-textarea" required></textarea>
                        </div>
                    </form>
                </div>
                
                <div class="composer-actions">
                    <button class="btn-secondary" onclick="closeMessageComposer()">Annulla</button>
                    <button class="btn-primary" id="sendButton" onclick="sendMessage()" disabled>
                        <span>🚀</span> Invia Messaggio
                    </button>
                </div>
            </div>
        </div>
        
        <script>
            let autocompleteTimeout;
            let selectedComune = '';
            
            function setupAutocomplete() {
                console.log('Setting up autocomplete...');
                const input = document.getElementById('searchInput');
                const list = document.getElementById('autocompleteList');
                
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
                    const query = this.value.trim();
                    
                    clearTimeout(autocompleteTimeout);
                    
                    if (query.length < 2) {
                        hideAutocomplete();
                        return;
                    }
                    
                    autocompleteTimeout = setTimeout(() => {
                        fetchAutocomplete(query);
                    }, 300);
                });
                
                input.addEventListener('blur', function() {
                    // Hide after small delay to allow clicks
                    setTimeout(() => hideAutocomplete(), 200);
                });
                
                input.addEventListener('focus', function() {
                    if (this.value.length >= 2) {
                        fetchAutocomplete(this.value.trim());
                    }
                });
            }
            
            function fetchAutocomplete(query) {
                fetch(`/api/autocomplete?q=${encodeURIComponent(query)}&limit=8`)
                    .then(response => response.json())
                    .then(data => {
                        console.log('Autocomplete response:', data);
                        if (data.success && data.results.length > 0) {
                            showAutocompleteResults(data.results);
                        } else {
                            hideAutocomplete();
                        }
                    })
                    .catch(error => {
                        console.error('Autocomplete error:', error);
                        hideAutocomplete();
                    });
            }
            
            function showAutocompleteResults(results) {
                console.log('Showing autocomplete results:', results);
                const list = document.getElementById('autocompleteList');
                list.innerHTML = '';
                
                results.forEach(result => {
                    const item = document.createElement('div');
                    item.className = 'autocomplete-item';
                    item.textContent = result.display;
                    item.addEventListener('click', () => {
                        document.getElementById('searchInput').value = result.comune;
                        selectedComune = result.comune;
                        hideAutocomplete();
                        searchRepresentatives();
                    });
                    list.appendChild(item);
                });
                
                list.style.display = 'block';
                console.log('Autocomplete list shown with', results.length, 'items');
            }
            
            function hideAutocomplete() {
                document.getElementById('autocompleteList').style.display = 'none';
            }
            
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
                
                fetch(`/api/lookup?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            displayResults(data);
                        } else {
                            contentDiv.innerHTML = `<div class="error">Errore: ${data.error}</div>`;
                        }
                    })
                    .catch(error => {
                        contentDiv.innerHTML = `<div class="error">Errore di connessione: ${error.message}</div>`;
                    });
            }
            
            function displayResults(data) {
                const location = data.location;
                const reps = data.representatives;
                const summary = data.summary;
                
                // Store data in global variables for contact functions
                currentRepresentatives = reps;
                currentLocation = location;
                
                let html = `
                    <h2>📍 ${location.comune} (${location.provincia}) - ${location.regione}</h2>
                    <p><strong>Totale rappresentanti trovati: ${summary.total_representatives}</strong></p>
                `;
                
                // Camera
                if (reps.camera && reps.camera.length > 0) {
                    html += `<h3>🏛️ Camera dei Deputati (${summary.deputati_count})</h3>`;
                    reps.camera.forEach((rep, i) => {
                        html += `
                            <div class="representative">
                                <div class="rep-header">
                                    <div>
                                        <h4 class="rep-name">${rep.nome} ${rep.cognome}</h4>
                                        <div class="rep-party">${rep.gruppo_partito}</div>
                                        <div class="rep-details">Collegio: ${rep.collegio}</div>
                                    </div>
                                </div>
                                
                                <div class="contact-section">
                                    <div class="email-display">📧 ${rep.email || 'Email non disponibile'}</div>
                                    ${rep.email && rep.email !== 'Non disponibile' ? `
                                        <div class="contact-options">
                                            <button class="contact-btn btn-email" onclick="openMailClient(${i}, 'camera', '${location.comune.replace(/'/g, "\\'")}')" >
                                                📧 Apri Email Client
                                            </button>
                                            <button class="contact-btn btn-send-direct" onclick="sendDirectMessage(${i}, 'camera', '${location.comune.replace(/'/g, "\\'")}')" >
                                                🚀 Invia Diretto
                                            </button>
                                        </div>
                                    ` : ''}
                                </div>
                            </div>
                        `;
                    });
                }
                
                // Senato
                if (reps.senato && reps.senato.length > 0) {
                    html += `<h3>🏛️ Senato della Repubblica (${summary.senatori_count})</h3>`;
                    reps.senato.forEach((rep, i) => {
                        html += `
                            <div class="representative">
                                <div class="rep-header">
                                    <div>
                                        <h4 class="rep-name">${rep.nome} ${rep.cognome}</h4>
                                        <div class="rep-party">${rep.gruppo_partito}</div>
                                        <div class="rep-details">Regione: ${rep.regione}</div>
                                    </div>
                                </div>
                                
                                <div class="contact-section">
                                    <div class="email-display">📧 ${rep.email || 'Email non disponibile'}</div>
                                    ${rep.email && rep.email !== 'Non disponibile' ? `
                                        <div class="contact-options">
                                            <button class="contact-btn btn-email" onclick="openMailClient(${i}, 'senato', '${location.comune.replace(/'/g, "\\'")}')" >
                                                📧 Apri Email Client
                                            </button>
                                            <button class="contact-btn btn-send-direct" onclick="sendDirectMessage(${i}, 'senato', '${location.comune.replace(/'/g, "\\'")}')" >
                                                🚀 Invia Diretto
                                            </button>
                                        </div>
                                    ` : ''}
                                </div>
                            </div>
                        `;
                    });
                }
                
                // EU Parliament
                if (reps.eu_parliament && reps.eu_parliament.length > 0) {
                    html += `<h3>🇪🇺 Parlamento Europeo (${summary.mep_count})</h3>`;
                    reps.eu_parliament.forEach((rep, i) => {
                        html += `
                            <div class="representative">
                                <div class="rep-header">
                                    <div>
                                        <h4 class="rep-name">${rep.nome} ${rep.cognome}</h4>
                                        <div class="rep-party">${rep.gruppo_partito}</div>
                                        <div class="rep-details">Circoscrizione: ${rep.circoscrizione_eu}</div>
                                    </div>
                                </div>
                                
                                <div class="contact-section">
                                    <div class="email-display">📧 ${rep.email || 'Email non disponibile'}</div>
                                    ${rep.email && rep.email !== 'Non disponibile' ? `
                                        <div class="contact-options">
                                            <button class="contact-btn btn-email" onclick="openMailClient(${i}, 'eu', '${location.comune.replace(/'/g, "\\'")}')" >
                                                📧 Apri Email Client
                                            </button>
                                            <button class="contact-btn btn-send-direct" onclick="sendDirectMessage(${i}, 'eu', '${location.comune.replace(/'/g, "\\'")}')" >
                                                🚀 Invia Diretto
                                            </button>
                                        </div>
                                    ` : ''}
                                </div>
                            </div>
                        `;
                    });
                }
                
                document.getElementById('resultsContent').innerHTML = html;
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
            
            // Global variables to store representatives data
            let currentRepresentatives = null;
            let currentLocation = null;
            
            // Updated contact functions that use indices
            function openMailClient(index, repType, userLocation) {
                if (!currentRepresentatives || !currentRepresentatives[repType] || !currentRepresentatives[repType][index]) {
                    console.error('Representative not found:', index, repType);
                    return;
                }
                const rep = currentRepresentatives[repType][index];
                
                if (!rep.email || rep.email === 'Non disponibile') {
                    showNotification("Email non disponibile per questo rappresentante.", "error");
                    return;
                }
                
                try {
                    const mailto = createMailto(rep, repType, userLocation);
                    window.open(mailto, '_blank');
                    showNotification("Client email aperto! Verifica che il messaggio sia stato creato correttamente.", "success");
                } catch (error) {
                    console.error("Error creating mailto:", error);
                    showNotification("Errore nell'apertura del client email. Prova a copiare l'email manualmente.", "error");
                }
            }
            
            function sendDirectMessage(index, repType, userLocation) {
                if (!currentRepresentatives || !currentRepresentatives[repType] || !currentRepresentatives[repType][index]) {
                    console.error('Representative not found:', index, repType);
                    return;
                }
                const rep = currentRepresentatives[repType][index];
                openMessageComposer(rep, repType, userLocation);
            }
            
            // Contact functionality
            function createMailto(rep, repType, userLocation) {
                const templates = getMessageTemplates();
                const template = templates[repType] || templates.default;
                
                const subject = template.subject
                    .replace('{{rep_name}}', `${rep.nome} ${rep.cognome}`)
                    .replace('{{location}}', userLocation);
                    
                const body = template.body
                    .replace('{{rep_name}}', `${rep.nome} ${rep.cognome}`)
                    .replace('{{rep_title}}', getRepresentativeTitle(repType))
                    .replace('{{location}}', userLocation)
                    .replace('{{user_name}}', '[Il tuo nome]');
                
                const mailto = `mailto:${rep.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
                return mailto;
            }
            
            function getRepresentativeTitle(repType) {
                const titles = {
                    'camera': 'Onorevole Deputato/a',
                    'senato': 'Onorevole Senatore/Senatrice',
                    'eu': 'Onorevole Deputato/a Europeo/a'
                };
                return titles[repType] || 'Gentile Rappresentante';
            }
            
            function getMessageTemplates() {
                return {
                    camera: {
                        subject: 'Cittadino di {{location}} - Richiesta informazioni',
                        body: `Gentile {{rep_title}} {{rep_name}},

sono {{user_name}}, cittadino/a di {{location}}.

Vi scrivo per [descrivere brevemente la questione o richiesta].

[Aggiungere qui il contenuto del messaggio]

Ringrazio per l'attenzione e resto in attesa di un riscontro.

Cordiali saluti,
{{user_name}}

---
Messaggio inviato tramite Civic Bridge (https://civic-bridge.it)`
                    },
                    senato: {
                        subject: 'Cittadino di {{location}} - Richiesta informazioni',
                        body: `Gentile {{rep_title}} {{rep_name}},

sono {{user_name}}, cittadino/a di {{location}}.

Vi scrivo per [descrivere brevemente la questione o richiesta].

[Aggiungere qui il contenuto del messaggio]

Ringrazio per l'attenzione e resto in attesa di un riscontro.

Cordiali saluti,
{{user_name}}

---
Messaggio inviato tramite Civic Bridge (https://civic-bridge.it)`
                    },
                    eu: {
                        subject: 'Cittadino italiano - Richiesta informazioni EU',
                        body: `Gentile {{rep_title}} {{rep_name}},

sono {{user_name}}, cittadino/a italiano/a residente a {{location}}.

Vi scrivo per [descrivere brevemente la questione europea o richiesta].

[Aggiungere qui il contenuto del messaggio]

Ringrazio per l'attenzione e resto in attesa di un riscontro.

Cordiali saluti,
{{user_name}}

---
Messaggio inviato tramite Civic Bridge (https://civic-bridge.it)`
                    }
                };
            }
            
            
            // Global variables for message composer
            let currentRepresentative = null;
            let currentRepType = null;
            let currentUserLocation = null;
            let isAuthenticated = false;
            let authProvider = null;
            
            
            function openMessageComposer(rep, repType, userLocation) {
                if (!rep) return;
                
                // Store current context in global variables
                currentRepresentative = rep;
                currentRepType = repType;
                currentUserLocation = userLocation;
                
                // Update modal header
                const recipientDiv = document.getElementById('composerRecipient');
                recipientDiv.textContent = `A: ${currentRepresentative.nome} ${currentRepresentative.cognome} (${currentRepresentative.email})`;
                
                // Pre-fill the form
                const templates = getMessageTemplates();
                const template = templates[currentRepType] || templates.camera;
                
                const subjectInput = document.getElementById('messageSubject');
                const bodyTextarea = document.getElementById('messageBody');
                
                subjectInput.value = template.subject
                    .replace('{{rep_name}}', `${currentRepresentative.nome} ${currentRepresentative.cognome}`)
                    .replace('{{location}}', currentUserLocation);
                
                bodyTextarea.value = template.body
                    .replace('{{rep_name}}', `${currentRepresentative.nome} ${currentRepresentative.cognome}`)
                    .replace('{{rep_title}}', getRepresentativeTitle(currentRepType))
                    .replace('{{location}}', currentUserLocation)
                    .replace('{{user_name}}', '[Il tuo nome]');
                
                // Show modal
                const modal = document.getElementById('messageComposerModal');
                modal.classList.add('show');
                
                // Setup form validation and focus
                setTimeout(() => {
                    setupFormValidation();
                    setupTestMode();
                    document.getElementById('senderName').focus();
                }, 300);
            }
            
            function closeMessageComposer() {
                const modal = document.getElementById('messageComposerModal');
                modal.classList.remove('show');
                
                // Reset form
                document.getElementById('messageForm').reset();
                document.getElementById('authStatus').textContent = '';
                isAuthenticated = false;
                authProvider = null;
                updateSendButton();
            }
            
            // OAuth Authentication Functions
            function authenticateEmail(provider) {
                const authStatus = document.getElementById('authStatus');
                authStatus.textContent = `Collegamento con ${provider}...`;
                
                if (provider === 'gmail') {
                    authenticateGmail();
                } else if (provider === 'outlook') {
                    authenticateOutlook();
                }
            }
            
            async function authenticateGmail() {
                try {
                    const response = await fetch('/api/auth/gmail', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        // For MVP, simulate successful authentication
                        // In production, would handle OAuth redirect flow
                        setTimeout(() => {
                            isAuthenticated = true;
                            authProvider = 'gmail';
                            document.getElementById('authStatus').innerHTML = 
                                '<span style="color: #38a169;">✓ Gmail collegato</span>';
                            updateSendButton();
                            showNotification("Gmail collegato con successo!", "success");
                        }, 1000);
                    } else {
                        showNotification("Errore collegamento Gmail: " + data.error, "error");
                    }
                } catch (error) {
                    console.error('Gmail auth error:', error);
                    showNotification("Errore di connessione. Riprova.", "error");
                }
            }
            
            async function authenticateOutlook() {
                try {
                    const response = await fetch('/api/auth/outlook', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        // For MVP, simulate successful authentication
                        // In production, would handle OAuth redirect flow
                        setTimeout(() => {
                            isAuthenticated = true;
                            authProvider = 'outlook';
                            document.getElementById('authStatus').innerHTML = 
                                '<span style="color: #38a169;">✓ Outlook collegato</span>';
                            updateSendButton();
                            showNotification("Outlook collegato con successo!", "success");
                        }, 1000);
                    } else {
                        showNotification("Errore collegamento Outlook: " + data.error, "error");
                    }
                } catch (error) {
                    console.error('Outlook auth error:', error);
                    showNotification("Errore di connessione. Riprova.", "error");
                }
            }
            
            function updateSendButton() {
                const sendButton = document.getElementById('sendButton');
                const senderName = document.getElementById('senderName').value.trim();
                const messageBody = document.getElementById('messageBody').value.trim();
                
                const canSend = isAuthenticated && senderName && messageBody;
                sendButton.disabled = !canSend;
            }
            
            // Test mode setup
            function setupTestMode() {
                const testModeCheckbox = document.getElementById('testMode');
                const testEmailInput = document.getElementById('testEmailInput');
                
                testModeCheckbox.addEventListener('change', function() {
                    if (this.checked) {
                        testEmailInput.style.display = 'block';
                        document.getElementById('testEmail').required = true;
                    } else {
                        testEmailInput.style.display = 'none';
                        document.getElementById('testEmail').required = false;
                    }
                    updateSendButton();
                });
            }
            
            // Form validation - setup when modal opens
            function setupFormValidation() {
                const senderNameInput = document.getElementById('senderName');
                const messageBodyInput = document.getElementById('messageBody');
                
                if (senderNameInput && messageBodyInput) {
                    // Remove any existing listeners first
                    senderNameInput.removeEventListener('input', updateSendButton);
                    messageBodyInput.removeEventListener('input', updateSendButton);
                    
                    // Add listeners
                    senderNameInput.addEventListener('input', updateSendButton);
                    messageBodyInput.addEventListener('input', updateSendButton);
                    
                    // Auto-replace placeholder in message body
                    senderNameInput.addEventListener('input', function() {
                        const messageBody = messageBodyInput.value;
                        const updatedBody = messageBody.replace(/\[Il tuo nome\]/g, this.value || '[Il tuo nome]');
                        messageBodyInput.value = updatedBody;
                    });
                }
            }
            
            // Send message function (updated)
            async function sendMessage() {
                if (!isAuthenticated) {
                    showNotification("Prima devi collegarti a Gmail o Outlook", "error");
                    return;
                }
                
                const sendButton = document.getElementById('sendButton');
                const originalText = sendButton.innerHTML;
                
                try {
                    // Update button state
                    sendButton.disabled = true;
                    sendButton.innerHTML = '<span>⏳</span> Invio in corso...';
                    
                    // Check if test mode is enabled
                    const testMode = document.getElementById('testMode').checked;
                    const recipientEmail = testMode ? 
                        document.getElementById('testEmail').value : 
                        currentRepresentative.email;
                    
                    const messageData = {
                        to: recipientEmail,
                        subject: document.getElementById('messageSubject').value,
                        body: document.getElementById('messageBody').value,
                        senderName: document.getElementById('senderName').value,
                        provider: authProvider,
                        representative: currentRepresentative,
                        repType: currentRepType,
                        location: currentUserLocation,
                        testMode: testMode
                    };
                    
                    // Send email via API
                    const response = await fetch('/api/send-email', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(messageData)
                    });
                    
                    const result = await response.json();
                    
                    if (!result.success) {
                        throw new Error(result.error || 'Send failed');
                    }
                    
                    showNotification("Messaggio inviato con successo!", "success");
                    closeMessageComposer();
                    
                } catch (error) {
                    console.error('Send error:', error);
                    showNotification("Errore nell'invio del messaggio. Riprova.", "error");
                    sendButton.disabled = false;
                    sendButton.innerHTML = originalText;
                }
            }
            
            async function simulateEmailSend(messageData) {
                // Simulate API call delay
                return new Promise((resolve) => {
                    setTimeout(() => {
                        console.log('Email would be sent:', messageData);
                        resolve();
                    }, 2000);
                });
            }
            
            // Close modal when clicking outside
            document.addEventListener('click', function(event) {
                const modal = document.getElementById('messageComposerModal');
                if (event.target === modal) {
                    closeMessageComposer();
                }
            });
            
            // Close modal with Escape key
            document.addEventListener('keydown', function(event) {
                if (event.key === 'Escape') {
                    const modal = document.getElementById('messageComposerModal');
                    if (modal.classList.contains('show')) {
                        closeMessageComposer();
                    }
                }
            });
            
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