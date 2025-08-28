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

// Comprehensive party mapping with full names, abbreviations, and search keywords
const PARTY_MAPPINGS = {
  // Key is a normalized version for matching, value contains all party info
  'partito_democratico': {
    abbreviation: 'PD',
    fullName: 'Partito Democratico',
    searchKeywords: ['pd', 'partito democratico', 'democratico', 'dem'],
    variations: ['PARTITO DEMOCRATICO - ITALIA DEMOCRATICA E PROGRESSISTA']
  },
  'lega': {
    abbreviation: 'Lega',
    fullName: 'Lega',
    searchKeywords: ['lega', 'salvini', 'lega nord', 'lega - salvini premier'],
    variations: ['LEGA - SALVINI PREMIER']
  },
  'movimento_5_stelle': {
    abbreviation: 'M5S',
    fullName: 'Movimento 5 Stelle',
    searchKeywords: ['m5s', 'movimento 5 stelle', 'cinque stelle', '5 stelle', 'movimento'],
    variations: ['MOVIMENTO 5 STELLE']
  },
  'forza_italia': {
    abbreviation: 'FI',
    fullName: 'Forza Italia',
    searchKeywords: ['fi', 'forza italia', 'berlusconi'],
    variations: ['FORZA ITALIA']
  },
  'fratelli_ditalia': {
    abbreviation: 'FdI',
    fullName: "Fratelli d'Italia",
    searchKeywords: ['fdi', 'fratelli ditalia', "fratelli d'italia", 'meloni'],
    variations: ["FRATELLI D'ITALIA"]
  },
  'italia_viva': {
    abbreviation: 'IV',
    fullName: 'Italia Viva',
    searchKeywords: ['iv', 'italia viva', 'renzi'],
    variations: ['ITALIA VIVA', 'AZIONE - ITALIA VIVA - RENEW EUROPE']
  },
  'azione': {
    abbreviation: 'Az',
    fullName: 'Azione',
    searchKeywords: ['az', 'azione', 'calenda'],
    variations: ['AZIONE', 'AZIONE - ITALIA VIVA - CALENDA', 'AZIONE - ITALIA VIVA - RENEW EUROPE']
  },
  'piu_europa': {
    abbreviation: '+Eu',
    fullName: 'Più Europa',
    searchKeywords: ['+eu', 'più europa', 'piu europa', 'bonino'],
    variations: ['PIÙ EUROPA']
  },
  'alleanza_verdi_sinistra': {
    abbreviation: 'AVS',
    fullName: 'Alleanza Verdi e Sinistra',
    searchKeywords: ['avs', 'alleanza verdi sinistra', 'verdi', 'sinistra', 'verde'],
    variations: ['ALLEANZA VERDI E SINISTRA']
  },
  'noi_moderati': {
    abbreviation: 'NM',
    fullName: 'Noi Moderati',
    searchKeywords: ['nm', 'noi moderati', 'moderati'],
    variations: ['NOI MODERATI']
  }
};

/**
 * Get party code abbreviation
 * @param {string} party - Full party name
 * @returns {string} Party abbreviation
 */
export function getPartyCode(party) {
  if (!party) return '';
  
  // Handle Senate-specific party codes
  const senateMapping = {
    'PD-IDP': 'PD',           // Partito Democratico
    'FI-BP-PPE': 'FI',         // Forza Italia
    'LSP-PS': 'Lega',          // Lega
    'M5S': 'M5S',              // Movimento 5 Stelle
    'F': 'FdI',                // Fratelli d'Italia
    'IV-C-RE': 'IV',           // Italia Viva
    'M': 'Misto',              // Gruppo Misto
    'A': 'Aut',                // Autonomie
    'C': 'CI'                  // Centro/Civici
  };
  
  // Check if it's a Senate party code first
  if (senateMapping[party]) return senateMapping[party];
  
  // First try exact match with existing logic for backward compatibility
  const exactMatches = {
    'Partito Democratico': 'PD',
    'Lega': 'Lega',
    'Movimento 5 Stelle': 'M5S',
    'Forza Italia': 'FI',
    "Fratelli d'Italia": 'FdI',
    'Italia Viva': 'IV',
    'Azione': 'Az',
    'Più Europa': '+Eu',
    'Alleanza Verdi e Sinistra': 'AVS',
    'Noi Moderati': 'NM'
  };
  
  if (exactMatches[party]) return exactMatches[party];
  
  // Try to match against party variations in the comprehensive mapping
  const partyStr = party.toString().toUpperCase();
  
  for (const [key, partyData] of Object.entries(PARTY_MAPPINGS)) {
    // Check if the input matches any of the known variations
    if (partyData.variations.some(variation => 
        partyStr.includes(variation.toUpperCase()) || 
        variation.toUpperCase().includes(partyStr)
    )) {
      return partyData.abbreviation;
    }
  }
  
  // Fallback to first 3 characters if no match found
  const p = party.toString();
  return p ? p.substring(0, 3).toUpperCase() : '';
}

/**
 * Get full party name from abbreviation or variation
 * @param {string} party - Party name, abbreviation, or variation
 * @returns {string} Full standardized party name
 */
export function getFullPartyName(party) {
  if (!party) return '';
  
  // Handle Senate-specific party codes
  const senateToFullName = {
    'PD-IDP': 'Partito Democratico',
    'FI-BP-PPE': 'Forza Italia',
    'LSP-PS': 'Lega',
    'M5S': 'Movimento 5 Stelle',
    'F': "Fratelli d'Italia",
    'IV-C-RE': 'Italia Viva',
    'M': 'Misto',
    'A': 'Autonomie',
    'C': 'Centro'
  };
  
  // Check if it's a Senate code first
  if (senateToFullName[party]) return senateToFullName[party];
  
  const partyStr = party.toString().toUpperCase();
  
  for (const [key, partyData] of Object.entries(PARTY_MAPPINGS)) {
    // Check abbreviation
    if (partyData.abbreviation.toUpperCase() === partyStr) {
      return partyData.fullName;
    }
    
    // Check variations
    if (partyData.variations.some(variation => 
        partyStr.includes(variation.toUpperCase()) || 
        variation.toUpperCase().includes(partyStr)
    )) {
      return partyData.fullName;
    }
  }
  
  return party; // Return original if no match found
}

/**
 * Check if a search query matches a party name
 * @param {string} query - Search query
 * @param {string} partyName - Party name to check against
 * @returns {boolean} True if query matches party
 */
export function isPartyMatch(query, partyName) {
  if (!query || !partyName) return false;
  
  const queryLower = query.toLowerCase().trim();
  if (queryLower.length < 2) return false; // Avoid too short queries
  
  // Handle Senate-specific party codes first
  const senateToFullName = {
    'PD-IDP': 'Partito Democratico',
    'FI-BP-PPE': 'Forza Italia', 
    'LSP-PS': 'Lega',
    'M5S': 'Movimento 5 Stelle',
    'F': "Fratelli d'Italia",
    'IV-C-RE': 'Italia Viva',
    'M': 'Misto',
    'A': 'Autonomie',
    'C': 'Centro'
  };
  
  // Convert Senate code to full name for matching
  const fullPartyName = senateToFullName[partyName] || partyName;
  const partyStr = fullPartyName.toString().toUpperCase();
  
  for (const [key, partyData] of Object.entries(PARTY_MAPPINGS)) {
    // Check if this partyName matches any of our known parties
    const isThisParty = partyData.variations.some(variation => 
      partyStr.includes(variation.toUpperCase()) || 
      variation.toUpperCase().includes(partyStr)
    );
    
    if (isThisParty) {
      // Check if query matches any of the search keywords
      return partyData.searchKeywords.some(keyword => 
        keyword.toLowerCase().includes(queryLower) || 
        queryLower.includes(keyword.toLowerCase())
      );
    }
  }
  
  // Fallback: check against both original and full party name
  return partyName.toLowerCase().includes(queryLower) || 
         fullPartyName.toLowerCase().includes(queryLower);
}

/**
 * Get party color for styling
 * @param {string} party - Full party name
 * @returns {string} Hex color code
 */
export function getPartyColor(party) {
  // Handle Senate-specific party codes
  const senateToFullName = {
    'PD-IDP': 'Partito Democratico',
    'FI-BP-PPE': 'Forza Italia',
    'LSP-PS': 'Lega',
    'M5S': 'Movimento 5 Stelle',
    'F': "Fratelli d'Italia",
    'IV-C-RE': 'Italia Viva',
    'M': 'Misto',
    'A': 'Autonomie',
    'C': 'Centro'
  };
  
  // Convert Senate code to full name if needed
  const partyName = senateToFullName[party] || party;
  
  // WCAG AA compliant colors with sufficient contrast
  const partyColors = {
    'Partito Democratico': '#dc2626', // Red - high contrast
    'Lega': '#1d4ed8', // Blue - high contrast  
    'Movimento 5 Stelle': '#d97706', // Orange - high contrast
    'Forza Italia': '#2563eb', // Blue - high contrast
    "Fratelli d'Italia": '#1f2937', // Dark gray - high contrast
    'Italia Viva': '#7c3aed', // Purple - high contrast
    'Azione': '#059669', // Green - high contrast
    'Più Europa': '#ea580c', // Orange - high contrast
    'Alleanza Verdi e Sinistra': '#16a34a', // Green - high contrast
    'Noi Moderati': '#4b5563', // Gray - high contrast
    'Misto': '#6b7280', // Gray for mixed group
    'Autonomie': '#0891b2', // Cyan
    'Centro': '#0ea5e9' // Sky blue
  };
  return partyColors[partyName] || '#6b7280';
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