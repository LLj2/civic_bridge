/**
 * Representatives display and interaction
 * Handles representative cards, institution sections, and contact buttons
 */

import { getRepresentatives } from './state.js';
import { getPartyCode, debounce } from './utils.js';
import { toggleRecipient, openDrawerWithRecipient } from './drawer.js';

/**
 * Display representatives results
 * @param {Object} data - API response data
 */
export function displayResults(data) {
  const { location, representatives: reps, summary } = data;
  const contentDiv = document.getElementById('resultsContent');
  
  // Result header
  let html = `
    <div class="result-header">
      <h2 class="result-title">📍 ${location.comune} (${location.provincia}) – ${location.regione}</h2>
      <p class="result-meta">Trovati ${summary.total_representatives} rappresentanti</p>
    </div>`;
  
  // Institution tabs (segmented control)
  html += `
    <div class="institution-tabs" role="tablist">
      <button class="tab-btn active" data-institution="all" role="tab" aria-selected="true" id="tab-all">
        Tutti <span class="tab-count">${summary.total_representatives}</span>
      </button>
      ${reps.camera && reps.camera.length > 0 ? 
        `<button class="tab-btn" data-institution="camera" role="tab" aria-selected="false" id="tab-camera">
          Camera <span class="tab-count">${summary.deputati_count}</span>
        </button>` : ''}
      ${reps.senato && reps.senato.length > 0 ? 
        `<button class="tab-btn" data-institution="senato" role="tab" aria-selected="false" id="tab-senato">
          Senato <span class="tab-count">${summary.senatori_count}</span>
        </button>` : ''}
      ${reps.eu_parliament && reps.eu_parliament.length > 0 ? 
        `<button class="tab-btn" data-institution="eu" role="tab" aria-selected="false" id="tab-eu">
          Parlamento Europeo <span class="tab-count">${summary.mep_count}</span>
        </button>` : ''}
    </div>`;
  
  // In-results search (above list)
  html += `
    <div class="search-within-results">
      <input type="text" id="searchResults" class="search-within-input" 
             placeholder="Filtra per nome, partito o collegio…">
    </div>`;
  
  // Representative list container (all reps, filtered by active tab)
  html += `<div class="representative-list" role="tabpanel" id="rep-list">`;
  
  // Add all representatives (tabs will filter them)
  if (reps.camera && reps.camera.length > 0) {
    reps.camera.forEach((rep, index) => {
      html += renderRepresentativeCard(rep, index, 'camera');
    });
  }
  
  if (reps.senato && reps.senato.length > 0) {
    reps.senato.forEach((rep, index) => {
      html += renderRepresentativeCard(rep, index, 'senato');
    });
  }
  
  if (reps.eu_parliament && reps.eu_parliament.length > 0) {
    reps.eu_parliament.forEach((rep, index) => {
      html += renderRepresentativeCard(rep, index, 'eu');
    });
  }
  
  html += `</div>`;
  
  contentDiv.innerHTML = html;
  
  // Setup event listeners for contact buttons (event delegation)
  setupContactButtonListeners(contentDiv);
  
  // Setup tab functionality
  setupTabListeners(contentDiv);
  
  // Setup search functionality  
  setupSearchListeners(contentDiv);
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
    <div class="representative" data-institution="${institution}" data-rep-id="rep-${institution}-${index}">
      <div class="rep-info">
        <div class="rep-name">${rep.nome} ${rep.cognome}</div>
        <div class="rep-details">${roleText} • ${partyCode}</div>
        <div class="rep-location">${locationInfo}</div>
        <div class="rep-contact">${rep.email || 'Nessuna email disponibile'}</div>
      </div>
      <div class="rep-actions">
        <button class="btn-add" 
                data-rep-index="${index}"
                data-institution="${institution}"
                ${isDisabled ? 'disabled' : ''}>
          Aggiungi
        </button>
        <button class="btn-contact-single"
                data-rep-index="${index}"
                data-institution="${institution}"
                ${isDisabled ? 'disabled' : ''}>
          Contatta
        </button>
      </div>
    </div>`;
}

/**
 * Setup contact button event listeners using event delegation
 * @param {HTMLElement} container - Container element
 */
function setupContactButtonListeners(container) {
  container.addEventListener('click', function(event) {
    const addBtn = event.target.closest('.btn-add');
    const contactBtn = event.target.closest('.btn-contact-single');
    
    if (addBtn && !addBtn.disabled) {
      const repIndex = parseInt(addBtn.dataset.repIndex);
      const institution = addBtn.dataset.institution;
      const repId = `rep-${institution}-${repIndex}`;
      
      // Toggle recipient selection
      toggleRecipient(repId, repIndex, institution);
      
    } else if (contactBtn && !contactBtn.disabled) {
      const repIndex = parseInt(contactBtn.dataset.repIndex);
      const institution = contactBtn.dataset.institution;
      
      // Open drawer with this specific recipient
      openDrawerWithRecipient(repIndex, institution);
    }
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

/**
 * Setup show/hide all button event listeners
 * @param {HTMLElement} container - Container element
 */
function setupShowHideAllListeners(container) {
  const expandBtn = container.querySelector('#expandAllBtn');
  const collapseBtn = container.querySelector('#collapseAllBtn');
  const selectAllBtn = container.querySelector('#selectAllBtn');
  const deselectAllBtn = container.querySelector('#deselectAllBtn');
  const contactSelectedBtn = container.querySelector('#contactSelectedBtn');
  
  if (expandBtn) {
    expandBtn.addEventListener('click', expandAllSections);
  }
  
  if (collapseBtn) {
    collapseBtn.addEventListener('click', collapseAllSections);
  }
  
  if (selectAllBtn) {
    selectAllBtn.addEventListener('click', selectAllRepresentatives);
  }
  
  if (deselectAllBtn) {
    deselectAllBtn.addEventListener('click', deselectAllRepresentatives);
  }
  
  if (contactSelectedBtn) {
    contactSelectedBtn.addEventListener('click', contactSelectedRepresentatives);
  }
}

/**
 * Expand all institution sections
 */
function expandAllSections() {
  const sections = document.querySelectorAll('.institution-section');
  sections.forEach(section => {
    const icon = section.querySelector('.collapse-icon');
    section.classList.remove('collapsed');
    if (icon) icon.textContent = '▼';
  });
}

/**
 * Collapse all institution sections
 */
function collapseAllSections() {
  const sections = document.querySelectorAll('.institution-section');
  sections.forEach(section => {
    const icon = section.querySelector('.collapse-icon');
    section.classList.add('collapsed');
    if (icon) icon.textContent = '▶';
  });
}

/**
 * Setup tab button event listeners
 * @param {HTMLElement} container - Container element
 */
function setupTabListeners(container) {
  const tabButtons = container.querySelectorAll('.tab-btn');
  
  tabButtons.forEach(button => {
    button.addEventListener('click', function() {
      const institution = this.dataset.institution;
      
      // Update active state and ARIA attributes
      tabButtons.forEach(btn => {
        btn.classList.remove('active');
        btn.setAttribute('aria-selected', 'false');
      });
      this.classList.add('active');
      this.setAttribute('aria-selected', 'true');
      
      // Apply tab filter
      applyTabFilter(institution);
    });
  });
}

/**
 * Apply tab filter
 * @param {string} institution - Institution type ('all', 'camera', 'senato', 'eu')
 */
function applyTabFilter(institution) {
  const representatives = document.querySelectorAll('.representative');
  
  representatives.forEach(rep => {
    const repInstitution = rep.dataset.institution;
    const isVisible = institution === 'all' || repInstitution === institution;
    
    if (isVisible) {
      rep.classList.remove('hidden');
      rep.classList.add('visible');
    } else {
      rep.classList.add('hidden');
      rep.classList.remove('visible');
    }
  });
}

/**
 * Setup selection event listeners
 * @param {HTMLElement} container - Container element
 */
function setupSelectionListeners(container) {
  // Listen for checkbox changes to update selected count
  container.addEventListener('change', function(event) {
    if (event.target.classList.contains('rep-checkbox')) {
      updateSelectedCount();
    }
  });
}

/**
 * Select all visible representatives
 */
function selectAllRepresentatives() {
  const checkboxes = document.querySelectorAll('.rep-checkbox:not(:disabled)');
  const visibleCheckboxes = Array.from(checkboxes).filter(cb => {
    const representative = cb.closest('.representative');
    const section = cb.closest('.institution-section');
    return representative && section && 
           !representative.classList.contains('hidden') &&
           !section.classList.contains('hidden');
  });
  
  visibleCheckboxes.forEach(checkbox => {
    checkbox.checked = true;
  });
  
  updateSelectedCount();
}

/**
 * Deselect all representatives
 */
function deselectAllRepresentatives() {
  const checkboxes = document.querySelectorAll('.rep-checkbox');
  checkboxes.forEach(checkbox => {
    checkbox.checked = false;
  });
  
  updateSelectedCount();
}

/**
 * Update selected representatives count
 */
function updateSelectedCount() {
  const selectedCheckboxes = document.querySelectorAll('.rep-checkbox:checked');
  const count = selectedCheckboxes.length;
  const contactBtn = document.getElementById('contactSelectedBtn');
  
  if (contactBtn) {
    contactBtn.textContent = `Contatta selezionati (${count})`;
    contactBtn.disabled = count === 0;
  }
}

/**
 * Contact selected representatives
 */
function contactSelectedRepresentatives() {
  const selectedCheckboxes = document.querySelectorAll('.rep-checkbox:checked');
  
  if (selectedCheckboxes.length === 0) return;
  
  // For now, open individual composer for first selected representative
  // In future versions, this could open a multi-recipient composer
  const firstCheckbox = selectedCheckboxes[0];
  const repIndex = parseInt(firstCheckbox.dataset.repIndex);
  const institution = firstCheckbox.dataset.institution;
  
  openComposer(repIndex, institution);
}

/**
 * Setup search functionality event listeners
 * @param {HTMLElement} container - Container element
 */
function setupSearchListeners(container) {
  const searchInput = container.querySelector('#searchResults');
  
  if (searchInput) {
    const debouncedSearch = debounce(performSearch, 300);
    
    searchInput.addEventListener('input', function() {
      const query = this.value.trim();
      debouncedSearch(query);
    });
  }
}

/**
 * Perform search within results
 * @param {string} query - Search query
 */
function performSearch(query) {
  const representatives = document.querySelectorAll('.representative');
  
  if (!query) {
    // Re-apply current tab filter instead of showing all
    const activeTab = document.querySelector('.tab-btn.active');
    const institution = activeTab ? activeTab.dataset.institution : 'all';
    applyTabFilter(institution);
    return;
  }
  
  const lowerQuery = query.toLowerCase();
  
  representatives.forEach(rep => {
    const nameElement = rep.querySelector('.rep-name');
    const detailsElement = rep.querySelector('.rep-details'); 
    const locationElement = rep.querySelector('.rep-location');
    
    if (nameElement && detailsElement && locationElement) {
      const name = nameElement.textContent.toLowerCase();
      const details = detailsElement.textContent.toLowerCase();
      const location = locationElement.textContent.toLowerCase();
      
      const matches = name.includes(lowerQuery) || 
                     details.includes(lowerQuery) || 
                     location.includes(lowerQuery);
      
      // Only show if matches search AND passes current tab filter
      const activeTab = document.querySelector('.tab-btn.active');
      const currentInstitution = activeTab ? activeTab.dataset.institution : 'all';
      const repInstitution = rep.dataset.institution;
      const passesTabFilter = currentInstitution === 'all' || repInstitution === currentInstitution;
      
      if (matches && passesTabFilter) {
        rep.classList.remove('hidden');
        rep.classList.add('visible');
      } else {
        rep.classList.add('hidden');
        rep.classList.remove('visible');
      }
    }
  });
}

/**
 * Update section visibility based on visible representatives
 */
function updateSectionVisibility() {
  const sections = document.querySelectorAll('.institution-section');
  
  sections.forEach(section => {
    const visibleReps = section.querySelectorAll('.representative.visible:not(.hidden)');
    const allReps = section.querySelectorAll('.representative');
    const hiddenReps = section.querySelectorAll('.representative.hidden');
    
    // Show section if it has any visible representatives
    if (visibleReps.length > 0) {
      section.classList.remove('hidden');
      section.classList.add('visible');
    } else if (hiddenReps.length === allReps.length) {
      // Hide section if all representatives are hidden
      section.classList.add('hidden');
      section.classList.remove('visible');
    }
  });
}