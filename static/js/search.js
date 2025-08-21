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
  const input = document.getElementById('searchInput');
  
  list.innerHTML = '';
  
  results.forEach((result, index) => {
    const item = document.createElement('div');
    item.className = 'autocomplete-item';
    item.textContent = result.display;
    item.role = 'option';
    item.id = `autocomplete-item-${index}`;
    item.setAttribute('aria-selected', 'false');
    
    // Use event listener instead of onclick
    item.addEventListener('click', function() {
      input.value = result.comune;
      selectedComune = result.comune;
      hideAutocomplete();
      searchRepresentatives();
    });
    
    list.appendChild(item);
  });
  
  list.classList.add('is-visible');
  
  // Update ARIA attributes
  input.setAttribute('aria-expanded', 'true');
  if (results.length > 0) {
    input.setAttribute('aria-activedescendant', 'autocomplete-item-0');
  }
}

/**
 * Hide autocomplete dropdown
 */
function hideAutocomplete() {
  const list = document.getElementById('autocompleteList');
  const input = document.getElementById('searchInput');
  
  if (list) {
    list.classList.remove('is-visible');
  }
  
  if (input) {
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
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
  
  resultsDiv.classList.remove('is-hidden');
  contentDiv.innerHTML = '<div class="loading">Ricerca in corso...</div>';
  
  try {
    const data = await lookup(query);
    
    if (data.success) {
      // Check if no representatives found
      if (!data.representatives || Object.keys(data.representatives).length === 0) {
        displayNoResultsState(query, data.location);
        return;
      }
      
      // Update global state
      setRepresentatives(data.representatives);
      setLocation(data.location);
      
      // Display results
      displayResults(data);
      
      // Auto-scroll to results and focus first tab
      scrollToResults();
    } else {
      displayErrorState(data.error || 'Errore sconosciuto', query);
    }
  } catch (error) {
    console.error('Search error:', error);
    displayNetworkErrorState(error.message, query);
  }
}

/**
 * Display no results state
 * @param {string} query - Search query
 * @param {Object} location - Location data
 */
function displayNoResultsState(query, location) {
  const contentDiv = document.getElementById('resultsContent');
  contentDiv.innerHTML = `
    <div class="error-state">
      <div class="error-state-content">
        <div class="error-state-icon">📭</div>
        <div class="error-state-title">Nessun rappresentante trovato</div>
        <div class="error-state-message">
          Non sono stati trovati rappresentanti per <strong>${query}</strong>.
          ${location ? `<br>Verifica che il comune sia corretto.` : ''}
        </div>
        <button class="btn-secondary retry-btn" onclick="document.getElementById('searchInput').focus()">
          Prova un altro comune
        </button>
      </div>
    </div>
  `;
}

/**
 * Display error state
 * @param {string} errorMessage - Error message
 * @param {string} query - Search query
 */
function displayErrorState(errorMessage, query) {
  const contentDiv = document.getElementById('resultsContent');
  contentDiv.innerHTML = `
    <div class="error-state">
      <div class="error-state-content">
        <div class="error-state-icon">⚠️</div>
        <div class="error-state-title">Errore nella ricerca</div>
        <div class="error-state-message">${errorMessage}</div>
        <button class="btn-primary retry-btn" onclick="searchRepresentatives()">
          Riprova
        </button>
      </div>
    </div>
  `;
}

/**
 * Display network error state
 * @param {string} errorMessage - Error message  
 * @param {string} query - Search query
 */
function displayNetworkErrorState(errorMessage, query) {
  const contentDiv = document.getElementById('resultsContent');
  contentDiv.innerHTML = `
    <div class="error-state">
      <div class="error-state-content">
        <div class="error-state-icon">🔌</div>
        <div class="error-state-title">Impossibile caricare i rappresentanti</div>
        <div class="error-state-message">
          Verifica la connessione internet e riprova.
          <br><small>Dettaglio errore: ${errorMessage}</small>
        </div>
        <button class="btn-primary retry-btn" onclick="searchRepresentatives()">
          Riprova
        </button>
      </div>
    </div>
  `;
}

/**
 * Scroll to results section and focus first tab for accessibility
 */
function scrollToResults() {
  const resultsDiv = document.getElementById('results');
  const firstTab = document.querySelector('.tab-btn');
  
  if (resultsDiv) {
    // Smooth scroll to results
    resultsDiv.scrollIntoView({ 
      behavior: 'smooth', 
      block: 'start' 
    });
    
    // Focus first tab after a short delay
    if (firstTab) {
      setTimeout(() => {
        firstTab.focus();
      }, 500);
    }
  }
}