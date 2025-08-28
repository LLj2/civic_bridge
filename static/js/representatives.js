/**
 * Representatives display and interaction
 * Handles representative cards, institution sections, and contact buttons
 */

import { getRepresentatives } from './state.js';
import { getPartyCode, getFullPartyName, isPartyMatch, getPartyColor, debounce } from './utils.js';
import { openComposer } from './composer.js';

/**
 * Create and setup live region for screen readers
 */
function setupLiveRegion() {
  let liveRegion = document.getElementById('liveRegion');
  if (!liveRegion) {
    liveRegion = document.createElement('div');
    liveRegion.id = 'liveRegion';
    liveRegion.setAttribute('aria-live', 'polite');
    liveRegion.setAttribute('aria-atomic', 'true');
    liveRegion.className = 'sr-only';
    liveRegion.style.cssText = 'position: absolute; left: -10000px; width: 1px; height: 1px; overflow: hidden;';
    document.body.appendChild(liveRegion);
  }
  return liveRegion;
}

/**
 * Announce message to screen readers
 * @param {string} message - Message to announce
 */
function announceToScreenReader(message) {
  const liveRegion = setupLiveRegion();
  liveRegion.textContent = message;
}

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
 * Convert string to Title Case
 * @param {string} str - String to convert
 * @returns {string} Title case string
 */
function toTitleCase(str) {
  if (!str) return '';
  return str.toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
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
  const fullPartyName = getFullPartyName(rep.gruppo_partito);
  const partyColor = getPartyColor(fullPartyName);
  
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
  
  // Generate initials for fallback avatar
  const initials = `${rep.nome?.charAt(0) || ''}${rep.cognome?.charAt(0) || ''}`.toUpperCase();
  
  // Generate muted party color for avatar background
  const getMutedPartyColor = (hexColor) => {
    // Convert hex to RGB
    const r = parseInt(hexColor.slice(1, 3), 16);
    const g = parseInt(hexColor.slice(3, 5), 16);
    const b = parseInt(hexColor.slice(5, 7), 16);
    
    // Make it lighter and more muted (blend with white)
    const factor = 0.15; // 15% of original color, 85% white
    const mutedR = Math.round(r * factor + 255 * (1 - factor));
    const mutedG = Math.round(g * factor + 255 * (1 - factor));
    const mutedB = Math.round(b * factor + 255 * (1 - factor));
    
    return `rgb(${mutedR}, ${mutedG}, ${mutedB})`;
  };
  
  const avatarBgColor = getMutedPartyColor(partyColor);
  
  // Determine if we have a photo
  const hasPhoto = rep.photo_url && rep.photo_url.trim() !== '';
  
  // Calculate text color for party chip based on background contrast
  const getContrastColor = (hexColor) => {
    // Convert hex to RGB
    const r = parseInt(hexColor.slice(1, 3), 16);
    const g = parseInt(hexColor.slice(3, 5), 16);
    const b = parseInt(hexColor.slice(5, 7), 16);
    
    // Calculate luminance
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance > 0.5 ? '#000000' : '#ffffff';
  };
  
  const chipTextColor = getContrastColor(partyColor);
  
  return `
    <div class="representative" 
         data-institution="${institution}" 
         data-rep-id="rep-${institution}-${index}" 
         data-party-full="${fullPartyName}" 
         role="article" 
         aria-labelledby="rep-name-${institution}-${index}"
         style="--party-color: ${partyColor}">
      <div class="party-accent-bar"></div>
      <div class="rep-photo-container">
        <div class="rep-avatar" style="background: ${avatarBgColor}; color: #4a5568;">${initials}</div>
        ${hasPhoto ? 
          `<img class="rep-photo" 
                src="${rep.photo_url}" 
                alt="" 
                loading="lazy"
                data-rep-id="rep-${institution}-${index}">` : 
          ''
        }
      </div>
      <div class="rep-info">
        <h3 id="rep-name-${institution}-${index}" class="rep-name">${toTitleCase(rep.nome)} ${toTitleCase(rep.cognome)}</h3>
        <div class="rep-role-party">
          <span class="rep-role">${roleText}</span> • 
          <span class="party-chip" style="background-color: ${partyColor}; color: ${chipTextColor};">${partyCode}</span>
        </div>
        <div class="rep-location">${locationInfo}</div>
        <div class="rep-email">${rep.email || 'Nessuna email disponibile'}</div>
      </div>
      <div class="rep-actions">
        <button class="btn-contact-primary"
                data-rep-index="${index}"
                data-institution="${institution}"
                aria-label="Contatta ${rep.nome} ${rep.cognome}"
                ${isDisabled ? 'disabled aria-disabled="true"' : ''}>
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
    const contactBtn = event.target.closest('.btn-contact-primary');
    
    if (contactBtn && !contactBtn.disabled) {
      const repIndex = parseInt(contactBtn.dataset.repIndex);
      const institution = contactBtn.dataset.institution;
      
      // Open composer modal with this specific recipient
      openComposer(repIndex, institution);
    }
  });
  
  // Handle image load errors - hide broken images to show avatar underneath
  container.addEventListener('error', function(event) {
    if (event.target.classList.contains('rep-photo')) {
      event.target.style.display = 'none';
    }
  }, true);
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
    
    // Keyboard navigation support
    button.addEventListener('keydown', function(e) {
      const buttons = Array.from(tabButtons);
      const currentIndex = buttons.indexOf(this);
      let targetIndex = -1;
      
      switch(e.key) {
        case 'ArrowLeft':
          e.preventDefault();
          targetIndex = currentIndex > 0 ? currentIndex - 1 : buttons.length - 1;
          break;
        case 'ArrowRight':
          e.preventDefault();
          targetIndex = currentIndex < buttons.length - 1 ? currentIndex + 1 : 0;
          break;
        case 'Home':
          e.preventDefault();
          targetIndex = 0;
          break;
        case 'End':
          e.preventDefault();
          targetIndex = buttons.length - 1;
          break;
      }
      
      if (targetIndex >= 0) {
        buttons[targetIndex].focus();
        buttons[targetIndex].click();
      }
    });
  });
}

/**
 * Apply tab filter
 * @param {string} institution - Institution type ('all', 'camera', 'senato', 'eu')
 */
function applyTabFilter(institution) {
  const representatives = document.querySelectorAll('.representative');
  let visibleCount = 0;
  
  representatives.forEach(rep => {
    const repInstitution = rep.dataset.institution;
    const isVisible = institution === 'all' || repInstitution === institution;
    
    if (isVisible) {
      rep.classList.remove('hidden');
      rep.classList.add('visible');
      visibleCount++;
    } else {
      rep.classList.add('hidden');
      rep.classList.remove('visible');
    }
  });
  
  // Check for empty state
  updateEmptyState(institution);
  
  // Announce filter change to screen readers
  const institutionNames = {
    all: 'tutti i rappresentanti',
    camera: 'deputati della Camera',
    senato: 'senatori del Senato', 
    eu: 'eurodeputati'
  };
  
  const institutionName = institutionNames[institution] || institution;
  announceToScreenReader(`Filtro applicato: mostrati ${visibleCount} ${institutionName}`);
}

/**
 * Update empty state display
 * @param {string} institution - Current active institution
 */
function updateEmptyState(institution) {
  const visibleReps = document.querySelectorAll('.representative.visible:not(.hidden)');
  const listContainer = document.getElementById('rep-list');
  
  // Remove existing empty state
  const existingEmptyState = document.querySelector('.empty-state');
  if (existingEmptyState) {
    existingEmptyState.remove();
  }
  
  if (visibleReps.length === 0) {
    const emptyState = createEmptyState(institution);
    listContainer.appendChild(emptyState);
  }
}

/**
 * Create empty state element
 * @param {string} institution - Institution type
 * @returns {HTMLElement} Empty state element
 */
function createEmptyState(institution) {
  const emptyState = document.createElement('div');
  emptyState.className = 'empty-state';
  
  let message = '';
  let icon = '🔍';
  
  const searchInput = document.getElementById('searchResults');
  const hasSearchQuery = searchInput && searchInput.value.trim();
  
  if (hasSearchQuery) {
    message = `Nessun rappresentante trovato per "${searchInput.value.trim()}"`;
    icon = '🔍';
  } else {
    switch (institution) {
      case 'camera':
        message = 'Nessun deputato trovato per questo Comune.';
        icon = '🏛️';
        break;
      case 'senato':
        message = 'Nessun senatore trovato per questo Comune.';
        icon = '🏛️';
        break;
      case 'eu':
        message = 'Nessun eurodeputato trovato per questo Comune.';
        icon = '🇪🇺';
        break;
      default:
        message = 'Nessun rappresentante trovato per questo Comune.';
        icon = '📭';
    }
  }
  
  emptyState.innerHTML = `
    <div class="empty-state-content">
      <div class="empty-state-icon">${icon}</div>
      <div class="empty-state-message">${message}</div>
      ${hasSearchQuery ? '<div class="empty-state-hint">Prova a cercare con termini diversi o seleziona un\'altra istituzione.</div>' : ''}
    </div>
  `;
  
  return emptyState;
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
    const rolePartyElement = rep.querySelector('.rep-role-party'); 
    const locationElement = rep.querySelector('.rep-location');
    const emailElement = rep.querySelector('.rep-email');
    const fullPartyName = rep.dataset.partyFull;
    
    if (nameElement) {
      const name = nameElement.textContent.toLowerCase();
      const roleParty = rolePartyElement ? rolePartyElement.textContent.toLowerCase() : '';
      const location = locationElement ? locationElement.textContent.toLowerCase() : '';
      const email = emailElement ? emailElement.textContent.toLowerCase() : '';
      
      // Enhanced matching with party names
      const matches = name.includes(lowerQuery) || 
                     roleParty.includes(lowerQuery) || 
                     location.includes(lowerQuery) ||
                     email.includes(lowerQuery) ||
                     isPartyMatch(query, fullPartyName);
      
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
  
  // Update empty state after search
  const activeTab = document.querySelector('.tab-btn.active');
  const institution = activeTab ? activeTab.dataset.institution : 'all';
  updateEmptyState(institution);
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