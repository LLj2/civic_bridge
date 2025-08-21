/**
 * Single-recipient composer modal functionality
 * Handles theme selection, topic selection, and message composition
 */

import { getRepresentatives, getLocation } from './state.js';
import { getPartyCode } from './utils.js';

// Composer state
let currentRecipient = null;
let themes = [];
let topics = {};

// Theme and topic definitions
const THEMES_AND_TOPICS = {
  'guerra_palestina': {
    title: 'Guerra in Palestina',
    topics: [
      { id: 'cessate_fuoco', label: 'Chiedere cessate il fuoco immediato' },
      { id: 'aiuti_umanitari', label: 'Aumentare gli aiuti umanitari' },
      { id: 'protezione_civili', label: 'Protezione dei civili' },
      { id: 'diritti_umani', label: 'Rispetto dei diritti umani' }
    ]
  },
  'politiche_migrazione': {
    title: 'Politiche di migrazione',
    topics: [
      { id: 'accoglienza', label: 'Migliorare le politiche di accoglienza' },
      { id: 'integrazione', label: 'Sostegno all\'integrazione' },
      { id: 'corridoi_umanitari', label: 'Apertura di corridoi umanitari' },
      { id: 'cooperazione_ue', label: 'Cooperazione europea sulla migrazione' }
    ]
  },
  'ambiente_clima': {
    title: 'Ambiente e clima',
    topics: [
      { id: 'green_deal', label: 'Implementazione del Green Deal europeo' },
      { id: 'energie_rinnovabili', label: 'Investimenti in energie rinnovabili' },
      { id: 'trasporti_sostenibili', label: 'Promozione dei trasporti sostenibili' },
      { id: 'economia_circolare', label: 'Sviluppo dell\'economia circolare' }
    ]
  },
  'lavoro_sociale': {
    title: 'Lavoro e politiche sociali',
    topics: [
      { id: 'salario_minimo', label: 'Introduzione del salario minimo europeo' },
      { id: 'diritti_lavoratori', label: 'Protezione dei diritti dei lavoratori' },
      { id: 'giovani_lavoro', label: 'Politiche per l\'occupazione giovanile' },
      { id: 'welfare', label: 'Rafforzamento del welfare sociale' }
    ]
  },
  'altro': {
    title: 'Altro argomento',
    topics: []
  }
};

/**
 * Initialize composer functionality
 */
export function initComposer() {
  setupComposerListeners();
}

/**
 * Open composer modal with specific representative
 * @param {number} repIndex - Representative index
 * @param {string} institution - Institution type
 */
export function openComposerModal(repIndex, institution) {
  const representatives = getRepresentatives();
  if (!representatives) return;
  
  const institutionKey = institution === 'eu' ? 'eu_parliament' : institution;
  const rep = representatives[institutionKey]?.[repIndex];
  
  if (!rep) {
    console.error('Representative not found');
    return;
  }
  
  currentRecipient = { ...rep, institution, index: repIndex };
  setupModal();
  showModal();
}

/**
 * Setup modal content with current recipient
 */
function setupModal() {
  if (!currentRecipient) return;
  
  const modal = document.getElementById('composerModal');
  const title = document.getElementById('composerTitle');
  const subtitle = document.getElementById('composerSubtitle');
  
  // Update header
  const roleText = getRoleText(currentRecipient.institution);
  title.textContent = `Scrivi a ${roleText} ${currentRecipient.nome} ${currentRecipient.cognome}`;
  
  let subtitleText = '';
  if (currentRecipient.institution === 'camera') {
    subtitleText = `Partito: ${getPartyCode(currentRecipient.gruppo_partito)} • Collegio: ${currentRecipient.collegio}`;
  } else if (currentRecipient.institution === 'senato') {
    subtitleText = `Partito: ${getPartyCode(currentRecipient.gruppo_partito)} • Regione: ${currentRecipient.regione}`;
  } else if (currentRecipient.institution === 'eu') {
    subtitleText = `Partito: ${getPartyCode(currentRecipient.gruppo_partito)} • Circoscrizione: ${currentRecipient.circoscrizione_eu}`;
  }
  
  if (currentRecipient.email && currentRecipient.email !== 'Non disponibile') {
    subtitleText += `\nEmail: ${currentRecipient.email}`;
  } else {
    subtitleText += `\nNessun indirizzo email disponibile`;
  }
  
  subtitle.textContent = subtitleText;
  
  // Setup theme dropdown
  setupThemeDropdown();
  
  // Reset form
  resetForm();
}

/**
 * Get role text for institution
 * @param {string} institution - Institution type
 * @returns {string} Role text
 */
function getRoleText(institution) {
  switch (institution) {
    case 'camera': return 'Deputato';
    case 'senato': return 'Senatore';
    case 'eu': return 'MEP';
    default: return 'On.le';
  }
}


/**
 * Setup theme dropdown
 */
function setupThemeDropdown() {
  const themeSelect = document.getElementById('themeSelect');
  if (!themeSelect) return;
  
  themeSelect.innerHTML = '<option value="">Seleziona un tema...</option>';
  
  Object.entries(THEMES_AND_TOPICS).forEach(([key, theme]) => {
    const option = document.createElement('option');
    option.value = key;
    option.textContent = theme.title;
    themeSelect.appendChild(option);
  });
}

/**
 * Setup composer event listeners
 */
function setupComposerListeners() {
  // Close modal
  const closeBtn = document.getElementById('closeComposerBtn');
  if (closeBtn) {
    closeBtn.addEventListener('click', hideModal);
  }
  
  // Theme selection
  const themeSelect = document.getElementById('themeSelect');
  if (themeSelect) {
    themeSelect.addEventListener('change', handleThemeChange);
  }
  
  // Send button
  const sendBtn = document.getElementById('sendButton');
  if (sendBtn) {
    sendBtn.addEventListener('click', handleSend);
  }
  
  // Copy button
  const copyBtn = document.getElementById('copyTextBtn');
  if (copyBtn) {
    copyBtn.addEventListener('click', copyToClipboard);
  }
  
  // Modal overlay click to close
  const modal = document.getElementById('composerModal');
  if (modal) {
    modal.addEventListener('click', function(e) {
      if (e.target === modal) {
        hideModal();
      }
    });
  }
  
  // Escape key to close
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && isModalOpen()) {
      hideModal();
    }
  });
}

/**
 * Handle theme selection change
 */
function handleThemeChange() {
  const themeSelect = document.getElementById('themeSelect');
  const selectedTheme = themeSelect.value;
  
  // Show/hide topics section
  const topicsContainer = document.getElementById('topicsContainer');
  if (!topicsContainer) {
    createTopicsContainer();
  }
  
  updateTopicsDisplay(selectedTheme);
  updateSubject();
  updateBody();
}

/**
 * Create topics container if it doesn't exist
 */
function createTopicsContainer() {
  const themeField = document.getElementById('themeSelect').closest('.composer-field');
  const topicsContainer = document.createElement('div');
  topicsContainer.id = 'topicsContainer';
  topicsContainer.className = 'composer-field';
  topicsContainer.style.display = 'none';
  
  topicsContainer.innerHTML = `
    <label class="composer-label">Argomenti (opzionali):</label>
    <div id="topicsList" class="topics-list"></div>
  `;
  
  themeField.insertAdjacentElement('afterend', topicsContainer);
}

/**
 * Update topics display based on selected theme
 * @param {string} selectedTheme - Selected theme key
 */
function updateTopicsDisplay(selectedTheme) {
  const topicsContainer = document.getElementById('topicsContainer');
  const topicsList = document.getElementById('topicsList');
  
  if (!selectedTheme || selectedTheme === 'altro') {
    topicsContainer.style.display = 'none';
    return;
  }
  
  const theme = THEMES_AND_TOPICS[selectedTheme];
  if (!theme || !theme.topics.length) {
    topicsContainer.style.display = 'none';
    return;
  }
  
  topicsContainer.style.display = 'block';
  topicsList.innerHTML = '';
  
  theme.topics.forEach(topic => {
    const topicItem = document.createElement('div');
    topicItem.className = 'topic-item';
    topicItem.innerHTML = `
      <label class="topic-label">
        <input type="checkbox" class="topic-checkbox" value="${topic.id}">
        ${topic.label}
      </label>
    `;
    topicsList.appendChild(topicItem);
    
    // Add change listener
    const checkbox = topicItem.querySelector('.topic-checkbox');
    checkbox.addEventListener('change', function() {
      updateBody();
    });
  });
}

/**
 * Update subject based on theme
 */
function updateSubject() {
  const themeSelect = document.getElementById('themeSelect');
  const subjectInput = document.getElementById('subjectInput');
  const location = getLocation();
  
  if (!themeSelect.value) {
    subjectInput.value = '';
    return;
  }
  
  const theme = THEMES_AND_TOPICS[themeSelect.value];
  const comune = location?.comune || '[Comune]';
  
  subjectInput.value = `Richiesta da cittadino di ${comune}: ${theme.title}`;
}

/**
 * Update body based on theme and selected topics
 */
function updateBody() {
  const themeSelect = document.getElementById('themeSelect');
  const bodyTextarea = document.getElementById('bodyTextarea');
  const location = getLocation();
  
  if (!themeSelect.value) {
    bodyTextarea.value = '';
    return;
  }
  
  const theme = THEMES_AND_TOPICS[themeSelect.value];
  const comune = location?.comune || '[Comune]';
  const titolo = getTitleForRecipient(currentRecipient);
  
  let body = `Gentile ${titolo} ${currentRecipient.cognome},\n\n`;
  body += `Le scrivo come cittadino di ${comune} in merito a ${theme.title}.\n\n`;
  
  // Add selected topics
  const selectedTopics = getSelectedTopics();
  if (selectedTopics.length > 0) {
    body += `Punti principali:\n`;
    selectedTopics.forEach(topic => {
      body += `- ${topic}\n`;
    });
    body += `\n`;
  }
  
  body += `Cordiali saluti,\n[Firma opzionale]`;
  
  bodyTextarea.value = body;
}

/**
 * Get title for recipient based on role and gender
 * @param {Object} recipient - Recipient data
 * @returns {string} Title
 */
function getTitleForRecipient(recipient) {
  if (recipient.institution === 'eu') {
    return 'Onorevole';
  } else if (recipient.institution === 'senato') {
    return 'Senatrice'; // Could be improved with gender detection
  } else if (recipient.institution === 'camera') {
    return 'Onorevole';
  }
  return 'Onorevole';
}

/**
 * Get selected topics as array of labels
 * @returns {Array} Selected topic labels
 */
function getSelectedTopics() {
  const checkboxes = document.querySelectorAll('.topic-checkbox:checked');
  const topics = [];
  
  checkboxes.forEach(checkbox => {
    const label = checkbox.closest('.topic-label').textContent.trim();
    topics.push(label);
  });
  
  return topics;
}

/**
 * Handle send button click
 */
function handleSend() {
  const sendMethod = document.querySelector('input[name="sendMethod"]:checked')?.value || 'mailto';
  const subject = document.getElementById('subjectInput').value;
  const body = document.getElementById('bodyTextarea').value;
  
  if (!currentRecipient || !currentRecipient.email || currentRecipient.email === 'Non disponibile') {
    alert('Nessun indirizzo email disponibile per questo rappresentante.');
    return;
  }
  
  if (!subject || !body) {
    alert('Compila oggetto e messaggio prima di inviare.');
    return;
  }
  
  if (sendMethod === 'mailto') {
    openMailtoClient(subject, body);
  } else if (sendMethod === 'oauth') {
    // TODO: Implement OAuth sending
    alert('Invio tramite OAuth non ancora implementato.');
  }
}

/**
 * Open mailto client with composed message
 * @param {string} subject - Email subject
 * @param {string} body - Email body
 */
function openMailtoClient(subject, body) {
  const mailtoUrl = `mailto:${encodeURIComponent(currentRecipient.email)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  window.location.href = mailtoUrl;
  
  // Show success message and close modal
  setTimeout(() => {
    alert('Email aperta nel tuo client di posta!');
    hideModal();
  }, 500);
}

/**
 * Copy text to clipboard
 */
export function copyToClipboard() {
  const subject = document.getElementById('subjectInput').value;
  const body = document.getElementById('bodyTextarea').value;
  const text = `Oggetto: ${subject}\n\n${body}`;
  
  navigator.clipboard.writeText(text).then(() => {
    alert('Testo copiato negli appunti!');
  }).catch(() => {
    alert('Errore nella copia del testo.');
  });
}

/**
 * Show modal
 */
function showModal() {
  const modal = document.getElementById('composerModal');
  if (modal) {
    modal.classList.add('show');
    
    // Focus first input
    setTimeout(() => {
      const firstInput = modal.querySelector('select, input, textarea');
      if (firstInput) {
        firstInput.focus();
      }
    }, 100);
  }
}

/**
 * Hide modal
 */
function hideModal() {
  const modal = document.getElementById('composerModal');
  if (modal) {
    modal.classList.remove('show');
  }
  
  currentRecipient = null;
  resetForm();
}

/**
 * Check if modal is open
 * @returns {boolean} Modal open state
 */
function isModalOpen() {
  const modal = document.getElementById('composerModal');
  return modal && modal.classList.contains('show');
}

/**
 * Reset form to initial state
 */
function resetForm() {
  const themeSelect = document.getElementById('themeSelect');
  const subjectInput = document.getElementById('subjectInput');
  const bodyTextarea = document.getElementById('bodyTextarea');
  const topicsContainer = document.getElementById('topicsContainer');
  
  if (themeSelect) themeSelect.value = '';
  if (subjectInput) subjectInput.value = '';
  if (bodyTextarea) bodyTextarea.value = '';
  if (topicsContainer) topicsContainer.style.display = 'none';
  
  // Reset send method to mailto
  const mailtoRadio = document.getElementById('sendMailto');
  if (mailtoRadio) mailtoRadio.checked = true;
}