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

// New identity state
let composerState = {
  identity: 'cittadino', // 'elettore' | 'cittadino'
  themeId: null,
  selectedTopicIds: [],
  subject: '',
  body: '',
  userCity: '',
  subjectEdited: false,
  introEdited: false
};

/**
 * Initialize composer
 */
export async function initComposer() {
  await loadThemesConfig();
  setupComposerListeners();
}

/**
 * Check if user is an elector for the given representative
 * @param {string} userComuneIstat - User's comune ISTAT code
 * @param {Object} rep - Representative data
 * @param {string} institution - Institution type
 * @returns {boolean} True if user is an elector
 */
function isElector(userComuneIstat, rep, institution) {
  if (!userComuneIstat || !rep) return false;
  
  const location = getLocation();
  if (!location) return false;
  
  switch (institution) {
    case 'camera':
      // For Camera, check if user's collegio matches representative's collegio
      // This requires mapping comune to collegio, which is complex
      // For now, simplified check based on region matching
      return checkCameraConstituency(location, rep);
      
    case 'senato':
      // For Senato, check if user's regione matches representative's regione
      return location.regione === rep.regione;
      
    case 'eu':
      // For EU Parliament, check if user's regione is in MEP's constituency
      return checkEUConstituency(location.regione, rep.circoscrizione_eu);
      
    default:
      return false;
  }
}

/**
 * Check Camera constituency (simplified region-based check)
 * @param {Object} location - User location
 * @param {Object} rep - Representative data
 * @returns {boolean} True if in same constituency
 */
function checkCameraConstituency(location, rep) {
  if (!location.regione || !rep.collegio) return false;
  
  // Extract region from collegio string (e.g., "LAZIO 1 - P01" -> "LAZIO")
  const repRegion = rep.collegio.split(/[\s-]/)[0].toUpperCase();
  const userRegion = location.regione.toUpperCase();
  
  return repRegion === userRegion;
}

/**
 * Check EU constituency mapping
 * @param {string} userRegione - User's region
 * @param {string} repConstituency - Representative's EU constituency
 * @returns {boolean} True if user's region is in MEP's constituency
 */
function checkEUConstituency(userRegione, repConstituency) {
  if (!userRegione || !repConstituency) return false;
  
  // EU constituency mapping
  const euConstituencies = {
    'Nord-occidentale': ['Piemonte', 'Valle d\'Aosta', 'Lombardia', 'Liguria'],
    'Nord-orientale': ['Veneto', 'Trentino-Alto Adige', 'Friuli-Venezia Giulia', 'Emilia-Romagna'],
    'Centrale': ['Toscana', 'Umbria', 'Marche', 'Lazio'],
    'Meridionale': ['Abruzzo', 'Molise', 'Campania', 'Puglia', 'Basilicata', 'Calabria'],
    'Insulare': ['Sicilia', 'Sardegna']
  };
  
  const regions = euConstituencies[repConstituency] || [];
  return regions.includes(userRegione);
}

/**
 * Initialize composer state when opening modal
 * @param {Object} rep - Representative data
 * @param {string} institution - Institution type
 */
function initializeComposerState(rep, institution) {
  const location = getLocation();
  const userIsElector = location ? isElector(location.istat_comune, rep, institution) : false;
  
  composerState = {
    identity: userIsElector ? 'elettore' : 'cittadino',
    themeId: null,
    selectedTopicIds: [],
    subject: '',
    body: '',
    userCity: location?.comune || '',
    subjectEdited: false,
    introEdited: false
  };
  
  // Update identity UI
  updateIdentityUI(userIsElector);
}

/**
 * Update identity selection UI
 * @param {boolean} userIsElector - Whether user is an elector
 */
function updateIdentityUI(userIsElector) {
  const elettoreRadio = document.getElementById('identityElettore');
  const cittadinoRadio = document.getElementById('identityCittadino');
  
  if (!elettoreRadio || !cittadinoRadio) return;
  
  // Enable/disable elettore option
  elettoreRadio.disabled = !userIsElector;
  
  // Set default selection
  if (userIsElector) {
    elettoreRadio.checked = true;
    cittadinoRadio.checked = false;
  } else {
    elettoreRadio.checked = false;
    cittadinoRadio.checked = true;
  }
  
  // Update tooltip visibility
  const tooltip = document.getElementById('elettoreTooltip');
  if (tooltip) {
    tooltip.style.display = userIsElector ? 'none' : 'inline';
  }
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
  
  // Initialize composer state
  initializeComposerState(rep, institution);
  
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
 * Build subject line based on identity and theme
 * @param {string} identity - 'elettore' or 'cittadino'
 * @param {string} cityName - User's city name
 * @param {string} themeTitle - Theme title
 * @returns {string} Subject line
 */
function buildSubject(identity, cityName, themeTitle) {
  const who = identity === 'elettore' ? 'un suo elettore' : 'un cittadino';
  return `Richiesta da ${who} di ${cityName}: ${themeTitle}`;
}

/**
 * Build message introduction based on identity
 * @param {string} identity - 'elettore' or 'cittadino'
 * @param {string} lastName - Representative's last name
 * @param {string} cityName - User's city name
 * @param {string} themeTitle - Theme title
 * @param {string} institution - Institution type
 * @returns {string} Message introduction
 */
function buildIntro(identity, lastName, cityName, themeTitle, institution) {
  const who = identity === 'elettore' ? 'suo elettore' : 'cittadino';
  
  // Build salutation
  const titleMap = {
    camera: 'Onorevole',
    senato: 'Onorevole',
    eu: 'Onorevole'
  };
  const title = titleMap[institution] || 'Onorevole';
  
  return `Gentile ${title} ${lastName},\n\nLe scrivo come ${who} residente a ${cityName} in merito a ${themeTitle}.`;
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
  
  // Update composer state
  composerState.themeId = theme ? Object.keys(themesConfig).find(key => themesConfig[key] === theme) : null;
  
  // Update subject
  const subject = buildSubject(composerState.identity, cityName, theme.title);
  const subjectInput = document.getElementById('subjectInput');
  if (subjectInput && !composerState.subjectEdited) {
    subjectInput.value = subject;
    composerState.subject = subject;
  }
  
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
  const bodyTextarea = document.getElementById('bodyTextarea');
  
  if (!theme || !rep || !bodyTextarea) return;
  
  const cityName = location?.comune || 'Roma';
  const lastName = rep.cognome;
  
  // Build message intro
  const intro = buildIntro(composerState.identity, lastName, cityName, theme.title, institution);
  
  // Add topics if selected
  const selectedTopics = getSelectedTopics();
  let topicsSection = '';
  if (selectedTopics.length > 0) {
    topicsSection = '\n\nPunti principali:\n';
    selectedTopics.forEach(topic => {
      topicsSection += `• ${topic}\n`;
    });
  }
  
  const signature = '\n\nCordiali saluti,\n[Nome e cognome]';
  const fullBody = intro + topicsSection + signature;
  
  // Only update if user hasn't manually edited the introduction
  if (!composerState.introEdited) {
    bodyTextarea.value = fullBody;
    composerState.body = fullBody;
  }
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
  
  // Reset composer state tracking flags
  composerState.themeId = null;
  composerState.selectedTopicIds = [];
  composerState.subject = '';
  composerState.body = '';
  composerState.subjectEdited = false;
  composerState.introEdited = false;
  
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
 * Handle identity change
 */
function onIdentityChange() {
  const elettoreRadio = document.getElementById('identityElettore');
  const newIdentity = elettoreRadio?.checked ? 'elettore' : 'cittadino';
  
  // Check if user has manually edited content
  const shouldConfirm = (composerState.subjectEdited || composerState.introEdited) && 
                       composerState.themeId && 
                       newIdentity !== composerState.identity;
  
  if (shouldConfirm) {
    const confirmed = confirm('Vuoi aggiornare oggetto e introduzione in base alla tua scelta?');
    if (!confirmed) {
      // Reset radio button to previous state
      const currentRadio = document.getElementById(
        composerState.identity === 'elettore' ? 'identityElettore' : 'identityCittadino'
      );
      if (currentRadio) currentRadio.checked = true;
      return;
    }
    
    // Reset edit tracking flags
    composerState.subjectEdited = false;
    composerState.introEdited = false;
  }
  
  // Update state
  composerState.identity = newIdentity;
  
  // Update form if theme is selected
  if (composerState.themeId) {
    const theme = themesConfig[composerState.themeId];
    if (theme) {
      updateMessageFields(theme);
    }
  }
}

/**
 * Setup composer modal event listeners
 */
export function setupComposerListeners() {
  // Identity selection change
  const identityRadios = document.querySelectorAll('input[name="senderIdentity"]');
  identityRadios.forEach(radio => {
    radio.addEventListener('change', onIdentityChange);
  });
  
  // Theme selection change
  const themeSelect = document.getElementById('themeSelect');
  if (themeSelect) {
    themeSelect.addEventListener('change', onThemeChange);
  }
  
  // Subject field validation and edit tracking
  const subjectInput = document.getElementById('subjectInput');
  if (subjectInput) {
    subjectInput.addEventListener('input', () => {
      hideFieldError('subjectInput');
      validateForm();
      
      // Track manual editing
      if (subjectInput.value !== composerState.subject) {
        composerState.subjectEdited = true;
      }
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
  
  // Body field edit tracking
  const bodyTextarea = document.getElementById('bodyTextarea');
  if (bodyTextarea) {
    bodyTextarea.addEventListener('input', () => {
      // Track manual editing of intro section
      if (bodyTextarea.value !== composerState.body) {
        composerState.introEdited = true;
      }
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