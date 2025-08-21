/**
 * API communication module
 * Handles all HTTP requests to the Flask backend
 */

/**
 * Autocomplete API call
 * @param {string} query - Search query
 * @returns {Promise<Object>} API response
 */
export async function autocomplete(query) {
  const response = await fetch('/api/autocomplete?q=' + encodeURIComponent(query));
  const data = await response.json();
  return data;
}

/**
 * Lookup representatives for a location
 * @param {string} comune - City name
 * @returns {Promise<Object>} API response with representatives data
 */
export async function lookup(comune) {
  const response = await fetch('/api/lookup?q=' + encodeURIComponent(comune));
  const data = await response.json();
  return data;
}

/**
 * Load themes from API
 * @returns {Promise<Object>} Themes configuration
 */
export async function loadThemes() {
  const response = await fetch('/api/themes');
  const data = await response.json();
  return data;
}