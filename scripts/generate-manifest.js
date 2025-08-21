#!/usr/bin/env node
/**
 * Generate asset manifest with hashes for cache busting
 */

import fs from 'fs';
import crypto from 'crypto';
import path from 'path';

const distDir = 'dist';
const manifestPath = path.join(distDir, 'manifest.json');

function getFileHash(filePath) {
    const fileBuffer = fs.readFileSync(filePath);
    const hashSum = crypto.createHash('sha256');
    hashSum.update(fileBuffer);
    return hashSum.digest('hex').substring(0, 8);
}

function generateManifest() {
    const manifest = {};
    
    // Check for built assets
    const assets = ['app.min.css', 'app.min.js'];
    
    for (const asset of assets) {
        const assetPath = path.join(distDir, asset);
        
        if (fs.existsSync(assetPath)) {
            const hash = getFileHash(assetPath);
            const [name, ext] = asset.split('.');
            const hashedName = `${name}.${hash}.${ext}`;
            
            // Copy to hashed filename
            const hashedPath = path.join(distDir, hashedName);
            fs.copyFileSync(assetPath, hashedPath);
            
            // Add to manifest
            manifest[asset] = hashedName;
        }
    }
    
    // Write manifest
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
    console.log('✓ Generated asset manifest:', manifest);
    
    return manifest;
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
    try {
        generateManifest();
    } catch (error) {
        console.error('Error generating manifest:', error);
        process.exit(1);
    }
}

export { generateManifest };