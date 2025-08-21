"""
Asset handling utilities for production builds
"""
import json
import os
from flask import current_app

_manifest = None

def load_manifest():
    """Load asset manifest from dist/manifest.json"""
    global _manifest
    if _manifest is None:
        manifest_path = os.path.join('dist', 'manifest.json')
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r') as f:
                _manifest = json.load(f)
        else:
            _manifest = {}
    return _manifest

def asset_url(filename):
    """Get the URL for an asset, using hashed version in production"""
    if current_app.config.get('DEBUG', False):
        # Development mode - use original files
        if filename == 'app.min.css':
            return 'css/main.css'  # Use original CSS in dev
        elif filename == 'app.min.js':
            return 'js/main.js'    # Use original JS in dev
        return filename
    else:
        # Production mode - use hashed files
        manifest = load_manifest()
        return f"../dist/{manifest.get(filename, filename)}"

def get_css_files():
    """Get list of CSS files for template"""
    if current_app.config.get('DEBUG', False):
        # Development - separate files
        return [
            'css/main.css',
            'css/components.css', 
            'css/responsive.css'
        ]
    else:
        # Production - single minified file
        return [asset_url('app.min.css')]

def get_js_files():
    """Get list of JS files for template"""
    if current_app.config.get('DEBUG', False):
        # Development - separate modules
        return ['js/main.js']  # main.js imports others
    else:
        # Production - single minified file (not as module)
        return [asset_url('app.min.js')]