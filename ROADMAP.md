# 🗺️ Civic Bridge - Work Breakdown Structure & Roadmap

## **Phase 1: Electoral District Mapping Enhancement**

### 1.1 Data Research & Analysis
- **1.1.1** Research official Italian electoral district data sources
- **1.1.2** Download and analyze current collegio elettorale datasets
- **1.1.3** Map data structure differences between Camera/Senato districts
- **1.1.4** Identify gaps in current comune → collegio mapping

### 1.2 Data Integration
- **1.2.1** Create enhanced collegio mapping tables
- **1.2.2** Build comune → collegio → representative lookup chains
- **1.2.3** Update CSV processing in civic_lookup.py
- **1.2.4** Add collegio information to API responses

### 1.3 Algorithm Enhancement
- **1.3.1** Modify representative matching to use district-first approach
- **1.3.2** Add fallback logic for unmapped comuni
- **1.3.3** Validate accuracy improvements with test cases
- **1.3.4** Update API documentation for new data fields

---

## **Phase 2: UI/UX Improvements**

### 2.1 Category Organization
- **2.1.1** Group representatives by institution (Camera/Senato/EU)
- **2.1.2** Add section headers with counts
- **2.1.3** Implement collapsible/expandable sections
- **2.1.4** Add "Show All" / "Show Less" functionality

### 2.2 Filtering & Navigation
- **2.2.1** Create institution filter buttons (Camera/Senato/EU toggle)
- **2.2.2** Add "Select All" / "Deselect All" options
- **2.2.3** Implement search within results
- **2.2.4** Add sorting options (name, party, district)

### 2.3 Visual Enhancements
- **2.3.1** Research official representative photo sources
- **2.3.2** Integrate headshot images into representative cards
- **2.3.3** Add party logos/colors where appropriate
- **2.3.4** Improve mobile responsive design
- **2.3.5** Add loading states and skeleton screens

---

## **Phase 3: Pre-defined Email Themes**

### 3.1 Template Development
- **3.1.1** Research common citizen advocacy topics
- **3.1.2** Create template library structure
- **3.1.3** Write professional Italian templates for:
  - Embargo/Trade sanctions
  - Humanitarian corridors
  - Environmental issues
  - Economic policies
  - Healthcare matters
  - Immigration policy
  - EU affairs

### 3.2 Template Integration
- **3.2.1** Add theme selection dropdown to message composer
- **3.2.2** Implement dynamic template loading
- **3.2.3** Create template customization interface
- **3.2.4** Add template preview functionality

### 3.3 Smart Suggestions
- **3.3.1** Logic for suggesting relevant templates based on representative type
- **3.3.2** Add context-aware recipient suggestions
- **3.3.3** Template personalization based on location/district

---

## **Phase 4: User Authentication System**

### 4.1 Basic Authentication
- **4.1.1** Design simple email/password registration
- **4.1.2** Implement login/logout functionality
- **4.1.3** Add password reset capability
- **4.1.4** Create user profile management

### 4.2 Data Persistence
- **4.2.1** Design user data schema
- **4.2.2** Implement user session management
- **4.2.3** Create contact history storage
- **4.2.4** Add draft message saving

### 4.3 User Experience
- **4.3.1** Add optional account creation flow
- **4.3.2** Implement "Remember me" functionality
- **4.3.3** Create user dashboard interface
- **4.3.4** Add privacy settings and data controls

---

## **Phase 5: Contact Tracking & Analytics**

### 5.1 Tracking Infrastructure
- **5.1.1** Design contact event data model
- **5.1.2** Implement contact logging system
- **5.1.3** Add representative interaction markers
- **5.1.4** Create basic analytics collection

### 5.2 User-Facing Features
- **5.2.1** Add "Already Contacted" indicators on representative cards
- **5.2.2** Create user contact history page
- **5.2.3** Implement contact frequency warnings/suggestions
- **5.2.4** Add follow-up reminder system

### 5.3 Analytics Dashboard
- **5.3.1** Create personal engagement statistics
- **5.3.2** Add most-contacted representatives
- **5.3.3** Show contact success rates (when available)
- **5.3.4** Generate periodic engagement reports

---

## **Phase 6: OAuth Implementation**

### 6.1 OAuth Infrastructure
- **6.1.1** Set up Google Cloud Project and APIs
- **6.1.2** Configure OAuth credentials and scopes
- **6.1.3** Implement OAuth redirect flow
- **6.1.4** Add token storage and refresh logic

### 6.2 Email Integration
- **6.2.1** Replace simulated Gmail API with real implementation
- **6.2.2** Add Microsoft Graph API for Outlook integration
- **6.2.3** Implement email sending with proper error handling
- **6.2.4** Add send confirmation and delivery tracking

### 6.3 Production Readiness
- **6.3.1** Add OAuth consent screen configuration
- **6.3.2** Implement proper error handling and user feedback
- **6.3.3** Add rate limiting and API quota management
- **6.3.4** Test with real email accounts and recipients

---

## **📊 Effort Estimates**

| Phase | Tasks | Estimated Days | Priority |
|-------|-------|---------------|----------|
| Phase 1 | 12 tasks | 7-10 days | **High** |
| Phase 2 | 12 tasks | 8-12 days | **High** |
| Phase 3 | 9 tasks | 5-7 days | **Medium** |
| Phase 4 | 11 tasks | 10-14 days | **Medium** |
| Phase 5 | 10 tasks | 8-12 days | **Medium** |
| Phase 6 | 12 tasks | 5-8 days | **Low** |

**Total Estimated Effort: 43-63 days**

---

## **🎯 Success Metrics**

### Phase 1 - Electoral District Mapping
- **Accuracy**: >95% representative matching accuracy
- **Coverage**: All Italian comuni mapped to correct collegi
- **Data Quality**: Zero unmapped representatives
- **API Response**: <100ms lookup time maintained

### Phase 2 - UI/UX Improvements  
- **Performance**: <2 seconds initial page load
- **Mobile**: Fully responsive on all screen sizes
- **Usability**: <3 clicks to contact any representative
- **Accessibility**: WCAG 2.1 AA compliance

### Phase 3 - Email Templates
- **Content**: 7+ professional Italian templates
- **Usage**: <1 minute from template selection to send
- **Quality**: Professional tone, proper Italian formatting
- **Personalization**: Dynamic content based on location/representative

### Phase 4 - User Authentication
- **Security**: Secure password hashing, session management
- **UX**: Optional registration, no forced signup
- **Data**: Persistent contact history for registered users
- **Privacy**: GDPR-compliant data handling

### Phase 5 - Contact Tracking
- **Visibility**: Clear indicators for contacted representatives
- **History**: Complete contact timeline for users
- **Analytics**: Personal engagement insights
- **Insights**: Contact success patterns and suggestions

### Phase 6 - OAuth Implementation
- **Integration**: Real Gmail and Outlook API functionality
- **Reliability**: >95% email delivery success rate
- **Security**: Proper OAuth 2.0 implementation
- **UX**: Seamless authentication flow

---

## **🚀 Implementation Strategy**

### Immediate Priority (Weeks 1-4)
- **Phase 1**: Electoral district mapping enhancement
- **Phase 2.1**: Basic UI improvements (grouping, sections)

### Short Term (Weeks 5-8)
- **Phase 2.2-2.3**: Advanced UI features (filtering, photos)
- **Phase 3.1**: Template development

### Medium Term (Weeks 9-16)
- **Phase 3.2-3.3**: Template integration
- **Phase 4**: User authentication system

### Long Term (Weeks 17-20+)
- **Phase 5**: Contact tracking and analytics
- **Phase 6**: OAuth implementation

---

## **📋 Development Notes**

### Dependencies
- **Phase 4 → Phase 5**: User authentication required for tracking
- **Phase 1 → All**: Better data foundation improves all features
- **Phase 2**: Independent, can be done in parallel

### Risk Mitigation
- **Phase 1**: Validate data sources early to avoid rework
- **Phase 4**: Plan GDPR compliance from the start
- **Phase 6**: Test OAuth with small user group first

### MVP Decisions
- **Current system already functional** - no pressure for rushed implementation
- **Phase 1 has highest impact** on core functionality
- **Phase 6 can be delayed** if OAuth complexity becomes blocking

---

**Last Updated**: Development roadmap created with Claude Code  
**Next Action**: Begin Phase 1.1 - Research electoral district data sources