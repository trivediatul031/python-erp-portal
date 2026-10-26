# Microsoft Entra ID SSO Implementation Plan

**Implementation Order:** Sequential by dependency  
**Worktree:** c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso  
**Branch:** feature/entra-sso  
**Design Document:** sso-design.md (Revision 3)  
**Requirements:** sso-requirements.md v1.0

---

## Implementation Steps

- [ ] 1. **Add MSAL dependency to requirements.txt**
      
      Add the exact version specified in the design: `msal==1.26.0`
      
      **Files:**
      - c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso\requirements.txt
      
      **Verify:** Run `pip install -r requirements.txt` and confirm msal==1.26.0 installs without errors; then run `python -c "import msal; print(msal.__version__)"` and confirm output is `1.26.0`

---

- [ ] 2. **Update config.py with Azure AD configuration and validation**
      
      Add `import re` at the top of config.py. In the `Config` base class, add Azure AD environment variables (AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, APP_URL), derive AZURE_AUTHORITY from tenant ID, define AZURE_SCOPE list, and add configurable rate limit variables (LOGIN_RATE_LIMIT, AUTH_INITIATE_RATE_LIMIT, AUTH_CALLBACK_RATE_LIMIT) with defaults. In `ProductionConfig.init_app()`, add comprehensive validation: check all required Azure variables are present; validate tenant and client IDs are valid UUIDs using regex; validate client secret is at least 32 characters; validate APP_URL starts with http:// or https://; warn if APP_URL uses HTTP (except localhost).
      
      **Pattern from design:** The exact validation code is in sso-design.md under "Configuration Design > Startup Validation".
      
      **Files:**
      - c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso\config.py
      
      **Verify:** Run `python -c "from config import config; c=config['production']; print('AZURE_AUTHORITY:', c.AZURE_AUTHORITY, 'SCOPE:', c.AZURE_SCOPE)"` and confirm authority URL contains tenant ID and scope list has 4 items; then set FLASK_ENV=production with missing AZURE_CLIENT_SECRET and confirm app startup raises ValueError with clear message

---

- [ ] 3. **Compute AZURE_REDIRECT_URI in app/__init__.py at app initialization**
      
      In `create_app()` function, immediately after `app.config.from_object(config[config_name])`, add code to compute AZURE_REDIRECT_URI from APP_URL and store in app.config. Pattern: `app_url = app.config.get('APP_URL'); if app_url: app.config['AZURE_REDIRECT_URI'] = f"{app_url.rstrip('/')}/auth/Microsoft/callback"; else: app.config['AZURE_REDIRECT_URI'] = None`. This resolves Finding #3 (properties don't work as config values).
      
      **Files:**
      - c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso\app\__init__.py
      
      **Verify:** Run `python -c "from app import create_app; app = create_app(); print('Redirect URI:', app.config.get('AZURE_REDIRECT_URI'))"` with APP_URL=http://localhost:5000 in .env and confirm output is `http://localhost:5000/auth/Microsoft/callback` with capital M

---

- [ ] 4. **Create database index for case-insensitive email lookups**
      
      Connect to the SQLite database and execute: `CREATE INDEX IF NOT EXISTS idx_employee_email_lower ON employees(LOWER(email));`. This enables efficient case-insensitive matching using `func.lower(Employee.email) == email.lower()` in the callback handler. The index must exist before deploying the SSO code.
      
      **Files:**
      - Database: c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso\tas_erp.db
      
      **Verify:** Create verify_index.py script (from design document "Database Preparation > Finding #2 Resolution: Cross-Database Verification") and run `python verify_index.py` to confirm index exists; output must show "✓ Email index exists (case-insensitive lookup will be efficient)"

---

- [ ] 5. **Update imports in app/routes/auth.py**
      
      Replace the imports section at the top of auth.py. Change `from flask_wtf.csrf import csrf` to `from app import csrf` (Finding #1). Add `from sqlalchemy.sql import func` (Finding #4) and `from sqlalchemy.exc import IntegrityError` (Finding #6). Add `from datetime import datetime` and `import secrets` for OAuth2 state generation. Add MSAL import with try/except: `try: import msal except ImportError: msal = None; logging.error(...)`. Keep existing imports for Blueprint, render_template, redirect, url_for, flash, request, current_app, session, login_user, logout_user, current_user, models (User, Employee, db), and limiter.
      
      **Pattern from design:** The exact imports block is in sso-design.md under "Authentication Routes > Complete Imports Section (Finding #1, #4 Resolution)".
      
      **Files:**
      - c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso\app\routes\auth.py
      
      **Verify:** Run `python -c "from app.routes.auth import auth_bp; print('Imports OK')"` and confirm no import errors

---

- [ ] 6. **Add helper functions to app/routes/auth.py**
      
      Add two helper functions after the imports and before the routes. First, `get_msal_client()`: checks msal is installed, retrieves AZURE_AUTHORITY/CLIENT_ID/CLIENT_SECRET from current_app.config, validates all are present, returns `msal.ConfidentialClientApplication(client_id, client_credential, authority)`. Second, `log_auth_attempt(email, ip_address, status, reason, user_id=None, role=None)`: formats structured log with timestamp (ISO 8601 with microseconds), [AUTH] tag, email, ip (with fallback to 'unknown' per Finding #9), status, optional user_id/role, and reason; uses logger.info for success and logger.warning for failure.
      
      **Pattern from design:** Exact code in sso-design.md under "MSAL Client Setup > ConfidentialClientApplication Helper" and "Authentication Logging > Log Implementation".
      
      **Files:**
      - c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso\app\routes\auth.py
      
      **Verify:** Run `python -c "from app.routes.auth import get_msal_client, log_auth_attempt; print('Helpers OK')"` and confirm functions are importable

---

- [ ] 7. **Replace /login route with GET-only SSO version**
      
      Replace the existing `/login` route that accepts GET and POST with a GET-only version. Remove the LoginForm logic and password checking. Keep the current_user.is_authenticated check that redirects to role-based dashboard. Change the rate limit decorator to use configurable rate limit: `@limiter.limit(lambda: current_app.config.get('LOGIN_RATE_LIMIT', '30 per minute'))` (Finding #8). Render login.html (which will be modified to show Microsoft button).
      
      **Pattern from design:** Exact code in sso-design.md under "Authentication Routes > Route 1: `/login` (GET only) - Modified Route".
      
      **Files:**
      - c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso\app\routes\auth.py
      
      **Verify:** Run Flask routes command `cd c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso && python -c "from app import create_app; app = create_app(); print([r for r in app.url_map.iter_rules() if 'login' in r.rule])"` and confirm /login route exists and only allows GET method

---

- [ ] 8. **Add /auth/microsoft initiate route**
      
      Add new route `@auth_bp.route('/auth/microsoft')` with configurable rate limit decorator. Generate OAuth2 state parameter using `secrets.token_urlsafe(32)` and store in `session['oauth_state']`. Retrieve AZURE_REDIRECT_URI from app.config (computed at startup). Get MSAL client via helper function. Call `msal_client.get_authorization_request_url(scopes, state, redirect_uri)` with AZURE_SCOPE from config. Handle errors: if AZURE_REDIRECT_URI is None, flash error and redirect to login; catch ValueError from get_msal_client for config issues; catch generic exceptions for network/MSAL failures. Log redirects and errors appropriately.
      
      **Pattern from design:** Exact code in sso-design.md under "Authentication Routes > Route 2: `/auth/microsoft` (GET) - New Route".
      
      **Files:**
      - c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso\app\routes\auth.py
      
      **Verify:** Run `cd c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso && python -c "from app import create_app; app = create_app(); print([r for r in app.url_map.iter_rules() if 'microsoft' in r.rule])"` and confirm /auth/microsoft route exists

---

- [ ] 9. **Add /auth/Microsoft/callback route with all design fixes**
      
      Add new route `@auth_bp.route('/auth/Microsoft/callback', methods=['GET', 'POST'])` (capital M). Decorate with `@csrf.exempt` (Finding #1) and `@limiter.limit(lambda: current_app.config.get('AUTH_CALLBACK_RATE_LIMIT', '30 per minute'))` (Finding #8). Implement full callback logic: (1) Check for error parameter; (2) Validate OAuth state (pop from session); (3) Extract authorization code; (4) Exchange code for tokens via MSAL; (5) Extract email from ID token claims with fallback chain: preferred_username → email → upn; (6) Normalize email with lowercase and strip; (7) Match employee case-insensitively: `Employee.query.filter(db.func.lower(Employee.email) == email).first()`; (8) Check employee exists and is active using explicit False check `if employee.is_active is False` (Finding #5); (9) Find or auto-create User record with race condition handling (Finding #6): try commit, catch IntegrityError, rollback, retry query; (10) Check username conflict case-insensitively `db.func.lower(User.username) == email` (Finding #7); (11) Create Flask-Login session with login_user(); (12) Log all auth attempts with IP fallback (Finding #9); (13) Redirect to role-based dashboard. Handle all error scenarios from design table (user cancels, invalid state, token exchange failure, missing email, inactive accounts, network errors).
      
      **Pattern from design:** Exact code with ALL findings addressed in sso-design.md under "Authentication Routes > Route 3: `/auth/Microsoft/callback` (GET and POST) - New Route". This is the most complex route and must follow the design exactly.
      
      **Critical details:** Capital M in route path; CSRF exempt; explicit `is False` checks; IntegrityError retry; case-insensitive queries for both email and username; IP fallback to 'unknown'; func.now() for timestamps.
      
      **Files:**
      - c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso\app\routes\auth.py
      
      **Verify:** Run `cd c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso && python -c "from app import create_app; app = create_app(); rules = [r for r in app.url_map.iter_rules() if 'callback' in r.rule]; print('Callback routes:', [(r.rule, r.methods) for r in rules])"` and confirm /auth/Microsoft/callback exists and accepts GET and POST

---

- [ ] 10. **Update /logout route to clear session completely**
      
      Replace the existing simple logout route. Call `session.clear()` before `logout_user()` to clear all session data including any OAuth state remnants. Add optional Microsoft full sign-out (commented out): construct Microsoft logout URL with post_logout_redirect_uri and redirect there. Flash success message and redirect to login. The design includes commented code for full Microsoft logout that can be enabled later by registering front-channel logout URL in Azure AD.
      
      **Pattern from design:** Exact code in sso-design.md under "Authentication Routes > Route 4: `/logout` (GET) - Modified Route".
      
      **Files:**
      - c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso\app\routes\auth.py
      
      **Verify:** Run `cd c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso && python -c "from app import create_app; app = create_app(); print([r for r in app.url_map.iter_rules() if 'logout' in r.rule])"` and confirm /logout route exists

---

- [ ] 11. **Replace login.html template with Microsoft sign-in button**
      
      Replace the entire contents of app/templates/login.html. Keep the `{% extends "base.html" %}` and `{% block unauthenticated_content %}` structure. Remove the WTForms form with username/password fields. Add a "Sign in with Microsoft" button styled with Microsoft branding: white background, gray border (#8c8c8c), Microsoft four-color logo (SVG with red #f25022, blue #00a4ef, green #7fba00, yellow #ffb900), button text "Sign in with Microsoft" in gray (#5e5e5e). Button links to `{{ url_for('auth.microsoft_auth') }}`. Include helper text: "Use your company Microsoft account to sign in" and "Contact IT support for login issues". Change title from "TAS ERP Login" to "TR Portal Login" per original user request.
      
      **Pattern from design:** Exact HTML in sso-design.md under "Template Changes > login.html Replacement".
      
      **Files:**
      - c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso\app\templates\login.html
      
      **Verify:** Start Flask dev server `cd c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso && flask run` and navigate to http://localhost:5000/login in browser; confirm page shows "TR Portal Login" heading and "Sign in with Microsoft" button with four-color logo; confirm no username/password form is visible

---

- [ ] 12. **Update .env.example with Azure AD variables and detailed documentation**
      
      Add a new section to .env.example titled "Microsoft Entra ID (Azure AD) SSO Configuration" with clear comments. Add AZURE_TENANT_ID (with provided value as example), AZURE_CLIENT_ID (with provided value), AZURE_CLIENT_SECRET (with instructions to obtain from Azure Portal > Certificates & secrets), APP_URL (with examples for dev and prod). Add optional rate limiting configuration section with LOGIN_RATE_LIMIT, AUTH_INITIATE_RATE_LIMIT, AUTH_CALLBACK_RATE_LIMIT (all commented out with defaults shown). Add important note about redirect URI configuration: must add ${APP_URL}/auth/Microsoft/callback to Azure Portal > Authentication > Redirect URIs, with examples for both dev and prod, emphasizing capital M in Microsoft.
      
      **Pattern from design:** Exact content in sso-design.md under "Configuration Design > .env.example Update".
      
      **Files:**
      - c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso\.env.example
      
      **Verify:** Run `cat c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso\.env.example` and confirm Azure AD section exists with all required variables documented; confirm redirect URI note mentions capital M in Microsoft

---

- [ ] 13. **Create verify_index.py script for cross-database index verification**
      
      Create a new file verify_index.py in the worktree root. Import create_app, db, and SQLAlchemy inspect. In app context, use inspector.get_indexes('employees') to retrieve all indexes. Check if any index name or column_names contains 'email' (case-insensitive). Print all indexes found. If email index exists, print "✓ Email index exists (case-insensitive lookup will be efficient)". If missing, print "✗ Email index missing!" with CREATE INDEX command and database-specific instructions for SQLite, MySQL, and PostgreSQL.
      
      **Pattern from design:** Exact code in sso-design.md under "Database Preparation (Finding #2 Resolution) > Finding #2 Resolution: Cross-Database Verification".
      
      **Files:**
      - c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso\verify_index.py (new file)
      
      **Verify:** Run `cd c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso && python verify_index.py` and confirm script executes and reports index status (will report missing until step 4 is completed)

---

- [ ] 14. **Integration verification: Full SSO flow test with all components**
      
      This step requires Azure AD configuration to be complete (redirect URI registered, client secret generated). Set all environment variables in .env: AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, APP_URL=http://localhost:5000, SECRET_KEY (generate fresh). Ensure the database index from step 4 exists. Start Flask dev server. Navigate to http://localhost:5000/login and confirm Microsoft button appears. Click button and confirm redirect to login.microsoftonline.com with tenant ID in URL. After Microsoft authentication, confirm redirect back to /auth/Microsoft/callback. Confirm user is logged in and redirected to appropriate dashboard (admin or employee based on role). Check logs/erpportal.log for [AUTH] tagged entries showing successful login with email, IP, status=success. Test logout and confirm session cleared. Test error cases: employee not found (use Microsoft account not in Employee table), inactive employee (set is_active=False in database).
      
      **This step verifies:** Route registration, MSAL integration, OAuth2 flow, token exchange, email extraction, case-insensitive matching, user auto-creation, Flask-Login session, authentication logging, error handling, logout.
      
      **Files affected:** All files modified in previous steps
      
      **Verify:** Run `cd c:\Users\AtulTrivedi\erpportalflask\.worktrees\entra-sso && flask run` and perform manual testing as described; confirm all test cases pass: TC1 (successful login existing user), TC2 (auto-create user), TC3 (employee not found), TC4 (inactive employee), TC6 (user cancels), TC8 (case-insensitive email), TC10-11 (role-based access), TC12 (logout)

---

## Summary

**Total steps:** 14 (13 implementation + 1 integration verification)

**Files to create:** 1 (verify_index.py)

**Files to modify:** 6 (requirements.txt, config.py, app/__init__.py, app/routes/auth.py, app/templates/login.html, .env.example)

**Database changes:** 1 index (idx_employee_email_lower)

**External dependencies:** Azure AD app registration (redirect URI, client secret)

**Critical path:** Steps 1-6 must complete before routes can be tested; step 4 (database index) must complete before step 14 (full testing)

**Design findings addressed:** All 9 findings from design review resolved (#1 csrf import, #2 index verification, #3 redirect URI storage, #4 func.now, #5 explicit False checks, #6 IntegrityError handling, #7 case-insensitive username, #8 configurable rate limits, #9 IP fallback)

**No schema changes:** User and Employee tables remain unchanged; username and password_hash columns preserved

**Backward compatibility:** All existing routes, decorators, templates (except login.html), and functionality preserved
