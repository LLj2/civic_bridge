#!/usr/bin/env python3
"""
Civic Bridge - Startup Script
Launches the API server with proper error handling
"""

import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import flask
        import flask_cors
        import pandas
        import requests
        import bs4
        print("All dependencies found")
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Run: venv/Scripts/pip.exe install flask flask-cors pandas requests beautifulsoup4")
        return False

def check_data_files():
    """Check if required data files exist"""
    required_files = [
        "data/comuni.csv",
        "data/collegi_camera.csv", 
        "data/collegi_senato.csv"
    ]
    
    missing = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(file_path)
    
    if missing:
        print("Missing required data files:")
        for file in missing:
            print(f"  - {file}")
        return False
    
    print("All required data files found")
    return True

def main():
    print("Civic Bridge - Starting Server")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check data files
    if not check_data_files():
        sys.exit(1)
    
    # Import and start server
    try:
        from api_server import app, init_lookup
        
        print("\nInitializing lookup system...")
        lookup = init_lookup()
        
        print("\nStarting web server...")
        print("   - Website: http://localhost:5000")
        print("   - API: http://localhost:5000/api/lookup?q=Milano")
        print("   - Health: http://localhost:5000/api/health")
        print("   - Press Ctrl+C to stop")
        print("\n" + "=" * 40)
        
        app.run(debug=False, host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()