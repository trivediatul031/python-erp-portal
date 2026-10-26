# Microsoft Entra ID SSO Implementation - Requirements Document

## Summary

Replace the existing Flask-Login username/password form authentication in the ERP Travel Request (TR) Portal with Microsoft Entra ID (Azure AD) Single Sign-On (SSO) using OAuth2 authorization code flow. The authenticated user's email will be matched against the Employee table to establish identity and role-based access. All existing functionality, routes, dashboards, and role-based authorization must remain intact.

**Key Context:**
- Azure AD application already registered with:
  - Tenant ID: `e675c809-45cb-45e7-bdee-08c8772f0cf3`
  - Client ID: `c1aef541-a3eb-439c-a9b9-92d5f1226720`
  - Client Secret: **NOT yet provided** (must be obtained from Azure Portal and stored in environment variable)
- Current authentication: Flask-Login with User model (username/password_hash stored in database)
- User identity resolution: User.emp_id → Employee.email
- Role-based access: admin vs employee routes protected by decorators
- Database: SQLite (development) with existing User and Employee tables

## Functional Requirements

### FR1: Microsoft Entra ID OAuth2 Integration

**FR1.1** Integrate MSAL for Python (Microsoft Authentication Library) to implement OAuth2 authorization code flow with Microsoft Entra ID.

**FR1.2** Support both development (localhost) and production environments with environment-driven redirect URI configuration:
- Development: `http://localhost:5000/auth/callback`
- Production: configured via `AZURE_REDIRECT_URI` environment variable

**FR1.3** Use the provided tenant-specific authority URL: `https://login.microsoftonline.com/e675c809-45cb-45e7-bdee-08c8772f0cf3`

**FR1.4** Request the following OAuth2 scopes:
- `User.Read` (to retrieve authenticated user's profile including email)
- `openid` (for OpenID Connect authentication)
- `profile` (for basic profile information)
- `email` (for email claim in ID token)

**FR1.5** Store and retrieve OAuth2 tokens securely in Flask session storage with appropriate encryption using Flask's SECRET_KEY.

### FR2: Login Flow Replacement

**FR2.1** Replace the existing username/password login form in `app/templates/login.html` with a "Sign in with Microsoft" button that initiates the OAuth2 authorization flow.

**FR2.2** The "Sign in with Microsoft" button should:
- Use Microsoft branding guidelines (official button style/colors)
- Display clearly as the primary authentication method
- Redirect to Microsoft Entra ID login page when clicked

**FR2.3** Implement OAuth2 callback handler at route `/auth/callback` that:
- Receives the authorization code from Microsoft
- Exchanges the authorization code for access token and ID token
- Validates the ID token signature and claims
- Extracts the authenticated user's email address

**FR2.4** Extract the user's email address using one of the following methods (design must choose):
- **Option A:** Parse the `preferred_username` or `email` claim from the ID token (faster, no additional API call)
- **Option B:** Call Microsoft Graph API `/me` endpoint using the access token (more reliable, requires network call)

**FR2.5** Handle the case where a user is already logged in:
- If accessing `/login` while authenticated, redirect to the appropriate role-based dashboard
- No duplicate login sessions

### FR3: User Identity Resolution and Authorization

**FR3.1** After successful Microsoft authentication, match the authenticated email against the `Employee` table's `email` column to resolve the employee identity.

**FR3.2** If no matching employee record is found:
- Deny access with a clear, user-friendly error message: "Your Microsoft account is not associated with an employee record. Please contact your system administrator."
- Log the failed authentication attempt with email and timestamp
- Do NOT create a user session
- Provide a "Try Again" or "Back to Login" option

**FR3.3** If a matching employee record is found:
- Retrieve the employee's `emp_id`
- Check if a corresponding `User` record exists in the `users` table with matching `emp_id`
- If User record exists and `is_active=True`:
  - Load the existing User record
  - Create Flask-Login session using `login_user()`
  - Preserve the user's existing `role` (admin or employee)
- If User record exists but `is_active=False`:
  - Deny access with message: "Your account is inactive. Please contact your system administrator."
  - Log the failed attempt
- If no User record exists (design must decide):
  - **Option A:** Auto-create a User record with role='employee', is_active=True, username=email, password_hash='SSO' (placeholder)
  - **Option B:** Deny access and require admin to pre-create user accounts
  - **Recommendation:** Option A for better user experience

**FR3.4** Maintain the existing role-based access control:
- Admin users access admin routes (`/admin/*`) protected by `@admin_required`
- Employee users access employee routes (`/employee/*`) protected by `@employee_required`
- Flask-Login's `@login_required` decorator continues to protect all authenticated routes
- `current_user` object remains populated with User model attributes (user_id, role, emp_id, etc.)

**FR3.5** The User model's `user_id` must remain the primary identifier for Flask-Login sessions (no changes to `get_id()` method).

### FR4: Security and Secrets Management

**FR4.1** All Azure AD credentials and application secrets must be stored exclusively in environment variables:
- `AZURE_TENANT_ID`: e675c809-45cb-45e7-bdee-08c8772f0cf3
- `AZURE_CLIENT_ID`: c1aef541-a3eb-439c-a9b9-92d5f1226720
- `AZURE_CLIENT_SECRET`: **Must be obtained from Azure Portal** (App registration → Certificates & secrets → New client secret)
- `AZURE_REDIRECT_URI`: Full callback URL for production deployment

**FR4.2** Never hardcode secrets in source code, configuration files, or version control.

**FR4.3** Validate that all required Azure environment variables are present at application startup; raise a clear error if missing in production mode.

**FR4.4** Continue using existing Flask security mechanisms:
- CSRF protection via Flask-WTF (ensure CSRF tokens work with SSO flow)
- Secure session cookies (`SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SECURE` in production)
- Rate limiting via Flask-Limiter on authentication endpoints

**FR4.5** OAuth2 state parameter must be used to prevent CSRF attacks during the authorization flow:
- Generate a random state value before redirecting to Microsoft
- Store state in Flask session
- Validate state parameter matches on callback

**FR4.6** Token handling security:
- Access tokens and refresh tokens stored in server-side Flask session (not cookies)
- Tokens should not be logged or exposed in error messages
- Token expiration should be handled gracefully

**FR4.7** Preserve the existing `username` and `password_hash` columns in the User table:
- Do NOT drop these columns (potential future fallback mechanism)
- SSO users can have placeholder values (e.g., username=email, password_hash='SSO_AUTH')

### FR5: Authentication Logging and Auditing

**FR5.1** Log every authentication attempt (success and failure) with the following details:
- Timestamp (ISO 8601 format)
- Event type: AUTH_SUCCESS or AUTH_FAILURE
- Authenticated email address
- User's IP address
- Status: success or failure
- Reason: brief explanation (e.g., "employee not found", "account inactive", "successful login")
- Username/User ID if session created

**FR5.2** Log format must be structured for easy parsing:
```
[2024-01-15T10:30:45] [AUTH] email=user@company.com ip=192.168.1.100 status=success user_id=42 role=employee reason=authenticated via Microsoft SSO
[2024-01-15T10:31:12] [AUTH] email=unknown@external.com ip=192.168.1.101 status=failure reason=employee not found in database
```

**FR5.3** Authentication logs must be written to (design must choose):
- **Option A:** Dedicated database table `auth_logs` with columns: id, timestamp, email, ip_address, status, reason, user_id, role
- **Option B:** Application log file `logs/auth.log` with structured format
- **Option C:** Both database table and log file for redundancy
- **Recommendation:** Option C for production readiness

**FR5.4** Log retention: authentication logs should be retained for at least 90 days for security auditing purposes (design must specify mechanism).

**FR5.5** Failed login attempts from the same IP should be monitored for potential brute-force attacks (leverage existing Flask-Limiter or add additional tracking).

### FR6: Logout Functionality

**FR6.1** Update the `/logout` route to:
- Clear the Flask session completely (`session.clear()`)
- Call Flask-Login's `logout_user()`
- Optionally redirect to Microsoft's logout endpoint to clear Azure AD session

**FR6.2** Microsoft logout redirect URL (design must decide):
- **Option A:** Full sign-out from Microsoft: `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/logout?post_logout_redirect_uri={encoded_app_url}`
- **Option B:** Local logout only (faster but Microsoft session remains active)
- **Recommendation:** Option A for complete sign-out

**FR6.3** After logout, redirect user to the login page with a success message: "You have been successfully logged out."

**FR6.4** Ensure logout is not CSRF-protected (or use GET method) to avoid logout failures.

### FR7: Preserve Existing Functionality

**FR7.1** ALL existing routes must continue to work without modification:
- Admin routes: `/admin/dashboard`, `/admin/employee_list`, `/admin/tas_list`, `/admin/tas_detail/<id>`, `/admin/user_management`, etc.
- Employee routes: `/employee/dashboard`, `/employee/submit-tas`, `/employee/tas-history`, `/employee/tas/<id>`
- Root route `/` redirect logic based on authentication state

**FR7.2** All existing decorators must continue to function:
- `@login_required` (Flask-Login)
- `@admin_required` (app/auth.py)
- `@employee_required` (app/auth.py)

**FR7.3** The `current_user` proxy object must remain fully compatible with existing template and route code:
- `current_user.is_authenticated`
- `current_user.role`
- `current_user.emp_id`
- `current_user.username`
- `current_user.employee_profile` relationship

**FR7.4** All existing templates must continue to work:
- Dashboard templates (admin/dashboard.html, employee/dashboard.html)
- Form templates (employee/submit_tas.html)
- Base template header/navigation logic

**FR7.5** Database models must remain unchanged except for the login.html template and auth routes:
- User model: keep all columns including username and password_hash
- Employee model: no changes
- TASRecord model: no changes

**FR7.6** Flask extensions must continue to work:
- Flask-Login
- Flask-WTF (CSRF protection)
- Flask-Limiter (rate limiting)
- Flask-SQLAlchemy

### FR8: Error Handling

**FR8.1** Handle Microsoft Entra ID authentication failures:
- User cancels login at Microsoft page → redirect to login page with message "Authentication cancelled"
- Invalid credentials at Microsoft → Microsoft handles; if callback receives error parameter, display "Authentication failed. Please try again."
- Network timeout reaching Microsoft → display "Unable to connect to Microsoft authentication service. Please try again later."

**FR8.2** Handle token-related errors:
- Invalid authorization code → display "Authentication session expired. Please try again."
- Expired access token → use refresh token to obtain new access token automatically, or re-authenticate
- Token validation failure → log error and display "Authentication failed. Please contact support."

**FR8.3** Handle employee matching errors:
- Email not found in Employee table → clear message: "Your Microsoft account ({email}) is not associated with an employee record. Contact your administrator."
- Multiple employees with same email (data integrity issue) → log error, display generic message, notify admin

**FR8.4** Handle session and state errors:
- Missing or invalid OAuth state parameter → log potential CSRF attack, display "Invalid authentication request"
- Session expired during OAuth flow → redirect to login with message "Session expired. Please try again."

**FR8.5** All errors should:
- Display user-friendly messages (no stack traces or technical details)
- Log detailed technical information server-side for debugging
- Provide actionable next steps ("Try again", "Contact support")

**FR8.6** Ensure error pages respect the existing base template styling.

### FR9: Environment Configuration

**FR9.1** Support environment-based configuration via `FLASK_ENV` environment variable:
- `development`: use localhost redirect URI, enable debug logging, allow HTTP
- `production`: use production redirect URI, require HTTPS, validate all secrets

**FR9.2** Add new configuration variables to `config.py`:
- `AZURE_TENANT_ID`
- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_REDIRECT_URI`
- `AZURE_AUTHORITY` (derived from tenant ID)
- `AZURE_SCOPE` (list of scopes to request)

**FR9.3** Update `.env.example` with all required Azure AD variables and clear comments explaining:
- How to obtain each value from Azure Portal
- Example values (placeholders)
- Which values are secret vs. configuration

**FR9.4** Provide clear validation messages if required Azure variables are missing:
```python
if not AZURE_CLIENT_SECRET:
    raise ValueError("AZURE_CLIENT_SECRET must be set in environment variables. Obtain from Azure Portal: App registration → Certificates & secrets → New client secret")
```

### FR10: Documentation and Setup Instructions

**FR10.1** Create or update README section covering:
- Azure AD app registration prerequisites
- Required redirect URIs to configure in Azure Portal
- How to obtain the Client Secret from Azure Portal (step-by-step)
- Environment variable configuration
- Development vs. production setup differences

**FR10.2** Document the authentication flow for developers:
- User clicks "Sign in with Microsoft"
- Redirect to Microsoft login page
- User authenticates with Microsoft credentials
- Microsoft redirects to callback with authorization code
- Application exchanges code for tokens
- Application validates tokens and extracts email
- Application matches email to Employee record
- Application creates/loads User record and Flask session

**FR10.3** Include troubleshooting guide for common issues:
- "Employee not found" → ensure employee email in database matches Microsoft account email
- Authentication callback errors → verify redirect URI matches Azure configuration exactly
- Token validation failures → check system time synchronization

**FR10.4** Provide testing instructions:
- How to test SSO flow in localhost
- How to verify employee matching
- How to test role-based access after SSO login

## Non-Functional Requirements

### NFR1: Performance

- OAuth2 token exchange should complete within 3 seconds under normal network conditions
- Email-to-employee lookup query should use database index on Employee.email column
- Session loading should not add more than 100ms overhead vs. existing authentication

### NFR2: Compatibility

- Must work with Microsoft Entra ID (Azure AD) single-tenant configuration
- Must support modern browsers (Chrome, Firefox, Edge, Safari)
- Must work on both Windows and Linux servers
- Must support both HTTP (development) and HTTPS (production)

### NFR3: Maintainability

- Authentication logic should be modular and separated from route handlers
- Configuration should follow 12-factor app principles (environment variables)
- Code should follow existing project structure and style conventions
- Logging should use Python's standard logging module

### NFR4: Security

- All authentication flows must use HTTPS in production
- OAuth2 state parameter must prevent CSRF attacks
- Tokens must be stored securely (server-side session, not client cookies)
- Failed login attempts must be rate-limited (leverage existing Flask-Limiter)
- Authentication logs must not contain passwords or tokens

## Acceptance Criteria

### AC1: Microsoft SSO Login Flow
1. Navigating to `/login` displays a "Sign in with Microsoft" button (no username/password form)
2. Clicking "Sign in with Microsoft" redirects to Microsoft Entra ID login page
3. After successful authentication at Microsoft, user is redirected back to `/auth/callback`
4. Callback handler successfully exchanges authorization code for access token
5. User's email is extracted from token or Microsoft Graph API
6. User is redirected to appropriate dashboard (admin or employee based on role)

### AC2: Employee Identity Resolution
7. Employee with email `john.doe@company.com` in Employee table can successfully authenticate with matching Microsoft account
8. Employee not found in database receives error message: "Your Microsoft account is not associated with an employee record"
9. Inactive employee (is_active=False) receives error message: "Your account is inactive"
10. Employee with existing User record maintains their assigned role (admin vs employee)
11. Employee without User record has User record auto-created with role='employee' (if Option A chosen)

### AC3: Role-Based Access Control
12. Employee-role user can access `/employee/dashboard` after SSO login
13. Employee-role user receives 403 Forbidden when accessing `/admin/dashboard`
14. Admin-role user can access `/admin/dashboard` after SSO login
15. Admin-role user can access all admin routes after SSO login
16. `@login_required`, `@admin_required`, and `@employee_required` decorators work identically to before

### AC4: Session Management
17. Flask-Login session is created successfully after SSO authentication
18. `current_user.is_authenticated` returns True after successful login
19. `current_user.role` returns correct role (admin or employee)
20. `current_user.emp_id` returns correct employee ID
21. `current_user.employee_profile` relationship loads Employee data correctly

### AC5: Security and Secrets
22. All Azure credentials (TENANT_ID, CLIENT_ID, CLIENT_SECRET) loaded from environment variables only
23. No secrets hardcoded in Python files or templates
24. Application raises clear error on startup if AZURE_CLIENT_SECRET is missing in production
25. OAuth2 state parameter is validated on callback (invalid state rejected)
26. CSRF protection continues to work on non-auth forms

### AC6: Authentication Logging
27. Successful login logs entry with format: `[TIMESTAMP] [AUTH] email=user@company.com ip=X.X.X.X status=success user_id=42 role=employee`
28. Failed login (employee not found) logs entry with status=failure and reason
29. Failed login (inactive account) logs entry with status=failure and reason
30. All authentication log entries include timestamp, email, IP address, status, and reason
31. Authentication logs are written to file/database (per design decision)

### AC7: Logout Functionality
32. Clicking logout clears Flask session completely
33. After logout, user is redirected to login page
34. After logout, attempting to access protected route redirects to login
35. If Microsoft logout is implemented, Azure AD session is also cleared

### AC8: Error Handling
36. User cancels Microsoft login → redirected to login page with appropriate message
37. Network error during token exchange → user-friendly error message displayed
38. Invalid/expired authorization code → user-friendly error message displayed
39. Employee email not found → clear message with email address shown
40. All errors display user-friendly messages (no stack traces visible)

### AC9: Existing Functionality Preservation
41. All admin routes continue to work after SSO implementation
42. All employee routes continue to work after SSO implementation
43. TAS submission form works identically for SSO-authenticated employees
44. Admin dashboard statistics load correctly after SSO login
45. Employee dashboard shows correct TAS records after SSO login
46. All existing templates render without errors
47. Database schema remains unchanged (User and Employee tables intact)

### AC10: Configuration and Documentation
48. `.env.example` includes all Azure AD variables with clear comments
49. README includes section on Azure AD app registration steps
50. README documents how to obtain Client Secret from Azure Portal
51. README includes troubleshooting guide for common SSO issues
52. Configuration validates required variables and provides helpful error messages
53. Both development (localhost) and production redirect URIs are supported

### AC11: Development and Production Support
54. Application works in development mode with `http://localhost:5000/auth/callback`
55. Application supports production mode with configurable redirect URI
56. Environment variable `FLASK_ENV` controls development vs production behavior
57. HTTPS is enforced in production mode
58. Debug logging is enabled in development mode

## Out of Scope

The following items are explicitly **not** part of this implementation:

1. **Multi-factor authentication (MFA)** - Handled by Microsoft Entra ID configuration, not application code
2. **Azure AD group-based role assignment** - Role (admin vs employee) is determined by existing User.role column, not Azure AD groups
3. **Self-service employee registration** - Employees must exist in Employee table before SSO login
4. **Fallback to username/password login** - Completely replacing form login; no hybrid auth mode
5. **Password reset functionality** - Not applicable with SSO; handled by Microsoft
6. **Remember me / persistent login** - Session lifetime controlled by Flask configuration
7. **OAuth2 refresh token rotation** - Initial implementation uses access token only; refresh tokens optional
8. **Multi-tenant Azure AD support** - Single tenant only (provided tenant ID)
9. **Azure AD B2C** - Using Azure AD (Entra ID), not B2C variant
10. **Guest user authentication** - Only employees in the Employee table can authenticate
11. **API authentication (Bearer tokens)** - Web application authentication only
12. **Migration of existing password hashes** - Existing User records retained but passwords not migrated
13. **Automated testing for SSO flow** - Manual testing required (OAuth2 mocking is complex)
14. **User profile synchronization from Azure AD** - Employee data managed in local database only
15. **Audit log UI** - Authentication logs written to file/database but no admin UI to view them

## Open Design Decisions

The design phase must resolve the following decisions explicitly:

### Decision 1: Email Extraction Method
- **Option A:** Parse `email` or `preferred_username` claim from ID token (faster, no API call)
- **Option B:** Call Microsoft Graph API `/me` endpoint with access token (more reliable)
- **Consideration:** Check which claim is reliably present in ID token for single-tenant app

### Decision 2: User Record Auto-Creation
- **Option A:** Auto-create User record when Employee exists but User does not (better UX)
- **Option B:** Require admin to pre-create User records (tighter control)
- **Consideration:** How many existing employees lack User records?

### Decision 3: Authentication Logging Storage
- **Option A:** Database table `auth_logs` (queryable, structured)
- **Option B:** Log file `logs/auth.log` (simpler, no schema changes)
- **Option C:** Both (redundancy, best for production)
- **Consideration:** Does project need audit log reporting features?

### Decision 4: Microsoft Logout Behavior
- **Option A:** Full sign-out from Microsoft (clears Azure AD session)
- **Option B:** Local logout only (faster, but Microsoft session persists)
- **Consideration:** Are users on shared computers or personal devices?

### Decision 5: Token Storage Strategy
- **Option A:** Store access token in Flask session (simple, works for short-lived tokens)
- **Option B:** Store access token + refresh token (supports longer sessions)
- **Consideration:** What is the expected user session lifetime?

### Decision 6: CSRF Exemption for OAuth Callback
- **Option A:** Exempt `/auth/callback` from CSRF protection (OAuth state parameter provides CSRF protection)
- **Option B:** Keep CSRF protection and ensure compatibility with OAuth flow
- **Consideration:** Does Flask-WTF CSRF interfere with POST-based OAuth callbacks?

### Decision 7: Rate Limiting on SSO Routes
- **Option A:** Apply existing Flask-Limiter rules to `/auth/callback`
- **Option B:** More lenient limits on callback (user already rate-limited at Microsoft)
- **Consideration:** Prevent callback abuse vs. allow legitimate retries

### Decision 8: Session Timeout After SSO Login
- **Option A:** Keep existing 1-hour session timeout (`PERMANENT_SESSION_LIFETIME = 3600`)
- **Option B:** Extend session timeout since re-authentication is via Microsoft (e.g., 8 hours)
- **Consideration:** Balance between security and user convenience

## Assumptions

1. All employees who should access the system have valid Microsoft accounts (Azure AD identities)
2. Employee email addresses in the database match their Microsoft account email addresses exactly (case-insensitive)
3. Azure AD app registration has been completed and the provided Tenant ID and Client ID are correct
4. The system administrator has access to Azure Portal to obtain the Client Secret
5. Redirect URIs will be configured in Azure Portal to match the application's callback URL
6. The application runs behind a reverse proxy or load balancer that terminates SSL in production
7. The Employee table's email column is unique and has an index for performance
8. Existing User records will not be deleted; username/password columns retained for potential future use
9. Network connectivity to Microsoft's authentication endpoints is reliable
10. System clock is synchronized (NTP) for accurate token expiration validation

## Dependencies

### New Python Packages Required
- `msal==1.26.0` - Microsoft Authentication Library for Python

### Updated Packages (if needed)
- No updates to existing packages expected

### Azure AD App Registration Requirements
- Application must have redirect URIs configured
- API permissions: `User.Read` (Microsoft Graph, Delegated)
- Client secret must be generated and not expired
- Single-tenant configuration (no multi-tenant support needed)

### Environment Variables Required
- `AZURE_TENANT_ID` (provided: e675c809-45cb-45e7-bdee-08c8772f0cf3)
- `AZURE_CLIENT_ID` (provided: c1aef541-a3eb-439c-a9b9-92d5f1226720)
- `AZURE_CLIENT_SECRET` (to be obtained from Azure Portal)
- `AZURE_REDIRECT_URI` (for production deployment)
- `FLASK_ENV` (existing, controls dev vs prod)
- `SECRET_KEY` (existing, used for session encryption)

### Database Requirements
- Employee table must have `email` column (exists)
- Employee.email must be unique and indexed (verify during design)
- User table remains unchanged (no schema migration)
- Optional: new `auth_logs` table if database logging chosen

### External Services
- Microsoft Entra ID (Azure AD) authentication endpoints
- Microsoft Graph API (if email extraction via Graph chosen)
- Network connectivity to `login.microsoftonline.com`

---

**Document Version:** 1.0  
**Date:** 2024-01-15  
**Prepared for:** Microsoft Entra ID SSO Implementation - Design Phase
