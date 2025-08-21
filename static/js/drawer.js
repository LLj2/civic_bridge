/**
 * Composer drawer functionality
 * Handles recipient management, templates, and email composition
 */

import { getRepresentatives } from './state.js';

// Drawer state
let selectedRecipients = new Set();
let templates = {
    segnalazione: {
        subject: "Segnalazione da cittadino di {COMUNE}",
        body: `Gentile {TITOLO} {COGNOME},

Mi rivolgo a Lei in qualità di cittadino di {COMUNE} per segnalare una questione di interesse pubblico che richiede la Sua attenzione.

[Inserisci qui i dettagli della tua segnalazione]

Confido nella Sua disponibilità ad affrontare questa questione e resto in attesa di un Suo riscontro.

Cordiali saluti,
[Il tuo nome]
Cittadino di {COMUNE}`
    },
    richiesta_info: {
        subject: "Richiesta informazioni da cittadino di {COMUNE}",
        body: `Gentile {TITOLO} {COGNOME},

Sono un cittadino di {COMUNE} e vorrei richiedere alcune informazioni riguardo a [argomento].

[Inserisci qui la tua richiesta specifica]

La ringrazio per il tempo che vorrà dedicare alla mia richiesta e resto in attesa di un Suo cortese riscontro.

Cordiali saluti,
[Il tuo nome]
Cittadino di {COMUNE}`
    },
    proposta_civica: {
        subject: "Proposta civica da cittadino di {COMUNE}",
        body: `Gentile {TITOLO} {COGNOME},

Mi permetto di sottoporre alla Sua attenzione una proposta che potrebbe essere di interesse per la nostra comunità di {COMUNE}.

[Descrivi qui la tua proposta]

Sarei lieto di poter discutere ulteriormente questa proposta e resto a disposizione per eventuali chiarimenti.

Cordiali saluti,
[Il tuo nome]
Cittadino di {COMUNE}`
    }
};

/**
 * Initialize drawer functionality
 */
export function initDrawer() {
    setupDrawerListeners();
}

/**
 * Add representative to selection
 * @param {string} repId - Representative ID
 * @param {number} repIndex - Representative index  
 * @param {string} institution - Institution type
 */
export function addRecipient(repId, repIndex, institution) {
    selectedRecipients.add(repId);
    updateDrawerVisibility();
    updateRecipientChips();
    
    // Update button state
    const button = document.querySelector(`[data-rep-index="${repIndex}"][data-institution="${institution}"].btn-add`);
    if (button) {
        button.textContent = 'Rimuovi';
        button.classList.add('selected');
    }
}

/**
 * Remove representative from selection
 * @param {string} repId - Representative ID
 * @param {number} repIndex - Representative index
 * @param {string} institution - Institution type
 */
export function removeRecipient(repId, repIndex, institution) {
    selectedRecipients.delete(repId);
    updateDrawerVisibility();
    updateRecipientChips();
    
    // Update button state
    const button = document.querySelector(`[data-rep-index="${repIndex}"][data-institution="${institution}"].btn-add`);
    if (button) {
        button.textContent = 'Aggiungi';
        button.classList.remove('selected');
    }
}

/**
 * Toggle representative selection
 * @param {string} repId - Representative ID
 * @param {number} repIndex - Representative index
 * @param {string} institution - Institution type
 */
export function toggleRecipient(repId, repIndex, institution) {
    if (selectedRecipients.has(repId)) {
        removeRecipient(repId, repIndex, institution);
    } else {
        addRecipient(repId, repIndex, institution);
    }
}

/**
 * Open drawer with specific recipient
 * @param {number} repIndex - Representative index
 * @param {string} institution - Institution type
 */
export function openDrawerWithRecipient(repIndex, institution) {
    const repId = `rep-${institution}-${repIndex}`;
    if (!selectedRecipients.has(repId)) {
        addRecipient(repId, repIndex, institution);
    }
    
    // Ensure drawer is visible
    updateDrawerVisibility();
}

/**
 * Setup drawer event listeners
 */
function setupDrawerListeners() {
    // Close drawer
    const closeBtn = document.getElementById('closeDrawer');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeDrawer);
    }
    
    // Template selection
    const templateSelect = document.getElementById('templateSelect');
    if (templateSelect) {
        templateSelect.addEventListener('change', function() {
            const template = templates[this.value];
            if (template) {
                applyTemplate(template);
            }
        });
    }
    
    // Copy text button
    const copyBtn = document.getElementById('copyTextBtn');
    if (copyBtn) {
        copyBtn.addEventListener('click', copyToClipboard);
    }
    
    // Open email button
    const emailBtn = document.getElementById('openEmailBtn');
    if (emailBtn) {
        emailBtn.addEventListener('click', openEmail);
    }
}

/**
 * Update drawer visibility based on selected recipients
 */
function updateDrawerVisibility() {
    const drawer = document.getElementById('composerDrawer');
    if (!drawer) return;
    
    if (selectedRecipients.size > 0) {
        drawer.classList.remove('is-hidden');
    } else {
        drawer.classList.add('is-hidden');
    }
}

/**
 * Update recipient chips display
 */
function updateRecipientChips() {
    const container = document.getElementById('recipientChips');
    if (!container) return;
    
    container.innerHTML = '';
    
    const representatives = getRepresentatives();
    if (!representatives) return;
    
    selectedRecipients.forEach(repId => {
        const rep = findRepresentativeById(repId, representatives);
        if (rep) {
            const chip = createRecipientChip(rep, repId);
            container.appendChild(chip);
        }
    });
    
    updateEmailButtonState();
}

/**
 * Find representative by ID
 * @param {string} repId - Representative ID
 * @param {Object} representatives - Representatives data
 * @returns {Object|null} Representative data
 */
function findRepresentativeById(repId, representatives) {
    const [, institution, index] = repId.split('-');
    const institutionKey = institution === 'eu' ? 'eu_parliament' : institution;
    const reps = representatives[institutionKey];
    
    return reps && reps[parseInt(index)] || null;
}

/**
 * Create recipient chip element
 * @param {Object} rep - Representative data
 * @param {string} repId - Representative ID
 * @returns {HTMLElement} Chip element
 */
function createRecipientChip(rep, repId) {
    const chip = document.createElement('div');
    chip.className = 'recipient-chip';
    
    const hasEmail = rep.email && rep.email !== 'Non disponibile';
    chip.innerHTML = `
        <span class="chip-text">${rep.nome} ${rep.cognome}</span>
        ${!hasEmail ? '<span class="chip-warning">⚠️</span>' : ''}
        <button class="chip-remove" data-rep-id="${repId}">×</button>
    `;
    
    // Add remove listener
    const removeBtn = chip.querySelector('.chip-remove');
    removeBtn.addEventListener('click', function() {
        const [, institution, index] = repId.split('-');
        removeRecipient(repId, parseInt(index), institution);
    });
    
    return chip;
}

/**
 * Apply template to subject and body fields
 * @param {Object} template - Template data
 */
function applyTemplate(template) {
    const subjectInput = document.getElementById('drawerSubject');
    const bodyTextarea = document.getElementById('drawerBody');
    
    // Get current location for placeholders
    const currentLocation = getCurrentLocation();
    
    if (subjectInput) {
        subjectInput.value = replacePlaceholders(template.subject, currentLocation);
    }
    
    if (bodyTextarea) {
        bodyTextarea.value = replacePlaceholders(template.body, currentLocation);
    }
}

/**
 * Replace template placeholders
 * @param {string} text - Template text
 * @param {Object} location - Location data
 * @returns {string} Processed text
 */
function replacePlaceholders(text, location) {
    return text
        .replace(/{COMUNE}/g, location.comune || '[COMUNE]')
        .replace(/{TITOLO}/g, 'On.le') // Default title
        .replace(/{COGNOME}/g, '[COGNOME]');
}

/**
 * Get current location from page
 * @returns {Object} Location data
 */
function getCurrentLocation() {
    const titleElement = document.querySelector('.result-title');
    if (titleElement) {
        const titleText = titleElement.textContent;
        const match = titleText.match(/📍\s*([^(]+)\s*\(([^)]+)\)\s*–\s*(.+)/);
        if (match) {
            return {
                comune: match[1].trim(),
                provincia: match[2].trim(), 
                regione: match[3].trim()
            };
        }
    }
    return { comune: '', provincia: '', regione: '' };
}

/**
 * Update email button state based on valid recipients
 */
function updateEmailButtonState() {
    const emailBtn = document.getElementById('openEmailBtn');
    if (!emailBtn) return;
    
    const validRecipients = getValidRecipients();
    const isDisabled = validRecipients.length === 0;
    
    emailBtn.disabled = isDisabled;
    emailBtn.textContent = isDisabled ? 'Nessuna email valida' : 'Apri email';
}

/**
 * Get recipients with valid email addresses
 * @returns {Array} Valid recipients
 */
function getValidRecipients() {
    const representatives = getRepresentatives();
    if (!representatives) return [];
    
    const validRecipients = [];
    selectedRecipients.forEach(repId => {
        const rep = findRepresentativeById(repId, representatives);
        if (rep && rep.email && rep.email !== 'Non disponibile') {
            validRecipients.push(rep);
        }
    });
    
    return validRecipients;
}

/**
 * Copy subject and body to clipboard
 */
async function copyToClipboard() {
    const subject = document.getElementById('drawerSubject')?.value || '';
    const body = document.getElementById('drawerBody')?.value || '';
    
    const text = `Oggetto: ${subject}\n\n${body}`;
    
    try {
        await navigator.clipboard.writeText(text);
        showToast('Testo copiato negli appunti');
    } catch (err) {
        console.error('Failed to copy text: ', err);
        showToast('Errore nella copia del testo', 'error');
    }
}

/**
 * Open email client with composed message
 */
function openEmail() {
    const validRecipients = getValidRecipients();
    if (validRecipients.length === 0) return;
    
    const subject = document.getElementById('drawerSubject')?.value || '';
    const body = document.getElementById('drawerBody')?.value || '';
    
    // Build BCC list
    const bccEmails = validRecipients.map(rep => rep.email).join(',');
    
    // Create mailto URL
    const mailtoUrl = `mailto:?bcc=${encodeURIComponent(bccEmails)}&subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    
    // Open email client
    window.location.href = mailtoUrl;
    
    showToast('Bozza email aperta nel tuo client');
}

/**
 * Close drawer
 */
function closeDrawer() {
    selectedRecipients.clear();
    updateDrawerVisibility();
    
    // Reset all add buttons
    document.querySelectorAll('.btn-add.selected').forEach(btn => {
        btn.textContent = 'Aggiungi';
        btn.classList.remove('selected');
    });
    
    // Clear form
    document.getElementById('templateSelect').value = '';
    document.getElementById('drawerSubject').value = '';
    document.getElementById('drawerBody').value = '';
}

/**
 * Show toast notification
 * @param {string} message - Toast message
 * @param {string} type - Toast type ('success' or 'error')
 */
function showToast(message, type = 'success') {
    // Simple toast implementation
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}