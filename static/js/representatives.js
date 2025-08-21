/**
 * Representatives display and interaction
 * Handles representative cards, institution sections, and contact buttons
 */

import { getRepresentatives } from './state.js';
import { getPartyCode, debounce } from './utils.js';
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
  
  // Add filter buttons
  html += `
    <div class="filter-controls">
      <div class="filter-group">
        <label>Filtra per istituzione:</label>
        <div class="filter-buttons">
          <button class="filter-btn active" data-filter="all">Tutti (${summary.total_representatives})</button>
          ${reps.camera && reps.camera.length > 0 ? 
            `<button class="filter-btn" data-filter="camera">Camera (${summary.deputati_count})</button>` : ''}
          ${reps.senato && reps.senato.length > 0 ? 
            `<button class="filter-btn" data-filter="senato">Senato (${summary.senatori_count})</button>` : ''}
          ${reps.eu_parliament && reps.eu_parliament.length > 0 ? 
            `<button class="filter-btn" data-filter="eu">EU (${summary.mep_count})</button>` : ''}
        </div>
      </div>
      
      <div class="filter-group">
        <label for="searchResults">Cerca rappresentanti:</label>
        <input type="text" id="searchResults" class="search-results-input" 
               placeholder="Nome, cognome, partito...">
        <button class="btn-outline" id="clearSearchBtn">Pulisci</button>
      </div>
    </div>`;
  
  // Add show/hide controls
  html += `
    <div class="section-controls">
      <div class="control-group">
        <span class="control-label">Sezioni:</span>
        <button class="btn-outline" id="expandAllBtn">Mostra tutto</button>
        <button class="btn-outline" id="collapseAllBtn">Nascondi tutto</button>
      </div>
      <div class="control-group">
        <span class="control-label">Selezione:</span>
        <button class="btn-outline" id="selectAllBtn">Seleziona tutti</button>
        <button class="btn-outline" id="deselectAllBtn">Deseleziona tutti</button>
        <button class="btn-primary" id="contactSelectedBtn" disabled>Contatta selezionati (0)</button>
      </div>
    </div>`;
  
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
  
  // Setup show/hide all buttons
  setupShowHideAllListeners(contentDiv);
  
  // Setup filter buttons
  setupFilterListeners(contentDiv);
  
  // Setup selection functionality
  setupSelectionListeners(contentDiv);
  
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
    <div class="representative">
      <div class="rep-selection">
        <input type="checkbox" 
               class="rep-checkbox" 
               id="rep-${institution}-${index}"
               data-rep-index="${index}"
               data-institution="${institution}"
               ${isDisabled ? 'disabled' : ''}>
        <label for="rep-${institution}-${index}" class="checkbox-label"></label>
      </div>
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
 * Setup filter button event listeners
 * @param {HTMLElement} container - Container element
 */
function setupFilterListeners(container) {
  const filterButtons = container.querySelectorAll('.filter-btn');
  
  filterButtons.forEach(button => {
    button.addEventListener('click', function() {
      const filter = this.dataset.filter;
      
      // Update active state
      filterButtons.forEach(btn => btn.classList.remove('active'));
      this.classList.add('active');
      
      // Apply filter
      applyInstitutionFilter(filter);
    });
  });
}

/**
 * Apply institution filter
 * @param {string} filter - Filter type ('all', 'camera', 'senato', 'eu')
 */
function applyInstitutionFilter(filter) {
  const sections = document.querySelectorAll('.institution-section');
  
  sections.forEach(section => {
    const sectionId = section.id;
    const isVisible = filter === 'all' || sectionId.includes(filter);
    
    if (isVisible) {
      section.classList.remove('hidden');
      section.classList.add('visible');
      // Expand visible sections
      section.classList.remove('collapsed');
      const icon = section.querySelector('.collapse-icon');
      if (icon) icon.textContent = '▼';
    } else {
      section.classList.add('hidden');
      section.classList.remove('visible');
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
  const clearBtn = container.querySelector('#clearSearchBtn');
  
  if (searchInput) {
    const debouncedSearch = debounce(performSearch, 300);
    
    searchInput.addEventListener('input', function() {
      const query = this.value.trim();
      debouncedSearch(query);
    });
  }
  
  if (clearBtn) {
    clearBtn.addEventListener('click', function() {
      if (searchInput) {
        searchInput.value = '';
        performSearch('');
      }
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
    // Show all representatives
    representatives.forEach(rep => {
      rep.classList.remove('hidden');
      rep.classList.add('visible');
    });
    updateSectionVisibility();
    return;
  }
  
  const lowerQuery = query.toLowerCase();
  
  representatives.forEach(rep => {
    const nameElement = rep.querySelector('.rep-name');
    const detailsElement = rep.querySelector('.rep-details');
    const collegioElement = rep.querySelector('.rep-collegio');
    
    if (nameElement && detailsElement && collegioElement) {
      const name = nameElement.textContent.toLowerCase();
      const details = detailsElement.textContent.toLowerCase();
      const collegio = collegioElement.textContent.toLowerCase();
      
      const matches = name.includes(lowerQuery) || 
                     details.includes(lowerQuery) || 
                     collegio.includes(lowerQuery);
      
      if (matches) {
        rep.classList.remove('hidden');
        rep.classList.add('visible');
      } else {
        rep.classList.add('hidden');
        rep.classList.remove('visible');
      }
    }
  });
  
  updateSectionVisibility();
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