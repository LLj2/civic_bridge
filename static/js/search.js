/**
 * Search and autocomplete functionality
 * Handles city search, autocomplete, and API interactions
 */

import { autocomplete, lookup } from './api.js';
import { setLocation, setRepresentatives } from './state.js';
import { showNotification, debounce } from './utils.js';
import { displayResults } from './representatives.js';

let selectedComune = '';

/**
 * Setup autocomplete functionality
 */
export function setupAutocomplete() {
  const input = document.getElementById('searchInput');
  const list = document.getElementById('autocompleteList');
  
  if (!input || !list) {
    console.error('Autocomplete elements not found!');
    return;
  }
  
  // Debounced autocomplete function
  const debouncedAutocomplete = debounce(fetchAutocomplete, 300);
  
  // Input event listener
  input.addEventListener('input', function() {
    const query = this.value.trim();
    
    if (query.length < 2) {
      hideAutocomplete();
      return;
    }
    
    debouncedAutocomplete(query);
  });
  
  // Hide on blur (with delay for clicks)
  input.addEventListener('blur', function() {
    setTimeout(() => hideAutocomplete(), 200);
  });
  
  // Show on focus if value exists
  input.addEventListener('focus', function() {
    if (this.value.length >= 2) {
      debouncedAutocomplete(this.value.trim());
    }
  });
  
  // Enter key to search
  input.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
      hideAutocomplete();
      searchRepresentatives();
    }
  });
}

/**
 * Fetch autocomplete results
 * @param {string} query - Search query
 */
async function fetchAutocomplete(query) {
  try {
    const data = await autocomplete(query);
    
    if (data.success && data.results.length > 0) {
      showAutocompleteResults(data.results);
    } else {
      hideAutocomplete();
    }
  } catch (error) {
    console.error('Autocomplete error:', error);
    hideAutocomplete();
  }
}

/**
 * Show autocomplete results
 * @param {Array} results - Autocomplete results
 */
function showAutocompleteResults(results) {
  const list = document.getElementById('autocompleteList');
  list.innerHTML = '';
  
  results.forEach(result => {
    const item = document.createElement('div');
    item.className = 'autocomplete-item';
    item.textContent = result.display;
    
    // Use event listener instead of onclick
    item.addEventListener('click', function() {
      document.getElementById('searchInput').value = result.comune;
      selectedComune = result.comune;
      hideAutocomplete();
      searchRepresentatives();
    });
    
    list.appendChild(item);
  });
  
  list.style.display = 'block';
}

/**
 * Hide autocomplete dropdown
 */
function hideAutocomplete() {
  const list = document.getElementById('autocompleteList');
  if (list) {
    list.style.display = 'none';
  }
}

/**
 * Search for representatives
 */
export async function searchRepresentatives() {
  const query = document.getElementById('searchInput').value.trim();
  
  if (!query) {
    showNotification('Inserisci il nome di un comune', 'error');
    return;
  }
  
  const resultsDiv = document.getElementById('results');
  const contentDiv = document.getElementById('resultsContent');
  
  resultsDiv.style.display = 'block';
  contentDiv.innerHTML = '<div class="loading">Ricerca in corso...</div>';
  
  try {
    const data = await lookup(query);
    
    if (data.success) {
      // Update global state
      setRepresentatives(data.representatives);
      setLocation(data.location);
      
      // Display results
      displayResults(data);
    } else {
      contentDiv.innerHTML = `<div class="error">Errore: ${data.error}</div>`;
    }
  } catch (error) {
    console.error('Search error:', error);
    contentDiv.innerHTML = `<div class="error">Errore di connessione: ${error.message}</div>`;
  }
}