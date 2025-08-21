#!/usr/bin/env python3
"""
Simple build script for Civic Bridge assets
Concatenates and minifies CSS/JS without external dependencies
"""

import os
import re
import json
import hashlib
import shutil
from pathlib import Path

# Build configuration
STATIC_DIR = Path('static')
DIST_DIR = Path('dist')
CSS_FILES = ['css/main.css', 'css/components.css', 'css/responsive.css']
JS_FILES = ['js/state.js', 'js/search.js', 'js/composer.js', 'js/main.js']

def ensure_dir(path):
    """Create directory if it doesn't exist"""
    path.mkdir(parents=True, exist_ok=True)

def minify_css(content):
    """Simple CSS minification"""
    # Remove comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # Remove extra whitespace
    content = re.sub(r'\s+', ' ', content)
    # Remove spaces around certain characters
    content = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', content)
    return content.strip()

def minify_js(content):
    """Very basic JS minification (removes comments and excess whitespace)"""
    # Remove single-line comments (but preserve URLs)
    lines = []
    for line in content.split('\n'):
        # Only remove // comments if they're not part of URLs
        if '//' in line and not ('http://' in line or 'https://' in line):
            comment_pos = line.find('//')
            # Check if // is inside a string
            in_string = False
            quote_char = None
            for i, char in enumerate(line[:comment_pos]):
                if char in ['"', "'"]:
                    if not in_string:
                        in_string = True
                        quote_char = char
                    elif char == quote_char and line[i-1] != '\\':
                        in_string = False
                        quote_char = None
            
            if not in_string:
                line = line[:comment_pos]
        
        lines.append(line)
    
    content = '\n'.join(lines)
    
    # Remove multi-line comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # Remove extra whitespace but preserve necessary spaces
    content = re.sub(r'\n\s*\n', '\n', content)
    content = re.sub(r'  +', ' ', content)
    return content.strip()

def get_file_hash(file_path):
    """Get SHA256 hash of file content (first 8 chars)"""
    with open(file_path, 'rb') as f:
        content = f.read()
        return hashlib.sha256(content).hexdigest()[:8]

def build_css():
    """Build concatenated and minified CSS"""
    print("📦 Building CSS...")
    
    combined_content = []
    for css_file in CSS_FILES:
        file_path = STATIC_DIR / css_file
        if file_path.exists():
            print(f"   • {css_file}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                combined_content.append(f"/* {css_file} */")
                combined_content.append(content)
        else:
            print(f"   ⚠ {css_file} not found")
    
    # Write unminified version
    combined = '\n\n'.join(combined_content)
    app_css_path = DIST_DIR / 'app.css'
    with open(app_css_path, 'w', encoding='utf-8') as f:
        f.write(combined)
    
    # Write minified version
    minified = minify_css(combined)
    app_min_css_path = DIST_DIR / 'app.min.css'
    with open(app_min_css_path, 'w', encoding='utf-8') as f:
        f.write(minified)
    
    print(f"   ✓ Created {app_css_path} ({len(combined):,} chars)")
    print(f"   ✓ Created {app_min_css_path} ({len(minified):,} chars)")
    
    return app_min_css_path

def build_js():
    """Build concatenated and minified JS"""
    print("📦 Building JavaScript...")
    
    combined_content = []
    
    # For production build, we need to convert ES modules to regular JS
    # This is a simple approach - in a real build system you'd use a bundler
    
    for js_file in JS_FILES:
        file_path = STATIC_DIR / js_file
        if file_path.exists():
            print(f"   • {js_file}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Convert ES module syntax for production build
                if js_file != 'js/main.js':  # Don't process main.js imports
                    # Remove export statements and convert to global assignments
                    if 'state.js' in js_file:
                        content = re.sub(r'export\s+function\s+(\w+)', r'window.\1 = function', content)
                        content = re.sub(r'export\s+\{[^}]+\}', '', content)
                    else:
                        content = re.sub(r'export\s+\{[^}]+\}', '', content)
                        content = re.sub(r'export\s+function\s+(\w+)', r'window.\1 = function', content)
                
                # Remove import statements
                content = re.sub(r'import\s+\{[^}]+\}\s+from\s+[\'"][^\'\"]+[\'"];?\n?', '', content)
                content = re.sub(r'import\s+[^\s]+\s+from\s+[\'"][^\'\"]+[\'"];?\n?', '', content)
                
                combined_content.append(f"// {js_file}")
                combined_content.append(content)
        else:
            print(f"   ⚠ {js_file} not found")
    
    # Write unminified version
    combined = '\n\n'.join(combined_content)
    app_js_path = DIST_DIR / 'app.js'
    with open(app_js_path, 'w', encoding='utf-8') as f:
        f.write(combined)
    
    # Write minified version
    minified = minify_js(combined)
    app_min_js_path = DIST_DIR / 'app.min.js'
    with open(app_min_js_path, 'w', encoding='utf-8') as f:
        f.write(minified)
    
    print(f"   ✓ Created {app_js_path} ({len(combined):,} chars)")
    print(f"   ✓ Created {app_min_js_path} ({len(minified):,} chars)")
    
    return app_min_js_path

def generate_manifest():
    """Generate asset manifest with hashes"""
    print("📋 Generating asset manifest...")
    
    manifest = {}
    
    # CSS
    css_path = DIST_DIR / 'app.min.css'
    if css_path.exists():
        hash_val = get_file_hash(css_path)
        hashed_name = f'app.{hash_val}.min.css'
        hashed_path = DIST_DIR / hashed_name
        
        # Copy file content instead of using shutil.copy2 to avoid permission issues
        with open(css_path, 'r', encoding='utf-8') as src, open(hashed_path, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
            
        manifest['app.min.css'] = hashed_name
        print(f"   ✓ CSS: {hashed_name}")
    
    # JS
    js_path = DIST_DIR / 'app.min.js'
    if js_path.exists():
        hash_val = get_file_hash(js_path)
        hashed_name = f'app.{hash_val}.min.js'
        hashed_path = DIST_DIR / hashed_name
        
        # Copy file content instead of using shutil.copy2 to avoid permission issues
        with open(js_path, 'r', encoding='utf-8') as src, open(hashed_path, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
            
        manifest['app.min.js'] = hashed_name
        print(f"   ✓ JS: {hashed_name}")
    
    # Write manifest
    manifest_path = DIST_DIR / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"   ✓ Manifest: {manifest_path}")
    return manifest

def main():
    """Main build process"""
    print("🚀 Starting Civic Bridge build process...")
    
    # Create dist directory
    ensure_dir(DIST_DIR)
    
    # Build assets
    css_path = build_css()
    js_path = build_js()
    
    # Generate manifest with hashes
    manifest = generate_manifest()
    
    print(f"\n✅ Build complete! Generated {len(manifest)} hashed assets")
    print(f"   📁 Assets in: {DIST_DIR.absolute()}")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        if success:
            print("\n🎉 Build successful!")
        else:
            print("\n❌ Build failed!")
            exit(1)
    except Exception as e:
        print(f"\n💥 Build error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)