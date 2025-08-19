# 🛠️ Development Guide - Civic Bridge

## 🏗️ Architecture Overview

### Core Components

**`api_server.py`** - Main Flask application
- Web interface serving
- REST API endpoints (`/api/lookup`, `/api/autocomplete`) 
- OAuth simulation endpoints
- HTML template rendering

**`civic_lookup.py`** - Core data processing engine
- Representative matching algorithms
- Electoral district mapping
- Data loading and caching
- Location-based queries

### Data Files Structure
```
data/
├── comuni.csv                     # Italian municipalities
├── deputati_XiX.csv              # Chamber of Deputies data
├── senatori.csv                   # Senate data  
├── collegi_camera.csv             # Chamber electoral districts
├── collegi_senato.csv             # Senate electoral districts
└── meps.rdf                       # EU Parliament data
```

## 🔧 Current Implementation Status

### ✅ Working Features
- **Autocomplete**: Real-time city search with 300ms debounce
- **Representative Lookup**: Multi-institution query system
- **Email Integration**: mailto links with pre-filled templates
- **Message Composer**: Modal interface with OAuth simulation
- **Data Processing**: CSV-based government data parsing

### ⚠️ Known Limitations  
- **OAuth**: Currently simulated (shows success but doesn't send)
- **Electoral Districts**: Basic comune mapping (needs enhancement)
- **Data Freshness**: Static CSV files (need update mechanism)

## 🚀 Development Setup

### Local Development
```bash
# Start with debugging
python api_server.py

# Test autocomplete
curl "http://localhost:5000/api/autocomplete?q=roma"

# Test lookup
curl "http://localhost:5000/api/lookup?q=Milano"
```

### Key API Endpoints

**`GET /api/autocomplete?q={query}&limit={n}`**
- Returns matching cities with fuzzy search
- Response: `{success: bool, results: [...], count: int}`

**`GET /api/lookup?q={city}`** 
- Returns representatives for location
- Response: `{success: bool, representatives: {...}, location: {...}}`

**`POST /api/auth/gmail`** (Simulated)
- OAuth initiation endpoint
- Returns mock success response

**`POST /api/send-email`** (Simulated)  
- Email sending with tracking
- Accepts message data, returns tracking ID

## 🐛 Debugging Common Issues

### JavaScript Syntax Errors
- **Issue**: Italian text with apostrophes breaking string literals
- **Fix**: Use double quotes for all notification strings
- **Example**: `showNotification("Errore nell'apertura...", "error")`

### Autocomplete Not Working
- **Check**: Multiple Python processes running
- **Fix**: `taskkill /f /im python.exe` then restart

### Representative Index Errors
- **Issue**: `${i}` undefined in forEach loops
- **Fix**: Ensure `forEach((rep, i) => ...)` includes index parameter

## 📊 Data Processing Notes

### Representative Matching Algorithm
1. **Location Resolution**: City → Province → Region
2. **Electoral District Lookup**: Region/Province → Collegio
3. **Representative Filtering**: Active deputies/senators only
4. **Contact Information**: Email validation and formatting

### Current Mapping Logic
```python
# Camera: Region-based matching with collegio fallback
camera_reps = camera_df[camera_df['regione'] == location['regione']]

# Senato: Direct region mapping  
senato_reps = senato_df[senato_df['regione'] == location['regione']]

# EU: Circoscrizione (constituency) based
eu_reps = eu_df[eu_df['circoscrizione_eu'] == constituency_map[region]]
```

## 🎨 Frontend Architecture

### CSS Framework
- **Custom CSS**: No external frameworks
- **Responsive Design**: CSS Grid + Flexbox
- **Color Scheme**: Government-inspired blues and grays
- **Animations**: Subtle transitions for professional feel

### JavaScript Structure
- **No External Libraries**: Vanilla JS only
- **Modular Functions**: Separated concerns (autocomplete, lookup, composer)
- **Event Handling**: Modern addEventListener patterns
- **Error Handling**: Try-catch blocks with user notifications

### Modal System
- **Overlay Pattern**: Fixed positioning with backdrop
- **Form Validation**: Real-time input validation
- **State Management**: Global variables for current context

## 🔐 OAuth Implementation (Future)

### Required Setup
1. **Google Cloud Project**: Enable Gmail API
2. **OAuth Credentials**: Client ID/Secret configuration  
3. **Redirect URIs**: Localhost + production URLs
4. **Scope Permissions**: `gmail.send` for sending emails

### Implementation Flow
```javascript
// 1. OAuth Initiation
window.open('https://accounts.google.com/oauth/authorize?...')

// 2. Callback Handling  
const urlParams = new URLSearchParams(window.location.search);
const code = urlParams.get('code');

// 3. Token Exchange
fetch('/api/oauth/token', { body: { code } })

// 4. Gmail API Calls
fetch('https://gmail.googleapis.com/gmail/v1/users/me/messages/send')
```

## 📈 Performance Considerations

### Data Loading
- **Startup Time**: ~2-3 seconds for CSV parsing
- **Memory Usage**: ~50MB for complete dataset
- **Query Performance**: <100ms for typical lookups

### Caching Strategy
- **In-Memory**: DataFrames cached in global variables
- **Browser Caching**: Static assets cached
- **Future**: Redis for production scaling

## 🧪 Testing Strategy

### Current Testing
- **Manual Testing**: Browser-based UI testing
- **API Testing**: curl commands for endpoints
- **Data Validation**: Console logging for debugging

### Future Testing Framework
```python
# Unit Tests
pytest test_civic_lookup.py

# Integration Tests  
pytest test_api_endpoints.py

# End-to-End Tests
selenium test_user_flows.py
```

## 🚀 Deployment Considerations

### Production Requirements
- **HTTPS**: Required for OAuth and modern browsers
- **Domain Setup**: civic-bridge.it or similar
- **Server**: Python WSGI server (Gunicorn recommended)
- **Database**: Migration from CSV to PostgreSQL/SQLite

### Environment Variables
```bash
FLASK_ENV=production
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_secret
DATABASE_URL=postgresql://...
```

---

**Last Updated**: Development ongoing with Claude Code
**Next Priority**: Electoral district mapping enhancement