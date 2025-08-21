/**
 * Message composer modal functionality
 * Handles the modal, form validation, and message sending
 */

import { getRepresentatives, setSelectedRep, getSelectedRep, getSelectedInstitution, clearSelectedRep } from './state.js';
import { getPartyCode, showNotification } from './utils.js';
import { replaceTokens, getTemplate, populateThemes } from './themes.js';

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
  
  // Show modal
  const modal = document.getElementById('composerModal');
  modal.classList.add('show');
  
  // Focus first field
  document.getElementById('themeSelect').focus();
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
export function onThemeChange() {
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
export function sendMessage() {
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
export function setupComposerListeners() {
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