/**
 * Centralized state management for Civic Bridge
 * Single source of truth for application data
 */

// Application state
let currentRepresentatives = null;
let currentLocation = null;
let currentThemes = [];
let selectedRep = null;
let selectedInstitution = null;

/**
 * Update representatives data
 * @param {Object} reps - Representatives data from API
 */
export function setRepresentatives(reps) {
  currentRepresentatives = reps;
}

/**
 * Get current representatives data
 * @returns {Object|null} Current representatives
 */
export function getRepresentatives() {
  return currentRepresentatives;
}

/**
 * Update location data
 * @param {Object} location - Location data from API
 */
export function setLocation(location) {
  currentLocation = location;
}

/**
 * Get current location data
 * @returns {Object|null} Current location
 */
export function getLocation() {
  return currentLocation;
}

/**
 * Update themes data
 * @param {Array} themes - Available themes
 */
export function setThemes(themes) {
  currentThemes = themes;
}

/**
 * Get available themes
 * @returns {Array} Available themes
 */
export function getThemes() {
  return currentThemes;
}

/**
 * Set selected representative for composer
 * @param {Object} rep - Selected representative
 * @param {string} institution - Institution type ('camera', 'senato', 'eu')
 */
export function setSelectedRep(rep, institution) {
  selectedRep = rep;
  selectedInstitution = institution;
}

/**
 * Get selected representative
 * @returns {Object|null} Selected representative
 */
export function getSelectedRep() {
  return selectedRep;
}

/**
 * Get selected institution
 * @returns {string|null} Selected institution
 */
export function getSelectedInstitution() {
  return selectedInstitution;
}

/**
 * Clear selected representative
 */
export function clearSelectedRep() {
  selectedRep = null;
  selectedInstitution = null;
}