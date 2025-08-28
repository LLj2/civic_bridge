#!/usr/bin/env python3
"""
Civic Bridge API Server - Modernized
Clean Flask app using templates and modular frontend
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import numpy as np
import pandas as pd
import logging
import traceback
import os
from civic_lookup import CivicLookup, clean_for_json
from config import config
from asset_helpers import get_css_files, get_js_files

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

def create_app(config_name=None):
    """Application factory"""
    app = Flask(__name__)
    app.json_encoder = NumpyEncoder
    
    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # CORS configuration
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Security headers
    @app.after_request
    def add_security_headers(response):
        # Content Security Policy - no inline scripts/styles
        csp_policy = app.config.get('CSP_POLICY', {})
        if csp_policy:
            csp_string = '; '.join([f"{k} {v}" for k, v in csp_policy.items()])
            response.headers['Content-Security-Policy'] = csp_string
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # No-cache for development
        if app.debug:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            
        return response
    
    # Setup logging
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    logging.basicConfig(level=log_level)
    logger = logging.getLogger(__name__)
    
    # Initialize lookup system
    lookup_system = None
    
    def init_lookup():
        nonlocal lookup_system
        if lookup_system is None:
            lookup_system = CivicLookup()
            lookup_system.load_data()
        return lookup_system
    
    # Routes
    @app.route('/')
    def index():
        """Main application page"""
        return render_template('index.html', 
                             css_files=get_css_files(),
                             js_files=get_js_files(),
                             is_debug=app.debug)
    
    @app.route('/favicon.ico')
    def favicon():
        """Favicon to prevent 404 noise"""
        return '', 204
    
    @app.route('/api/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'civic-bridge-api',
            'version': '2.0.0'
        })
    
    @app.route('/api/autocomplete')
    def autocomplete():
        """Autocomplete endpoint for city names"""
        try:
            query = request.args.get('q', '').strip()
            limit = int(request.args.get('limit', 1000))  # Return all matches by default
            
            if len(query) < 2:
                return jsonify({'success': False, 'error': 'Query too short'})
            
            system = init_lookup()
            
            # Smart autocomplete with prioritized sorting
            query_upper = query.upper()
            comuni_df = system._comuni_cache.copy()
            
            # 1. Exact matches (highest priority)
            exact_matches = comuni_df[comuni_df['comune'].str.upper() == query_upper]
            
            # 2. Starts with query (high priority)
            starts_with = comuni_df[
                (comuni_df['comune'].str.upper().str.startswith(query_upper)) &
                (comuni_df['comune'].str.upper() != query_upper)  # Exclude exact matches
            ]
            
            # 3. Contains query (lower priority)
            starts_with_mask = comuni_df['comune'].str.upper().str.startswith(query_upper)
            contains = comuni_df[
                (comuni_df['comune'].str.upper().str.contains(query_upper, na=False)) &
                (~starts_with_mask.fillna(False))  # Handle NaN values in mask
            ]
            
            # Major cities get bonus points (appear higher in their respective groups)
            major_cities = {'ROMA', 'MILANO', 'NAPOLI', 'TORINO', 'PALERMO', 'GENOVA', 'BOLOGNA', 
                           'FIRENZE', 'BARI', 'CATANIA', 'VENEZIA', 'VERONA', 'MESSINA', 'PADOVA', 
                           'TRIESTE', 'TARANTO', 'BRESCIA', 'PARMA', 'MODENA', 'REGGIO CALABRIA'}
            
            def sort_group(df_group):
                """Sort a group with major cities first, then alphabetically"""
                if df_group.empty:
                    return df_group
                
                # Separate major cities from others
                major = df_group[df_group['comune'].str.upper().isin(major_cities)]
                others = df_group[~df_group['comune'].str.upper().isin(major_cities)]
                
                # Sort each group alphabetically, then concatenate
                major_sorted = major.sort_values('comune') if not major.empty else major
                others_sorted = others.sort_values('comune') if not others.empty else others
                
                return pd.concat([major_sorted, others_sorted], ignore_index=True)
            
            # Sort each group and combine with proper prioritization
            exact_sorted = sort_group(exact_matches)
            starts_sorted = sort_group(starts_with) 
            contains_sorted = sort_group(contains)
            
            # Combine results: exact → starts_with → contains (handle empty DataFrames)
            dfs_to_concat = [df for df in [exact_sorted, starts_sorted, contains_sorted] if not df.empty]
            
            if dfs_to_concat:
                all_matches = pd.concat(dfs_to_concat, ignore_index=True)
            else:
                all_matches = pd.DataFrame()  # Empty DataFrame if no matches
            
            # Limit results to prevent overwhelming the UI (10-15 is usually optimal)
            final_limit = min(limit, 15)
            limited_matches = all_matches.head(final_limit)
            
            results = []
            for _, row in limited_matches.iterrows():
                results.append({
                    'comune': clean_for_json(row['comune']),
                    'provincia': clean_for_json(row['provincia']),
                    'regione': clean_for_json(row['regione']),
                    'display': f"{clean_for_json(row['comune'])} ({clean_for_json(row['provincia'])}) - {clean_for_json(row['regione'])}"
                })
            
            return jsonify({
                'success': True,
                'results': results,
                'query': query
            })
            
        except Exception as e:
            logger.error(f"Autocomplete error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @app.route('/api/lookup')
    def lookup_representatives():
        """Main lookup endpoint"""
        try:
            query = request.args.get('q', '').strip()
            if not query:
                return jsonify({'success': False, 'error': 'Missing query parameter'})
            
            system = init_lookup()
            result = system.lookup_representatives(query)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Lookup error: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @app.route('/api/representatives/camera')
    def get_camera_representatives():
        """Get all Camera representatives"""
        try:
            system = init_lookup()
            if system._deputati_cache is not None:
                reps = []
                for _, row in system._deputati_cache.iterrows():
                    reps.append({
                        'nome': clean_for_json(row.get('nome', '')),
                        'cognome': clean_for_json(row.get('cognome', '')),
                        'gruppo_partito': clean_for_json(row.get('gruppo_partito', '')),
                        'collegio': clean_for_json(row.get('collegio', '')),
                        'email': clean_for_json(row.get('email_istituzionale', ''))
                    })
                return jsonify({'success': True, 'representatives': reps})
            else:
                return jsonify({'success': False, 'error': 'No data available'})
        except Exception as e:
            logger.error(f"Camera representatives error: {str(e)}")
            return jsonify({'success': False, 'error': 'Internal server error'}), 500
    
    @app.route('/api/representatives/senato')
    def get_senato_representatives():
        """Get all Senato representatives"""
        try:
            system = init_lookup()
            if system._senatori_cache is not None:
                reps = []
                for _, row in system._senatori_cache.iterrows():
                    reps.append({
                        'nome': clean_for_json(row.get('nome', '')),
                        'cognome': clean_for_json(row.get('cognome', '')),
                        'gruppo_partito': clean_for_json(row.get('gruppo_partito', '')),
                        'regione': clean_for_json(row.get('regione', '')),
                        'email': clean_for_json(row.get('email_istituzionale', ''))
                    })
                return jsonify({'success': True, 'representatives': reps})
            else:
                return jsonify({'success': False, 'error': 'No data available'})
        except Exception as e:
            logger.error(f"Senato representatives error: {str(e)}")
            return jsonify({'success': False, 'error': 'Internal server error'}), 500
    
    @app.route('/api/representatives/eu')
    def get_eu_representatives():
        """Get all EU representatives"""
        try:
            system = init_lookup()
            if system._mep_cache is not None:
                reps = []
                for _, row in system._mep_cache.iterrows():
                    reps.append({
                        'nome': clean_for_json(row.get('nome', '')),
                        'cognome': clean_for_json(row.get('cognome', '')),
                        'gruppo_partito': clean_for_json(row.get('gruppo_partito', '')),
                        'circoscrizione_eu': clean_for_json(row.get('circoscrizione_eu', '')),
                        'email': clean_for_json(row.get('email_istituzionale', ''))
                    })
                return jsonify({'success': True, 'representatives': reps})
            else:
                return jsonify({'success': False, 'error': 'No data available'})
        except Exception as e:
            logger.error(f"EU representatives error: {str(e)}")
            return jsonify({'success': False, 'error': 'Internal server error'}), 500
    
    @app.route('/api/themes')
    def get_themes():
        """Get themes and topics configuration"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config', 'themes.json')
            
            if not os.path.exists(config_path):
                # Fallback to hardcoded themes if config file doesn't exist
                logger.warning(f"Themes config file not found at {config_path}, using fallback")
                return jsonify({
                    'success': True,
                    'themes': {
                        'altro': {
                            'title': 'Altro argomento',
                            'description': 'Per argomenti generici',
                            'topics': []
                        }
                    },
                    'templates': {
                        'subject': 'Richiesta da cittadino di {comune}: {tema}',
                        'body': {
                            'greeting': 'Gentile {titolo} {cognome},',
                            'introduction': 'Le scrivo come cittadino di {comune} in merito a {tema}.',
                            'topics_header': 'Punti principali:',
                            'closing': 'Cordiali saluti,\n[Firma opzionale]'
                        }
                    },
                    'version': 'fallback'
                })
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Ensure themes are returned in file order by using OrderedDict
            # or converting to list of key-value pairs to preserve order
            themes_dict = config.get('themes', {})
            
            return jsonify({
                'success': True,
                'themes': themes_dict,  # JSON preserves order in Python 3.7+
                'templates': config.get('templates', {}),
                'version': config.get('version', 'unknown'),
                'updated': config.get('updated', 'unknown')
            })
            
        except Exception as e:
            logger.error(f"Themes config error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Failed to load themes configuration'
            }), 500
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    print("Starting Civic Bridge API Server...")
    print("API Endpoints:")
    print("  GET / - Main application")
    print("  GET /api/health - Health check")
    print("  GET /api/autocomplete?q=Milano - Autocomplete cities")
    print("  GET /api/lookup?q=Milano - Lookup representatives")
    print("  GET /api/representatives/camera - Get all deputies")
    print("  GET /api/representatives/senato - Get all senators")
    print("  GET /api/representatives/eu - Get all MEPs")
    print("  GET /api/themes - Get themes and topics configuration")
    print("")
    print("Server starting on http://localhost:5000")
    
    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=5000,
        use_reloader=True
    )