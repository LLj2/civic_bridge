/**
 * Representatives display and interaction
 * Handles representative cards, institution sections, and contact buttons
 */

import { getRepresentatives } from './state.js';
import { getPartyCode } from './utils.js';
import { openComposer } from './composer.js';

/**
 * Display representatives results
 * @param {Object} data - API response data
 */
export function displayResults(data) {
  const { location, representatives: reps, summary } = data;
  const contentDiv = document.getElementById('resultsContent');
  
  let html = `<h2>📍 ${location.comune} (${location.provincia}) - ${location.regione}</h2>` +
    `<p><strong>Totale rappresentanti trovati: ${summary.total_representatives}</strong></p>`;
  
  // Camera dei Deputati
  if (reps.camera && reps.camera.length > 0) {
    html += renderInstitutionSection('camera', 'Camera dei Deputati', '🏛️', reps.camera, summary.deputati_count);
  }
  
  // Senato della Repubblica
  if (reps.senato && reps.senato.length > 0) {
    html += renderInstitutionSection('senato', 'Senato della Repubblica', '🏛️', reps.senato, summary.senatori_count);
  }
  
  // Parlamento Europeo
  if (reps.eu_parliament && reps.eu_parliament.length > 0) {
    html += renderInstitutionSection('eu', 'Parlamento Europeo', '🇪🇺', reps.eu_parliament, summary.mep_count);
  }
  
  contentDiv.innerHTML = html;
  
  // Setup event listeners for contact buttons (event delegation)
  setupContactButtonListeners(contentDiv);
  
  // Setup section toggle listeners
  setupSectionToggleListeners(contentDiv);
}

/**
 * Render institution section HTML
 * @param {string} institutionKey - Institution key (camera, senato, eu)
 * @param {string} title - Institution title
 * @param {string} icon - Institution icon
 * @param {Array} representatives - Representatives array
 * @param {number} count - Representative count
 * @returns {string} HTML string
 */
function renderInstitutionSection(institutionKey, title, icon, representatives, count) {
  const sectionId = `${institutionKey}-section`;
  
  let html = `
    <div class="institution-section collapsed" id="${sectionId}">
      <div class="institution-header" data-section="${sectionId}">
        <h3 class="institution-title">
          ${icon} ${title}
          <span class="institution-count">${count}</span>
        </h3>
        <span class="collapse-icon">▶</span>
      </div>
      <div class="institution-content">
        <div class="institution-representatives">`;
  
  representatives.forEach((rep, index) => {
    html += renderRepresentativeCard(rep, index, institutionKey);
  });
  
  html += `
        </div>
      </div>
    </div>`;
  
  return html;
}

/**
 * Render representative card HTML
 * @param {Object} rep - Representative data
 * @param {number} index - Representative index
 * @param {string} institution - Institution type
 * @returns {string} HTML string
 */
function renderRepresentativeCard(rep, index, institution) {
  const partyCode = getPartyCode(rep.gruppo_partito);
  
  let roleText = '';
  let locationInfo = '';
  
  switch (institution) {
    case 'camera':
      roleText = 'Deputato';
      locationInfo = `Collegio: ${rep.collegio}`;
      break;
    case 'senato':
      roleText = 'Senatore';
      locationInfo = `Regione: ${rep.regione}`;
      break;
    case 'eu':
      roleText = 'MEP';
      locationInfo = `Circoscrizione: ${rep.circoscrizione_eu}`;
      break;
  }
  
  const isDisabled = (!rep.email || rep.email === 'Non disponibile');
  
  return `
    <div class="representative">
      <div class="rep-info">
        <div class="rep-name">${rep.nome} ${rep.cognome}</div>
        <div class="rep-details">${roleText} · ${partyCode}</div>
        <div class="rep-collegio">${locationInfo}</div>
      </div>
      <button class="rep-contact-btn"
              data-rep-index="${index}"
              data-institution="${institution}"
              ${isDisabled ? 'disabled' : ''}>
        Contatta
      </button>
    </div>`;
}

/**
 * Setup contact button event listeners using event delegation
 * @param {HTMLElement} container - Container element
 */
function setupContactButtonListeners(container) {
  container.addEventListener('click', function(event) {
    const button = event.target.closest('.rep-contact-btn');
    if (!button || button.disabled) return;
    
    const repIndex = parseInt(button.dataset.repIndex);
    const institution = button.dataset.institution;
    
    // Open composer modal
    openComposer(repIndex, institution);
  });
}

/**
 * Setup section toggle event listeners
 * @param {HTMLElement} container - Container element
 */
function setupSectionToggleListeners(container) {
  container.addEventListener('click', function(event) {
    const header = event.target.closest('.institution-header');
    if (!header) return;
    
    const sectionId = header.dataset.section;
    if (sectionId) {
      toggleSection(sectionId);
    }
  });
}

/**
 * Toggle collapsible section
 * @param {string} sectionId - Section ID to toggle
 */
export function toggleSection(sectionId) {
  const section = document.getElementById(sectionId);
  if (!section) return;
  
  const icon = section.querySelector('.collapse-icon');
  
  if (section.classList.contains('collapsed')) {
    section.classList.remove('collapsed');
    icon.textContent = '▼';
  } else {
    section.classList.add('collapsed');
    icon.textContent = '▶';
  }
}