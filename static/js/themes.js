/**
 * Theme management module
 * Handles theme loading and template token replacement
 */

import { getThemes, getSelectedRep, getSelectedInstitution, getLocation } from './state.js';

/**
 * Replace template tokens with actual values
 * @param {string} text - Template text with tokens
 * @returns {string} Text with tokens replaced
 */
export function replaceTokens(text) {
  const location = getLocation();
  const selectedRep = getSelectedRep();
  
  const locationName = (location && location.comune) ? location.comune : '[Comune]';
  const repName = selectedRep ? `${selectedRep.nome} ${selectedRep.cognome}` : '[Nome Rappresentante]';
  
  return (text || '')
    .replace(/\{\{rep_name\}\}/g, repName)
    .replace(/\{\{location\}\}/g, locationName)
    .replace(/\{\{user_name\}\}/g, '[Il tuo nome]')
    .replace(/\{\{custom_subject\}\}/g, '[Inserisci oggetto specifico]');
}

/**
 * Get template for current representative and theme
 * @param {string} themeId - Theme identifier
 * @returns {Object|null} Template object with subject and body
 */
export function getTemplate(themeId) {
  const themes = getThemes();
  const institution = getSelectedInstitution();
  
  if (!themeId || !institution) return null;
  
  const theme = themes.find(t => t.id === themeId);
  if (!theme || !theme.templates[institution]) return null;
  
  return theme.templates[institution];
}

/**
 * Populate theme dropdown options
 * @param {HTMLSelectElement} selectElement - Theme dropdown element
 */
export function populateThemes(selectElement) {
  const themes = getThemes();
  
  selectElement.innerHTML = '<option value="">Seleziona un tema...</option>';
  
  themes.forEach(theme => {
    const option = document.createElement('option');
    option.value = theme.id;
    option.textContent = theme.title;
    selectElement.appendChild(option);
  });
}