# OAuth Email Sending Implementation Plan

## Current State Analysis
The OAuth option in the composer is currently a placeholder that shows "Invio tramite OAuth non ancora implementato" alert.

## Option 1: Google Gmail API OAuth (Recommended)
**Steps Required:**
1. **Google Cloud Console Setup**
   - Create/configure Google Cloud Project
   - Enable Gmail API
   - Create OAuth 2.0 client credentials (web application)
   - Configure authorized redirect URIs

2. **Backend OAuth Flow Implementation**
   - Add OAuth endpoints: `/auth/google/start`, `/auth/google/callback`
   - Handle authorization code exchange for access tokens
   - Securely store refresh tokens (database or encrypted storage)
   - Implement token refresh logic

3. **Gmail API Integration**
   - Add Gmail API client library (google-api-python-client)
   - Implement email sending via Gmail API
   - Handle API errors and rate limits
   - Support HTML and plain text emails

4. **Frontend Integration**
   - Replace placeholder with actual OAuth initiation
   - Handle OAuth popup/redirect flow
   - Show authentication status to user
   - Graceful error handling

## Option 2: Microsoft Outlook OAuth (Alternative)
Similar steps but using Microsoft Graph API instead of Gmail API.

## Option 3: Generic SMTP with OAuth2 (Most Complex)
Support multiple providers using OAuth2 for SMTP authentication.

## Security Considerations
- Store client secrets securely (environment variables)
- Use HTTPS for all OAuth flows
- Implement CSRF protection
- Securely store user tokens
- Handle token expiration/refresh

## Implementation Details

### Google Cloud Console Setup
1. Go to https://console.cloud.google.com/
2. Create new project or select existing one
3. Enable Gmail API in API Library
4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
5. Configure application type as "Web application"
6. Add authorized redirect URIs: `http://localhost:5000/auth/google/callback`
7. Save client ID and client secret

### Backend Flask Routes Needed
```python
@app.route('/auth/google/start')
def google_auth_start():
    # Redirect user to Google OAuth consent screen

@app.route('/auth/google/callback')  
def google_auth_callback():
    # Handle callback, exchange code for tokens
    
@app.route('/api/send-email', methods=['POST'])
def send_email_oauth():
    # Send email using stored OAuth tokens
```

### Frontend Changes Required
- Update composer-new.js `handleSend()` function
- Add OAuth flow initiation
- Handle authentication status
- Show user which email account is connected

### Database Schema (if using database storage)
```sql
CREATE TABLE oauth_tokens (
    id INTEGER PRIMARY KEY,
    user_session VARCHAR(255),
    provider VARCHAR(50),
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    email_address VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Required Python Dependencies
```
google-auth==2.24.0
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.108.0
```

### Environment Variables Needed
```
GOOGLE_OAUTH_CLIENT_ID=your_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret
OAUTH_REDIRECT_URI=http://localhost:5000/auth/google/callback
```

## Recommended Implementation Order
1. Start with Gmail OAuth (most common)
2. Test with single user first  
3. Add user management if needed
4. Consider adding Outlook support later

## Testing Strategy
1. Test OAuth flow with personal Gmail account
2. Test email sending functionality
3. Test token refresh logic
4. Test error handling (invalid tokens, API limits)
5. Test with different email content types

## Alternative: Simpler SMTP Approach
Instead of full OAuth, could implement:
- Simple SMTP with app-specific passwords
- User provides their own SMTP credentials
- Less secure but much simpler to implement

## Next Steps
When ready to implement:
1. Choose Gmail OAuth approach
2. Set up Google Cloud Console project
3. Add required dependencies to requirements.txt
4. Implement backend OAuth flow
5. Update frontend composer functionality
6. Test end-to-end functionality

---
*Plan created: 2025-01-28*
*Status: Not implemented*