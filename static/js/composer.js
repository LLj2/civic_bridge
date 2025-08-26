/**
 * Message composer modal functionality
 * Handles the modal, form validation, and message sending
 */

import { getRepresentatives, setSelectedRep, getSelectedRep, getSelectedInstitution, clearSelectedRep, getLocation } from './state.js';
import { getPartyCode, showNotification } from './utils.js';
import { loadThemes } from './api.js';

// Composer state
let themesConfig = null;
let currentTopics = [];
let oauthAvailable = false;

/**
 * Initialize composer
 */
export async function initComposer() {
  await loadThemesConfig();
  setupComposerListeners();
}

/**
 * Load themes configuration
 */
async function loadThemesConfig() {
  try {
    const response = await loadThemes();
    if (response.success) {
      themesConfig = response.themes;
      console.log(`✅ Loaded ${Object.keys(themesConfig).length} themes`);
    }
  } catch (error) {
    console.error('Failed to load themes:', error);
    // Fallback to default theme
    themesConfig = {
      altro: {
        title: 'Altro argomento',
        topics: []
      }
    };
  }
}

/**
 * Open composer modal
 * @param {number} repIndex - Representative index
 * @param {string} institution - Institution type ('camera', 'senato', 'eu')
 */
export function openComposer(repIndex, institution) {
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
  
  // Show/hide OAuth button based on availability
  const oauthBtn = document.getElementById('sendOAuthBtn');
  if (oauthBtn) {
    oauthBtn.style.display = oauthAvailable ? 'inline-block' : 'none';
  }
  
  // Show modal
  const modal = document.getElementById('composerModal');
  modal.classList.add('show');
  
  // Focus first field
  setTimeout(() => {
    document.getElementById('themeSelect').focus();
  }, 100);
}

/**
 * Close composer modal
 */
export function closeComposer() {
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
    eu: 'Europarlamentare' 
  };
  
  const role = roleMap[institution];
  const partyCode = getPartyCode(rep.gruppo_partito);
  
  // Update title (normal case for names)
  const fullName = `${rep.nome} ${rep.cognome}`;
  document.getElementById('composerTitle').textContent = 
    `Scrivi a ${role} ${fullName}`;
  
  // Update subtitle elements
  document.getElementById('repParty').textContent = partyCode;
  
  let locationText = '';
  if (institution === 'camera') {
    locationText = rep.collegio || 'Non disponibile';
  } else if (institution === 'senato') {
    locationText = rep.regione || 'Non disponibile';
  } else {
    locationText = rep.circoscrizione_eu || 'Non disponibile';
  }
  document.getElementById('repLocation').textContent = locationText;
  
  const emailText = rep.email && rep.email !== 'Non disponibile' 
    ? rep.email 
    : 'Nessuna email disponibile';
  document.getElementById('repEmail').textContent = emailText;
  
  // Disable send buttons if no email
  const hasEmail = rep.email && rep.email !== 'Non disponibile';
  updateSendButtonsState(hasEmail);
}

/**
 * Update send buttons state based on email availability
 * @param {boolean} hasEmail - Whether representative has email
 */
function updateSendButtonsState(hasEmail) {
  const openEmailBtn = document.getElementById('openEmailBtn');
  const sendOAuthBtn = document.getElementById('sendOAuthBtn');
  
  if (!hasEmail) {
    openEmailBtn.disabled = true;
    openEmailBtn.textContent = 'Email non disponibile';
    if (sendOAuthBtn) {
      sendOAuthBtn.disabled = true;
    }
  } else {
    openEmailBtn.disabled = false;
    openEmailBtn.textContent = 'Apri email';
    if (sendOAuthBtn) {
      sendOAuthBtn.disabled = false;
    }
  }
}

/**
 * Populate theme dropdown
 */
function populateThemeDropdown() {
  const selectElement = document.getElementById('themeSelect');
  selectElement.innerHTML = '<option value="">Seleziona un tema...</option>';
  
  if (themesConfig) {
    // Sort themes by order property
    const sortedThemes = Object.entries(themesConfig)
      .sort((a, b) => (a[1].order || 999) - (b[1].order || 999));
    
    sortedThemes.forEach(([themeId, theme]) => {
      const option = document.createElement('option');
      option.value = themeId;
      option.textContent = theme.title;
      selectElement.appendChild(option);
    });
  }
}

/**
 * Handle theme selection change
 */
export function onThemeChange() {
  const themeId = document.getElementById('themeSelect').value;
  const topicsContainer = document.getElementById('topicsContainer');
  const topicsList = document.getElementById('topicsList');
  
  if (!themeId) {
    // Hide topics and clear fields
    topicsContainer.style.display = 'none';
    clearMessageFields();
    return;
  }
  
  const theme = themesConfig[themeId];
  if (!theme) {
    topicsContainer.style.display = 'none';
    clearMessageFields();
    return;
  }
  
  // Show topics if available (hide for "altro")
  if (theme.topics && theme.topics.length > 0) {
    topicsContainer.style.display = 'block';
    
    // Update the label to show which theme the topics belong to
    const topicsLabel = topicsContainer.querySelector('.composer-label');
    if (topicsLabel) {
      topicsLabel.innerHTML = `Argomenti <span class="label-hint">(opzionali per: ${theme.title})</span>`;
    }
    
    populateTopicsList(theme.topics);
  } else {
    topicsContainer.style.display = 'none';
  }
  
  // Update subject and message
  updateMessageFields(theme);
}

/**
 * Populate topics list with checkboxes
 * @param {Array} topics - Topics array
 */
function populateTopicsList(topics) {
  const topicsList = document.getElementById('topicsList');
  topicsList.innerHTML = '';
  
  currentTopics = topics;
  
  topics.forEach((topic, index) => {
    const topicItem = document.createElement('div');
    topicItem.className = 'topic-item';
    
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = `topic_${topic.id}`;
    checkbox.value = topic.id;
    checkbox.addEventListener('change', onTopicToggle);
    
    const label = document.createElement('label');
    label.htmlFor = `topic_${topic.id}`;
    label.textContent = topic.label;
    
    topicItem.appendChild(checkbox);
    topicItem.appendChild(label);
    topicsList.appendChild(topicItem);
  });
}

/**
 * Handle topic checkbox toggle
 */
function onTopicToggle() {
  updateMessageBody();
}

/**
 * Get selected topics
 * @returns {Array} Selected topic labels
 */
function getSelectedTopics() {
  const selectedTopics = [];
  currentTopics.forEach(topic => {
    const checkbox = document.getElementById(`topic_${topic.id}`);
    if (checkbox && checkbox.checked) {
      selectedTopics.push(topic.label);
    }
  });
  return selectedTopics;
}

/**
 * Update message fields based on theme
 * @param {Object} theme - Theme object
 */
function updateMessageFields(theme) {
  const location = getLocation();
  const rep = getSelectedRep();
  const institution = getSelectedInstitution();
  
  // Get location name
  const cityName = location?.comune || 'Roma';
  
  // Update subject
  const subject = `Richiesta da un suo elettore di ${cityName}: ${theme.title}`;
  document.getElementById('subjectInput').value = subject;
  
  // Update body
  updateMessageBody();
  
  validateForm();
}

/**
 * Update message body with current settings
 */
function updateMessageBody() {
  const themeSelect = document.getElementById('themeSelect');
  const theme = themesConfig[themeSelect.value];
  const rep = getSelectedRep();
  const location = getLocation();
  const institution = getSelectedInstitution();
  
  if (!theme || !rep) return;
  
  const cityName = location?.comune || 'Roma';
  const lastName = rep.cognome;
  
  // Build salutation (normal case)
  const titleMap = {
    camera: 'Onorevole',
    senato: 'Onorevole',
    eu: 'Onorevole'
  };
  const title = titleMap[institution] || 'Onorevole';
  
  // Build message body
  let body = `Gentile ${title} ${lastName},\n\n`;
  body += `Le scrivo come cittadino residente a ${cityName} in merito a ${theme.title}.`;
  
  // Add topics if selected
  const selectedTopics = getSelectedTopics();
  if (selectedTopics.length > 0) {
    body += '\n\nPunti principali:\n';
    selectedTopics.forEach(topic => {
      body += `• ${topic}\n`;
    });
  }
  
  body += '\n\nCordiali saluti,\n[Nome e cognome]';
  
  document.getElementById('bodyTextarea').value = body;
}

/**
 * Clear message fields
 */
function clearMessageFields() {
  document.getElementById('subjectInput').value = '';
  document.getElementById('bodyTextarea').value = '';
  document.getElementById('topicsList').innerHTML = '';
  currentTopics = [];
  validateForm();
}

/**
 * Reset entire form
 */
function resetForm() {
  document.getElementById('themeSelect').value = '';
  document.getElementById('subjectInput').value = '';
  document.getElementById('bodyTextarea').value = '';
  document.getElementById('topicsContainer').style.display = 'none';
  document.getElementById('topicsList').innerHTML = '';
  currentTopics = [];
  attemptedSubmit = false;
  
  // Reset field states
  const subjectInput = document.getElementById('subjectInput');
  if (subjectInput) {
    subjectInput.classList.remove('blurred');
  }
  
  hideFieldError('subjectInput');
  validateForm();
}

// Track if user has attempted to submit
let attemptedSubmit = false;

/**
 * Validate form and update UI state
 */
function validateForm() {
  const theme = document.getElementById('themeSelect').value;
  const subject = document.getElementById('subjectInput').value.trim();
  const openEmailBtn = document.getElementById('openEmailBtn');
  const sendOAuthBtn = document.getElementById('sendOAuthBtn');
  const rep = getSelectedRep();
  
  // Check if rep has email
  const hasEmail = rep && rep.email && rep.email !== 'Non disponibile';
  
  // Subject is required, theme is optional unless it's "altro"
  const isValid = subject && hasEmail;
  
  if (!hasEmail) {
    openEmailBtn.disabled = true;
    openEmailBtn.textContent = 'Email non disponibile';
    if (sendOAuthBtn) sendOAuthBtn.disabled = true;
  } else if (!isValid) {
    openEmailBtn.disabled = true;
    openEmailBtn.textContent = 'Compila i campi richiesti';
    if (sendOAuthBtn) sendOAuthBtn.disabled = true;
  } else {
    openEmailBtn.disabled = false;
    openEmailBtn.textContent = 'Apri email';
    if (sendOAuthBtn) sendOAuthBtn.disabled = false;
  }
}

/**
 * Show field error conditionally
 * @param {string} fieldId - Field ID
 * @param {string} message - Error message
 * @param {boolean} force - Force show error regardless of state
 */
function showFieldError(fieldId, message, force = false) {
  const field = document.getElementById(fieldId);
  const errorElement = document.getElementById(`${fieldId}Error`);
  
  if (!field || !errorElement) return;
  
  // Only show error if attempted submit or force is true
  const shouldShow = force || attemptedSubmit || field.classList.contains('blurred');
  
  if (shouldShow) {
    errorElement.textContent = message;
    errorElement.style.display = 'block';
    field.classList.add('error');
  }
}

/**
 * Hide field error
 * @param {string} fieldId - Field ID
 */
function hideFieldError(fieldId) {
  const errorElement = document.getElementById(`${fieldId}Error`);
  if (errorElement) {
    errorElement.style.display = 'none';
  }
  
  const field = document.getElementById(fieldId);
  if (field) {
    field.classList.remove('error');
  }
}

/**
 * Copy message text to clipboard
 */
export function copyMessageText() {
  const subject = document.getElementById('subjectInput').value;
  const body = document.getElementById('bodyTextarea').value;
  
  const fullText = `Oggetto: ${subject}\n\n${body}`;
  
  if (navigator.clipboard) {
    navigator.clipboard.writeText(fullText)
      .then(() => {
        showNotification('Testo copiato negli appunti', 'success');
        
        // Update button text temporarily
        const copyBtn = document.getElementById('copyTextBtn');
        const originalText = copyBtn.textContent;
        copyBtn.textContent = 'Copiato!';
        setTimeout(() => {
          copyBtn.textContent = originalText;
        }, 2000);
      })
      .catch(err => {
        console.error('Failed to copy text:', err);
        showNotification('Errore nella copia del testo', 'error');
      });
  } else {
    // Fallback for older browsers
    const textarea = document.createElement('textarea');
    textarea.value = fullText;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    
    try {
      document.execCommand('copy');
      showNotification('Testo copiato negli appunti', 'success');
    } catch (err) {
      showNotification('Errore nella copia del testo', 'error');
    }
    
    document.body.removeChild(textarea);
  }
}

/**
 * Open email client
 */
export function openEmailClient() {
  const selectedRep = getSelectedRep();
  const subject = document.getElementById('subjectInput').value.trim();
  const body = document.getElementById('bodyTextarea').value;
  
  // Mark as attempted submit
  attemptedSubmit = true;
  
  // Validate subject
  if (!subject) {
    showFieldError('subjectInput', "L'oggetto è obbligatorio", true);
    document.getElementById('subjectInput').focus();
    return;
  }
  
  hideFieldError('subjectInput');
  
  if (!selectedRep || !selectedRep.email || selectedRep.email === 'Non disponibile') {
    showNotification('Nessun indirizzo email disponibile per questo rappresentante.', 'error');
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
    copyMessageText();
    showNotification('Impossibile aprire il client email. Il testo è stato copiato negli appunti.', 'warning');
  }
}

/**
 * Send via OAuth
 */
export async function sendViaOAuth() {
  const selectedRep = getSelectedRep();
  const subject = document.getElementById('subjectInput').value.trim();
  const body = document.getElementById('bodyTextarea').value;
  
  // Mark as attempted submit
  attemptedSubmit = true;
  
  // Validate subject
  if (!subject) {
    showFieldError('subjectInput', "L'oggetto è obbligatorio", true);
    document.getElementById('subjectInput').focus();
    return;
  }
  
  hideFieldError('subjectInput');
  
  // TODO: Implement actual OAuth sending
  showNotification('Email inviata con successo', 'success');
  closeComposer();
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
 * Setup composer modal event listeners
 */
export function setupComposerListeners() {
  // Theme selection change
  const themeSelect = document.getElementById('themeSelect');
  if (themeSelect) {
    themeSelect.addEventListener('change', onThemeChange);
  }
  
  // Subject field validation
  const subjectInput = document.getElementById('subjectInput');
  if (subjectInput) {
    subjectInput.addEventListener('input', () => {
      hideFieldError('subjectInput');
      validateForm();
    });
    subjectInput.addEventListener('blur', () => {
      subjectInput.classList.add('blurred');
      if (!subjectInput.value.trim()) {
        showFieldError('subjectInput', "L'oggetto è obbligatorio");
      }
    });
    subjectInput.addEventListener('focus', () => {
      hideFieldError('subjectInput');
    });
  }
  
  // Close button
  const closeBtn = document.getElementById('closeComposerBtn');
  if (closeBtn) {
    closeBtn.addEventListener('click', closeComposer);
  }
  
  // Copy text button
  const copyBtn = document.getElementById('copyTextBtn');
  if (copyBtn) {
    copyBtn.addEventListener('click', copyMessageText);
  }
  
  // Open email button
  const openEmailBtn = document.getElementById('openEmailBtn');
  if (openEmailBtn) {
    openEmailBtn.addEventListener('click', openEmailClient);
  }
  
  // Send OAuth button
  const sendOAuthBtn = document.getElementById('sendOAuthBtn');
  if (sendOAuthBtn) {
    sendOAuthBtn.addEventListener('click', sendViaOAuth);
  }
  
  // Close modal when clicking outside
  const modal = document.getElementById('composerModal');
  if (modal) {
    modal.addEventListener('click', function(e) {
      if (e.target === this) {
        closeComposer();
      }
    });
  }
  
  // Escape key to close
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      const modal = document.getElementById('composerModal');
      if (modal && modal.classList.contains('show')) {
        closeComposer();
      }
    }
  });
}