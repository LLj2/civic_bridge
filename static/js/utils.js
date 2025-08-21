/**
 * Utility functions
 * Helper functions used across the application
 */

/**
 * Show notification to user
 * @param {string} message - Notification message
 * @param {string} type - Notification type ('success', 'error', 'info')
 */
export function showNotification(message, type = 'info') {
  // Remove any existing notifications
  const existingNotifications = document.querySelectorAll('.notification');
  existingNotifications.forEach(notif => notif.remove());
  
  // Create notification element
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.textContent = message;
  
  // Add to DOM
  document.body.appendChild(notification);
  
  // Show notification
  setTimeout(() => {
    notification.classList.add('show');
  }, 100);
  
  // Hide after 4 seconds
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 300);
  }, 4000);
}

/**
 * Get party code abbreviation
 * @param {string} party - Full party name
 * @returns {string} Party abbreviation
 */
export function getPartyCode(party) {
  const partyCodes = {
    'Partito Democratico': 'PD',
    'Lega': 'Lega',
    'Movimento 5 Stelle': 'M5S',
    'Forza Italia': 'FI',
    'Fratelli d\'Italia': 'FdI',
    'Italia Viva': 'IV',
    'Azione': 'Az',
    'Più Europa': '+Eu',
    'Alleanza Verdi e Sinistra': 'AVS',
    'Noi Moderati': 'NM'
  };
  
  if (partyCodes[party]) return partyCodes[party];
  const p = (party || '').toString();
  return p ? p.substring(0, 3).toUpperCase() : '';
}

/**
 * Get party color for styling
 * @param {string} party - Full party name
 * @returns {string} Hex color code
 */
export function getPartyColor(party) {
  const partyColors = {
    'Partito Democratico': '#e53e3e',
    'Lega': '#3182ce',
    'Movimento 5 Stelle': '#f0ad4e',
    'Forza Italia': '#3b82f6',
    'Fratelli d\'Italia': '#0f172a',
    'Italia Viva': '#8b5cf6',
    'Azione': '#10b981',
    'Più Europa': '#f59e0b'
  };
  return partyColors[party] || '#6b7280';
}

/**
 * Debounce function to limit API calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Delay in milliseconds
 * @returns {Function} Debounced function
 */
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}