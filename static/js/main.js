/**
 * Main application entry point
 * Initializes all modules and sets up the application
 */

import { setupAutocomplete, searchRepresentatives } from './search.js';
import { setupComposerListeners } from './composer.js';
import { loadThemes } from './api.js';
import { setThemes } from './state.js';
import { showNotification } from './utils.js';

/**
 * Initialize the application
 */
async function initApp() {
  console.log('🚀 Initializing Civic Bridge...');
  
  try {
    // Load themes from server
    await loadThemesData();
    
    // Setup autocomplete functionality
    setupAutocomplete();
    
    // Setup search button
    setupSearchButton();
    
    // Setup composer modal listeners
    setupComposerListeners();
    
    console.log('✅ Civic Bridge initialized successfully');
    
  } catch (error) {
    console.error('❌ Failed to initialize Civic Bridge:', error);
    showNotification('Errore durante l\'inizializzazione dell\'applicazione', 'error');
  }
}

/**
 * Load themes data from server
 */
async function loadThemesData() {
  try {
    const data = await loadThemes();
    setThemes(data.themes || []);
    console.log('📋 Themes loaded:', data.themes?.length || 0);
  } catch (error) {
    console.warn('⚠️ Failed to load themes, using fallback');
    // Fallback themes
    setThemes([
      {
        id: 'corridoio_umanitario',
        title: 'Corridoio umanitario',
        templates: {
          camera: { 
            subject: 'Corridoio umanitario Gaza', 
            body: 'Template di emergenza...' 
          }
        }
      }
    ]);
  }
}

/**
 * Setup search button event listener
 */
function setupSearchButton() {
  const searchButton = document.getElementById('searchButton');
  if (searchButton) {
    searchButton.addEventListener('click', searchRepresentatives);
  }
}

/**
 * Initialize when DOM is ready
 */
document.addEventListener('DOMContentLoaded', initApp);