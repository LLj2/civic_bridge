// js/state.js

/**
 * Centralized state management for Civic Bridge
 * Single source of truth for application data
 */

// Application state
let currentRepresentatives = null;
let currentLocation = null;
let currentThemes = [];
let selectedRep = null;
let selectedInstitution = null;

/**
 * Update representatives data
 * @param {Object} reps - Representatives data from API
 */
window.setRepresentatives = function(reps) {
  currentRepresentatives = reps;
}

/**
 * Get current representatives data
 * @returns {Object|null} Current representatives
 */
window.getRepresentatives = function() {
  return currentRepresentatives;
}

/**
 * Update location data
 * @param {Object} location - Location data from API
 */
window.setLocation = function(location) {
  currentLocation = location;
}

/**
 * Get current location data
 * @returns {Object|null} Current location
 */
window.getLocation = function() {
  return currentLocation;
}

/**
 * Update themes data
 * @param {Array} themes - Available themes
 */
window.setThemes = function(themes) {
  currentThemes = themes;
}

/**
 * Get available themes
 * @returns {Array} Available themes
 */
window.getThemes = function() {
  return currentThemes;
}

/**
 * Set selected representative for composer
 * @param {Object} rep - Selected representative
 * @param {string} institution - Institution type ('camera', 'senato', 'eu')
 */
window.setSelectedRep = function(rep, institution) {
  selectedRep = rep;
  selectedInstitution = institution;
}

/**
 * Get selected representative
 * @returns {Object|null} Selected representative
 */
window.getSelectedRep = function() {
  return selectedRep;
}

/**
 * Get selected institution
 * @returns {string|null} Selected institution
 */
window.getSelectedInstitution = function() {
  return selectedInstitution;
}

/**
 * Clear selected representative
 */
window.clearSelectedRep = function() {
  selectedRep = null;
  selectedInstitution = null;
}

// js/search.js

/**
 * Search and autocomplete functionality
 * Handles city search, autocomplete, and API interactions
 */


let selectedComune = '';

/**
 * Setup autocomplete functionality
 */
window.setupAutocomplete = function() {
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
  
  list.classList.add('is-visible');
}

/**
 * Hide autocomplete dropdown
 */
function hideAutocomplete() {
  const list = document.getElementById('autocompleteList');
  if (list) {
    list.classList.remove('is-visible');
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

// js/composer.js

/**
 * Message composer modal functionality
 * Handles the modal, form validation, and message sending
 */


/**
 * Open composer modal
 * @param {number} repIndex - Representative index
 * @param {string} institution - Institution type ('camera', 'senato', 'eu')
 */
window.openComposer = function(repIndex, institution) {
  const representatives = getRepresentatives();
  
  // Map institution keys for data access
  const institutionMap = { 
    camera: 'camera', 
    senato: 'senato', 
    eu: 'eu_parliament' 
  };
  const listKey = institutionMap[institution] || institution;
  
  // Get representative
  const rep = (representatives && representatives[listKey]) 
    ? representatives[listKey][repIndex] 
    : null;
  
  if (!rep) {
    console.error('Representative not found for', institution, repIndex);
    showNotification('Impossibile aprire il compositore: rappresentante non trovato.', 'error');
    return;
  }
  
  // Store in global state
  setSelectedRep(rep, institution);
  
  // Update modal header
  updateModalHeader(rep, institution);
  
  // Setup form
  populateThemeDropdown();
  resetForm();
  
  // Show modal
  const modal = document.getElementById('composerModal');
  modal.classList.add('show');
  
  // Focus first field
  document.getElementById('themeSelect').focus();
}

/**
 * Close composer modal
 */
window.closeComposer = function() {
  const modal = document.getElementById('composerModal');
  modal.classList.remove('show');
  
  clearSelectedRep();
  resetForm();
}

/**
 * Update modal header with representative info
 * @param {Object} rep - Representative data
 * @param {string} institution - Institution type
 */
function updateModalHeader(rep, institution) {
  const roleMap = { 
    camera: 'Deputato', 
    senato: 'Senatore', 
    eu: 'MEP' 
  };
  
  const role = roleMap[institution];
  const partyCode = getPartyCode(rep.gruppo_partito);
  
  document.getElementById('composerTitle').textContent = 
    `Scrivi a ${role} ${rep.nome} ${rep.cognome}`;
  
  let locationInfo = '';
  if (institution === 'camera') {
    locationInfo = `Collegio: ${rep.collegio}`;
  } else if (institution === 'senato') {
    locationInfo = `Regione: ${rep.regione}`;
  } else {
    locationInfo = `Circoscrizione: ${rep.circoscrizione_eu}`;
  }
  
  document.getElementById('composerSubtitle').textContent = 
    `${locationInfo} · Partito: ${partyCode}`;
}

/**
 * Populate theme dropdown
 */
function populateThemeDropdown() {
  const selectElement = document.getElementById('themeSelect');
  populateThemes(selectElement);
}

/**
 * Handle theme selection change
 */
window.onThemeChange = function() {
  const themeId = document.getElementById('themeSelect').value;
  
  if (!themeId) {
    clearMessageFields();
    return;
  }
  
  const template = getTemplate(themeId);
  if (!template) {
    clearMessageFields();
    return;
  }
  
  // Replace tokens and populate fields
  const subject = replaceTokens(template.subject);
  const body = replaceTokens(template.body);
  
  document.getElementById('subjectInput').value = subject;
  document.getElementById('bodyTextarea').value = body;
  
  validateForm();
}

/**
 * Clear message fields
 */
function clearMessageFields() {
  document.getElementById('subjectInput').value = '';
  document.getElementById('bodyTextarea').value = '';
  validateForm();
}

/**
 * Reset entire form
 */
function resetForm() {
  document.getElementById('themeSelect').value = '';
  document.getElementById('subjectInput').value = '';
  document.getElementById('bodyTextarea').value = '';
  document.getElementById('personalLine').value = '';
  document.getElementById('sendMailto').checked = true;
  updateCharCounter();
  validateForm();
}

/**
 * Update character counter for personal line
 */
function updateCharCounter() {
  const textarea = document.getElementById('personalLine');
  const counter = document.getElementById('personalCounter');
  const length = textarea.value.length;
  const maxLength = 300;
  
  counter.textContent = `${length} / ${maxLength} caratteri`;
  
  if (length > maxLength * 0.9) {
    counter.className = 'char-counter warning';
  } else if (length > maxLength) {
    counter.className = 'char-counter error';
  } else {
    counter.className = 'char-counter';
  }
}

/**
 * Validate form and enable/disable send button
 */
function validateForm() {
  const theme = document.getElementById('themeSelect').value;
  const subject = document.getElementById('subjectInput').value.trim();
  const personalLine = document.getElementById('personalLine').value.trim();
  const sendButton = document.getElementById('sendButton');
  
  const isValid = theme && subject && personalLine.length >= 20;
  sendButton.disabled = !isValid;
  
  sendButton.textContent = isValid ? 'Invia' : 'Compila tutti i campi';
}

/**
 * Send message
 */
window.sendMessage = function() {
  const sendMethod = document.querySelector('input[name="sendMethod"]:checked').value;
  const subject = document.getElementById('subjectInput').value;
  const body = document.getElementById('bodyTextarea').value;
  const personalLine = document.getElementById('personalLine').value;
  
  // Replace [RIGA PERSONALE OBBLIGATORIA] with actual personal content
  const finalBody = body.replace(/\\[RIGA PERSONALE OBBLIGATORIA[^\\]]*\\]/g, personalLine);
  
  if (sendMethod === 'mailto') {
    openMailClient(subject, finalBody);
  } else {
    sendViaOAuth(subject, finalBody);
  }
}

/**
 * Open mail client
 * @param {string} subject - Email subject
 * @param {string} body - Email body
 */
function openMailClient(subject, body) {
  const selectedRep = getSelectedRep();
  
  if (!selectedRep || !selectedRep.email || selectedRep.email === 'Non disponibile') {
    showNotification('Email non disponibile per questo rappresentante.', 'error');
    return;
  }
  
  const mailto = `mailto:${encodeURIComponent(selectedRep.email)}` +
    `?subject=${encodeURIComponent(subject)}` +
    `&body=${encodeURIComponent(body)}`;
  
  try {
    window.open(mailto, '_blank');
    showSuccessMessage();
  } catch (error) {
    console.error('Failed to open mail client:', error);
    showCopyFallback(subject, body);
  }
}

/**
 * Send via OAuth (placeholder)
 * @param {string} subject - Email subject
 * @param {string} body - Email body
 */
function sendViaOAuth(subject, body) {
  // TODO: Implement actual OAuth sending
  showNotification('OAuth implementation coming soon', 'info');
  showSuccessMessage();
}

/**
 * Show success message and close modal
 */
function showSuccessMessage() {
  const selectedRep = getSelectedRep();
  closeComposer();
  showNotification(`Email preparata per ${selectedRep.nome} ${selectedRep.cognome}`, 'success');
}

/**
 * Show copy fallback when email client fails
 * @param {string} subject - Email subject
 * @param {string} body - Email body
 */
function showCopyFallback(subject, body) {
  const text = `Oggetto: ${subject}\\n\\n${body}`;
  
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text);
    showNotification('Testo copiato negli appunti', 'success');
  } else {
    alert(`Impossibile aprire client email. Copia manualmente:\\n\\n${text}`);
  }
  
  closeComposer();
}

/**
 * Setup composer modal event listeners
 */
window.setupComposerListeners = function() {
  // Theme selection change
  document.getElementById('themeSelect').addEventListener('change', onThemeChange);
  
  // Personal line character counter and validation
  const personalLine = document.getElementById('personalLine');
  personalLine.addEventListener('input', function() {
    updateCharCounter();
    validateForm();
  });
  
  // Form validation on all inputs
  const formFields = ['themeSelect', 'subjectInput', 'personalLine'];
  formFields.forEach(id => {
    const element = document.getElementById(id);
    element.addEventListener('change', validateForm);
    element.addEventListener('input', validateForm);
  });
  
  // Close button
  document.getElementById('closeComposerBtn').addEventListener('click', closeComposer);
  
  // Send button
  document.getElementById('sendButton').addEventListener('click', sendMessage);
  
  // Close modal when clicking outside
  document.getElementById('composerModal').addEventListener('click', function(e) {
    if (e.target === this) {
      closeComposer();
    }
  });
  
  // Escape key to close
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      const modal = document.getElementById('composerModal');
      if (modal.classList.contains('show')) {
        closeComposer();
      }
    }
  });
}

// js/main.js

/**
 * Main application entry point
 * Initializes all modules and sets up the application
 */


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