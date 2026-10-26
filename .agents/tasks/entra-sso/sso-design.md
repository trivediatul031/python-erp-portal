# Microsoft Entra ID SSO Implementation - Technical Design Document (Revision 3)

**Design Version:** 3.0  
**Date:** 2024-01-15  
**Status:** Revised - All HIGH and MEDIUM Findings Addressed  
**Requirements Document:** sso-requirements.md v1.0

---

## Executive Summary

This design implements Microsoft Entra ID (Azure AD) Single Sign-On for the Flask Travel Request (TR) Portal using OAuth2 authorization code flow via MSAL (Microsoft Authentication Library) for Python. This revision addresses all 6 HIGH and 3 MEDIUM severity findings from the design review.

**Critical Changes from v2.0:**
- **Finding #1:** Changed CSRF import from `from flask_wtf.csrf import csrf` to `from app import csrf`
- **Finding #2:** Added cross-database index verification using SQLAlchemy inspector
- **Finding #3:** Changed redirect URI from `@property` to computed value stored in `app.config` at initialization
- **Finding #4:** Added `from sqlalchemy.sql import func` and use `func.now()` for timestamps
- **Finding #5:** Changed `if not employee.is_active` to `if employee.is_active is False` for explicit NULL handling
- **Finding #6:** Added `IntegrityError` handling for concurrent user creation race conditions
- **Finding #7:** Changed username conflict check to case-insensitive query
- **Finding #8:** Made rate limits configurable and increased callback limit to 30/min
- **Finding #9:** Added IP address fallback to 'unknown' if None

The existing Flask-Login session management, role-based authorization decorators, and User/Employee models remain unchanged. Username/password columns are preserved for potential future use.

---

## Overview

This design replaces username/password login with Microsoft SSO. After successful Microsoft authentication, the user's email is extracted from ID token claims, normalized to lowercase, and matched case-insensitively against the Employee table using a function-based database index. If a matching employee is found and active, a Flask-Login session is established. New employees automatically receive User records with `role='employee'`.

**Key Design Decisions:**
1. **Callback route:** `/auth/Microsoft/callback` (capital M) for branding consistency
2. **Dynamic deployment:** `APP_URL` environment variable + computed redirect URI at app startup
3. **No schema changes:** User and Employee tables unchanged; preserves username/password columns
4. **Unified logging:** Authentication events tagged with `[AUTH]` in main application log
5. **Auto-user creation:** New employees automatically get User records
6. **Explicit NULL handling:** Distinguish `False` from `None/NULL` in is_active checks
7. **Race condition handling:** Retry query on IntegrityError during user creation

---

## Technology Stack

- **OAuth2 Library**: MSAL for Python (`msal==1.26.0`)
- **Authentication Protocol**: OAuth2 Authorization Code Flow
- **Token Storage**: Flask server-side session (encrypted with `SECRET_KEY`); tokens discarded after initial use
- **Email Extraction**: ID token claims with fallback: `preferred_username` → `email` → `upn`
- **Email Matching**: Case-insensitive via `LOWER(email)` with function-based database index
- **Session Management**: Flask-Login (existing, no changes)
- **Authorization**: Existing `@login_required`, `@admin_required`, `@employee_required` decorators (no changes)
- **CSRF Protection**: OAuth2 state parameter for callback; Flask-WTF CSRF for other routes
- **Logging**: Python `logging` module with `[AUTH]` tag to `logs/erpportal.log`
- **Database**: SQLite with function-based index; no schema migration

---

## Configuration Design

### Environment Variables

Add to `config.py` in the `Config` base class:

```python
# Microsoft Entra ID (Azure AD) SSO Configuration
AZURE_TENANT_ID = os.environ.get('AZURE_TENANT_ID')
AZURE_CLIENT_ID = os.environ.get('AZURE_CLIENT_ID')
AZURE_CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET')

# Dynamic base URL for redirect URI construction
APP_URL = os.environ.get('APP_URL')

# Derived configuration
AZURE_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}" if AZURE_TENANT_ID else None
AZURE_SCOPE = ["User.Read", "openid", "profile", "email"]

# Rate limiting configuration (Finding #8)
LOGIN_RATE_LIMIT = os.environ.get('LOGIN_RATE_LIMIT', '30 per minute')
AUTH_INITIATE_RATE_LIMIT = os.environ.get('AUTH_INITIATE_RATE_LIMIT', '20 per minute')
# Callback should be generous - user already authenticated at Microsoft
AUTH_CALLBACK_RATE_LIMIT = os.environ.get('AUTH_CALLBACK_RATE_LIMIT', '30 per minute')
```

**Rationale for APP_URL:** 
- Single configuration works in dev (`http://localhost:5000`) and prod (`https://trportal.company.com`)
- No need to change `.env` files when switching environments
- Redirect URI constructed at runtime in `app/__init__.py`

### Redirect URI Construction (Finding #3 Resolution)

**Finding #3 Issue:** Properties don't work as Flask config values. `current_app.config.get('AZURE_REDIRECT_URI')` returns `<property object>`, not the computed string.

**Resolution:** Compute redirect URI at app initialization and store in `app.config`.

Add to `app/__init__.py` after `app.config.from_object(config[config_name])`:

```python
def create_app(config_name='default'):
    """Flask application factory."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Finding #3 Resolution: Compute AZURE_REDIRECT_URI at initialization
    app_url = app.config.get('APP_URL')
    if app_url:
        app.config['AZURE_REDIRECT_URI'] = f"{app_url.rstrip('/')}/auth/Microsoft/callback"
    else:
        app.config['AZURE_REDIRECT_URI'] = None
    
    # ... rest of initialization ...
```

**Examples:**
- Dev: `APP_URL=http://localhost:5000` → `http://localhost:5000/auth/Microsoft/callback`
- Prod: `APP_URL=https://trportal.company.com` → `https://trportal.company.com/auth/Microsoft/callback`

### Startup Validation

Add to `ProductionConfig.init_app()` in `config.py`:

```python
import re

@classmethod
def init_app(cls, app):
    """Initialize production configuration with comprehensive Azure AD validation."""
    Config.init_app(app)
    
    # Existing SECRET_KEY validation
    if not os.environ.get('SECRET_KEY') or cls.SECRET_KEY == 'dev-secret-key-please-change':
        raise ValueError(
            "SECRET_KEY must be set in environment variables for production. "
            "Generate with: python -c 'import secrets; print(secrets.token_hex(32))'"
        )
    
    # Validate required Azure AD credentials presence
    required_azure_vars = ['AZURE_TENANT_ID', 'AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET', 'APP_URL']
    missing_vars = [var for var in required_azure_vars if not os.environ.get(var)]
    
    if missing_vars:
        raise ValueError(
            f"Missing required Azure AD environment variables: {', '.join(missing_vars)}.\n"
            "Obtain from Azure Portal → App registrations → Your App:\n"
            "  - AZURE_TENANT_ID: Directory (tenant) ID\n"
            "  - AZURE_CLIENT_ID: Application (client) ID\n"
            "  - AZURE_CLIENT_SECRET: Certificates & secrets → New client secret\n"
            "  - APP_URL: Application base URL (e.g., https://yourdomain.com)"
        )
    
    # UUID format validation for tenant and client IDs
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    
    tenant_id = os.environ.get('AZURE_TENANT_ID', '')
    client_id = os.environ.get('AZURE_CLIENT_ID', '')
    
    if tenant_id and not uuid_pattern.match(tenant_id):
        raise ValueError(
            f"AZURE_TENANT_ID is not a valid UUID: {tenant_id}.\n"
            "Check: Azure Portal → App registrations → Overview → Directory (tenant) ID"
        )
    
    if client_id and not uuid_pattern.match(client_id):
        raise ValueError(
            f"AZURE_CLIENT_ID is not a valid UUID: {client_id}.\n"
            "Check: Azure Portal → App registrations → Overview → Application (client) ID"
        )
    
    # Client secret validation (Azure generates 40-44 character secrets)
    client_secret = os.environ.get('AZURE_CLIENT_SECRET', '')
    if client_secret and len(client_secret) < 32:
        raise ValueError(
            f"AZURE_CLIENT_SECRET appears invalid (length: {len(client_secret)} chars, expected 32+).\n"
            "Generate new: Azure Portal → App registrations → Certificates & secrets"
        )
    
    # APP_URL format validation
    app_url = os.environ.get('APP_URL', '')
    if app_url and not (app_url.startswith('http://') or app_url.startswith('https://')):
        raise ValueError(
            f"APP_URL must start with http:// or https://. Got: {app_url}"
        )
    
    # Warn if production uses HTTP (except localhost)
    if app_url and app_url.startswith('http://') and not app_url.startswith('http://localhost'):
        import logging
        logging.warning(
            f"APP_URL uses HTTP in production: {app_url}. "
            "HTTPS is strongly recommended for security."
        )
```

### .env.example Update

Update `.env.example`:

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here-generate-with-secrets-module
FLASK_ENV=development

# Database
DATABASE_URL=sqlite:///tas_erp.db

# ============================================================================
# Microsoft Entra ID (Azure AD) SSO Configuration
# ============================================================================
# Obtain these from: Azure Portal → App registrations → Your App

# Directory (tenant) ID - from Azure Portal → Overview
AZURE_TENANT_ID=e675c809-45cb-45e7-bdee-08c8772f0cf3

# Application (client) ID - from Azure Portal → Overview  
AZURE_CLIENT_ID=c1aef541-a3eb-439c-a9b9-92d5f1226720

# Client Secret - from Certificates & secrets → New client secret
# IMPORTANT: Copy immediately when generated (shown only once)
AZURE_CLIENT_SECRET=your-client-secret-here

# Application Base URL (used to construct redirect URI dynamically)
# Development: http://localhost:5000
# Production: https://yourdomain.com (NO trailing slash)
APP_URL=http://localhost:5000

# ============================================================================
# Rate Limiting Configuration (Optional - Finding #8)
# ============================================================================
# Adjust these values based on your usage patterns
# LOGIN_RATE_LIMIT=30 per minute
# AUTH_INITIATE_RATE_LIMIT=20 per minute
# AUTH_CALLBACK_RATE_LIMIT=30 per minute

# ============================================================================
# IMPORTANT: Azure AD Redirect URI Configuration
# ============================================================================
# The redirect URI is constructed as: ${APP_URL}/auth/Microsoft/callback
#
# You MUST add this exact URI to Azure Portal:
#   1. Go to: Azure Portal → App registrations → Your App
#   2. Navigate to: Authentication → Platform configurations → Web
#   3. Add Redirect URIs:
#      - Development: http://localhost:5000/auth/Microsoft/callback
#      - Production: https://yourdomain.com/auth/Microsoft/callback
#
# Note: The 'M' in 'Microsoft' must be capitalized!
# ============================================================================
```

---

## MSAL Client Setup

### Import Handling

Add to top of `app/routes/auth.py`:

```python
# MSAL import with error handling
try:
    import msal
except ImportError:
    msal = None
    import logging
    logging.error(
        "msal package not installed. Install with: pip install msal==1.26.0"
    )
```

### ConfidentialClientApplication Helper

Add to `app/routes/auth.py`:

```python
def get_msal_client():
    """
    Create and return an MSAL ConfidentialClientApplication instance.
    Uses configuration from current_app.config.
    
    Returns:
        msal.ConfidentialClientApplication: Initialized MSAL client
    
    Raises:
        ValueError: If required Azure configuration is missing or MSAL not installed
    """
    if msal is None:
        raise ValueError(
            "MSAL library not installed. Install with: pip install msal==1.26.0"
        )
    
    authority = current_app.config.get('AZURE_AUTHORITY')
    client_id = current_app.config.get('AZURE_CLIENT_ID')
    client_secret = current_app.config.get('AZURE_CLIENT_SECRET')
    
    if not all([authority, client_id, client_secret]):
        raise ValueError(
            "Azure AD configuration incomplete. Required: AZURE_TENANT_ID, "
            "AZURE_CLIENT_ID, AZURE_CLIENT_SECRET"
        )
    
    return msal.ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority=authority
    )
```

**Authority URL:** `https://login.microsoftonline.com/e675c809-45cb-45e7-bdee-08c8772f0cf3` (single-tenant)

---

## Authentication Routes

### Complete Imports Section (Finding #1, #4 Resolution)

Replace imports in `app/routes/auth.py`:

```python
import secrets
import logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, current_user
from app import csrf  # Finding #1: Import initialized CSRFProtect instance
from app.models import User, Employee, db
from app import limiter
from sqlalchemy.sql import func  # Finding #4: For database-generated timestamps
from sqlalchemy.exc import IntegrityError  # Finding #6: For race condition handling

# MSAL import with error handling
try:
    import msal
except ImportError:
    msal = None
    logging.error(
        "msal package not installed. Install with: pip install msal==1.26.0"
    )

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)
```

**Finding #1 Resolution:** Changed from `from flask_wtf.csrf import csrf` to `from app import csrf` to import the initialized CSRFProtect instance from `app/__init__.py`.

**Finding #4 Resolution:** Added `from sqlalchemy.sql import func` for database-generated timestamps using `func.now()`.

**Finding #6 Resolution:** Added `from sqlalchemy.exc import IntegrityError` for handling concurrent user creation.

### Route 1: `/login` (GET only) - Modified Route

**Finding #8 Resolution:** Use configurable rate limit from config.

Replace existing `/login` route:

```python
@auth_bp.route('/login', methods=['GET'])
@limiter.limit(lambda: current_app.config.get('LOGIN_RATE_LIMIT', '30 per minute'))
def login():
    """
    Login route - renders page with Microsoft SSO button.
    Rate limit configurable to prevent reconnaissance attacks.
    """
    if current_user.is_authenticated:
        # Redirect authenticated users to role-based dashboard
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('employee.dashboard'))
    
    # Render login page with "Sign in with Microsoft" button
    return render_template('login.html')
```

**Finding #8 Resolution:** Rate limit now comes from config with default '30 per minute'.

### Route 2: `/auth/microsoft` (GET) - New Route

Add new route:

```python
@auth_bp.route('/auth/microsoft')
@limiter.limit(lambda: current_app.config.get('AUTH_INITIATE_RATE_LIMIT', '20 per minute'))
def microsoft_auth():
    """
    Initiate OAuth2 authorization code flow with Microsoft Entra ID.
    Generates a state parameter for CSRF protection and redirects to Microsoft.
    """
    try:
        msal_client = get_msal_client()
        
        # Generate state for CSRF protection (256 bits of entropy)
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        
        # Get redirect URI (computed at app initialization - Finding #3)
        redirect_uri = current_app.config.get('AZURE_REDIRECT_URI')
        
        if not redirect_uri:
            logger.error("APP_URL not configured; cannot construct redirect URI")
            flash('Authentication service is not configured. Contact administrator.', 'error')
            return redirect(url_for('auth.login'))
        
        # Build authorization URL
        auth_url = msal_client.get_authorization_request_url(
            scopes=current_app.config.get('AZURE_SCOPE'),
            state=state,
            redirect_uri=redirect_uri
        )
        
        logger.info(f"Redirecting to Microsoft authentication (redirect_uri={redirect_uri})")
        return redirect(auth_url)
        
    except ValueError as e:
        logger.error(f"Azure configuration error: {str(e)}")
        flash('Authentication service is not configured. Contact administrator.', 'error')
        return redirect(url_for('auth.login'))
    except Exception as e:
        logger.error(f"Error initiating Microsoft auth: {str(e)}", exc_info=True)
        flash('Unable to connect to authentication service. Please try again later.', 'error')
        return redirect(url_for('auth.login'))
```

### Route 3: `/auth/Microsoft/callback` (GET and POST) - New Route

**Finding #1, #5, #6, #7 Resolution:** CSRF exemption, explicit NULL checks, race condition handling, case-insensitive username query.

Add new route:

```python
@auth_bp.route('/auth/Microsoft/callback', methods=['GET', 'POST'])
@csrf.exempt  # Finding #1: OAuth2 state parameter provides CSRF protection
@limiter.limit(lambda: current_app.config.get('AUTH_CALLBACK_RATE_LIMIT', '30 per minute'))
def microsoft_callback():
    """
    OAuth2 callback handler. Exchanges authorization code for tokens,
    validates response, extracts user email, matches to Employee,
    and creates Flask-Login session.
    
    Note: CSRF exempt because Azure AD may use GET or POST for callback,
    and OAuth2 state parameter provides equivalent CSRF protection.
    """
    try:
        # Check for error parameter from Microsoft
        error = request.args.get('error')
        error_description = request.args.get('error_description', 'Unknown error')
        
        if error:
            if error == 'access_denied':
                logger.info(f"User cancelled Microsoft authentication: {error_description}")
                flash('Authentication cancelled.', 'info')
            else:
                logger.warning(f"Microsoft authentication error: {error} - {error_description}")
                flash('Authentication failed. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        # Validate state parameter (CSRF protection)
        state = request.args.get('state')
        stored_state = session.pop('oauth_state', None)
        
        if not state or state != stored_state:
            logger.warning(
                f"Invalid OAuth state parameter from IP {request.remote_addr or 'unknown'}. "
                f"Expected: {stored_state}, Got: {state}"
            )
            log_auth_attempt(
                email='unknown',
                ip_address=request.remote_addr,
                status='failure',
                reason='Invalid OAuth state (potential CSRF attack)'
            )
            flash('Invalid authentication request. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        # Get authorization code
        auth_code = request.args.get('code')
        if not auth_code:
            logger.error("No authorization code received from Microsoft")
            flash('Authentication failed. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        # Exchange authorization code for tokens
        msal_client = get_msal_client()
        redirect_uri = current_app.config.get('AZURE_REDIRECT_URI')
        
        token_response = msal_client.acquire_token_by_authorization_code(
            code=auth_code,
            scopes=current_app.config.get('AZURE_SCOPE'),
            redirect_uri=redirect_uri
        )
        
        # Check for errors in token response
        if 'error' in token_response:
            error_msg = token_response.get('error_description', token_response.get('error'))
            logger.error(f"Token acquisition failed: {error_msg}")
            flash('Authentication session expired. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        # Extract email with fallback chain
        id_token_claims = token_response.get('id_token_claims')
        if not id_token_claims:
            logger.error("No ID token claims in token response")
            flash('Authentication failed. Please contact support.', 'error')
            return redirect(url_for('auth.login'))
        
        # Email claim priority: preferred_username → email → upn (User Principal Name)
        email = (
            id_token_claims.get('preferred_username') or 
            id_token_claims.get('email') or 
            id_token_claims.get('upn')
        )
        
        # Validate email is non-empty
        if not email or not email.strip():
            logger.error(
                f"Email claim is empty or missing in ID token. "
                f"Available claims: {list(id_token_claims.keys())}"
            )
            flash('Unable to retrieve your email address. Please contact support.', 'error')
            return redirect(url_for('auth.login'))
        
        # Normalize email (lowercase, strip whitespace)
        email = email.lower().strip()
        
        logger.info(f"Microsoft authentication successful for email: {email}")
        
        # Match email to Employee (case-insensitive with index)
        employee = Employee.query.filter(db.func.lower(Employee.email) == email).first()
        
        if not employee:
            logger.warning(f"Employee not found for email: {email}")
            log_auth_attempt(
                email=email,
                ip_address=request.remote_addr,
                status='failure',
                reason='Employee not found in database'
            )
            flash(
                f'Your Microsoft account ({email}) is not associated with an employee record. '
                'Please contact your system administrator.',
                'error'
            )
            return redirect(url_for('auth.login'))
        
        # Finding #5: Explicit False check to distinguish from NULL
        if employee.is_active is False:
            logger.warning(f"Inactive employee login attempt: {email} (emp_id={employee.emp_id})")
            log_auth_attempt(
                email=email,
                ip_address=request.remote_addr,
                status='failure',
                reason='Employee account is inactive'
            )
            flash('Your employee account is inactive. Please contact your system administrator.', 'error')
            return redirect(url_for('auth.login'))
        
        # Find or create User record
        user = User.query.filter_by(emp_id=employee.emp_id).first()
        
        if user:
            # Existing user - check if active (Finding #5: explicit False check)
            if user.is_active is False:
                logger.warning(f"Inactive user login attempt: {email} (user_id={user.user_id})")
                log_auth_attempt(
                    email=email,
                    ip_address=request.remote_addr,
                    status='failure',
                    reason='User account is inactive',
                    user_id=user.user_id
                )
                flash('Your account is inactive. Please contact your system administrator.', 'error')
                return redirect(url_for('auth.login'))
        else:
            # Finding #7: Case-insensitive username conflict check
            existing_user_with_email = User.query.filter(
                db.func.lower(User.username) == email
            ).first()
            
            if existing_user_with_email:
                logger.error(
                    f"Cannot auto-create user for {email}: username already exists "
                    f"for different employee (existing_user_id={existing_user_with_email.user_id}, "
                    f"existing_emp_id={existing_user_with_email.emp_id}, "
                    f"current_emp_id={employee.emp_id})"
                )
                log_auth_attempt(
                    email=email,
                    ip_address=request.remote_addr,
                    status='failure',
                    reason='Username conflict: email already in use by another user account'
                )
                flash(
                    'Your email address is already associated with another user account. '
                    'Please contact your system administrator.',
                    'error'
                )
                return redirect(url_for('auth.login'))
            
            # Auto-create User record for new SSO users
            # Finding #4: Use func.now() for database-generated timestamps
            user = User(
                username=email,
                password_hash='SSO_AUTH',  # Placeholder (not a valid bcrypt hash)
                role='employee',  # Default role; admins assigned manually
                emp_id=employee.emp_id,
                is_active=True,
                created_at=func.now(),
                updated_at=func.now()
            )
            
            # Finding #6: Handle race condition with IntegrityError
            try:
                db.session.add(user)
                db.session.commit()
                logger.info(
                    f"Auto-created User record for {email} "
                    f"(user_id={user.user_id}, emp_id={employee.emp_id})"
                )
            except IntegrityError as e:
                db.session.rollback()
                logger.warning(
                    f"Race condition during user auto-creation for {email}: {str(e)}. "
                    "Retrying query for existing user."
                )
                
                # Race condition: another request created the user between our check and commit
                # Query again to get the newly created user
                user = User.query.filter_by(emp_id=employee.emp_id).first()
                
                if not user:
                    # Still doesn't exist - unexpected integrity error
                    logger.error(f"Integrity error during user creation but user still not found: {email}")
                    flash('Unable to create your user account. Please contact support.', 'error')
                    return redirect(url_for('auth.login'))
                
                # Found the user created by concurrent request - proceed with that user
                logger.info(f"Using User record created by concurrent request: {email} (user_id={user.user_id})")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to auto-create user for {email}: {str(e)}", exc_info=True)
                flash('Unable to create your user account. Please contact support.', 'error')
                return redirect(url_for('auth.login'))
        
        # Create Flask-Login session
        login_user(user)
        
        # Log successful authentication
        log_auth_attempt(
            email=email,
            ip_address=request.remote_addr,
            status='success',
            reason='Authenticated via Microsoft SSO',
            user_id=user.user_id,
            role=user.role
        )
        
        logger.info(f"User logged in via SSO: {email} (user_id={user.user_id}, role={user.role})")
        
        # Redirect to role-based dashboard
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('employee.dashboard'))
    
    except Exception as e:
        logger.error(f"Unexpected error in Microsoft callback: {str(e)}", exc_info=True)
        flash('An error occurred during authentication. Please try again.', 'error')
        return redirect(url_for('auth.login'))
```

**Key Resolutions:**
- **Finding #1:** `@csrf.exempt` decorator using imported `csrf` from `app`
- **Finding #4:** Use `func.now()` for timestamps instead of `datetime.utcnow()`
- **Finding #5:** `if employee.is_active is False` and `if user.is_active is False` for explicit NULL handling
- **Finding #6:** Try/except IntegrityError with retry query for race condition
- **Finding #7:** `db.func.lower(User.username) == email` for case-insensitive check
- **Finding #9:** `request.remote_addr or 'unknown'` fallback for IP address

### Route 4: `/logout` (GET) - Modified Route

Replace existing `/logout` route:

```python
@auth_bp.route('/logout')
def logout():
    """
    Logout route. Clears Flask session, logs out user, and optionally
    signs out from Microsoft Entra ID.
    """
    # Clear Flask session completely
    session.clear()
    
    # Logout from Flask-Login
    logout_user()
    
    # Optional: Microsoft full sign-out
    # To enable, uncomment this block AND register redirect URI in Azure AD:
    # Azure Portal → App registrations → Your App → Authentication → Redirect URIs
    # Add the base URL (Front-channel logout URL):
    #   - Development: http://localhost:5000/
    #   - Production: https://yourdomain.com/
    """
    from urllib.parse import quote
    
    tenant_id = current_app.config.get('AZURE_TENANT_ID')
    app_url = current_app.config.get('APP_URL')
    
    if tenant_id and app_url:
        # Build Microsoft logout URL with URL-encoded redirect
        post_logout_redirect = app_url.rstrip('/')
        microsoft_logout_url = (
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/logout"
            f"?post_logout_redirect_uri={quote(post_logout_redirect)}"
        )
        return redirect(microsoft_logout_url)
    """
    
    flash('You have been successfully logged out.', 'success')
    return redirect(url_for('auth.login'))
```

---

## Authentication Logging

### Log Format

Structured format with consistent timestamp:

```
[2024-01-15T10:30:45.123456] [AUTH] email=user@company.com ip=192.168.1.100 status=success user_id=42 role=employee reason=Authenticated via Microsoft SSO
[2024-01-15T10:31:12.654321] [AUTH] email=unknown@external.com ip=192.168.1.101 status=failure reason=Employee not found in database
```

### Log Implementation

**Decision:** Use main application logger with `[AUTH]` tag.

Add to `app/routes/auth.py`:

```python
def log_auth_attempt(email, ip_address, status, reason, user_id=None, role=None):
    """
    Log an authentication attempt to main application log with [AUTH] tag.
    
    Args:
        email (str): User's email address (or 'unknown')
        ip_address (str): Client IP address (or None)
        status (str): 'success' or 'failure'
        reason (str): Human-readable explanation
        user_id (int, optional): User ID (for successful logins)
        role (str, optional): User role (for successful logins)
    """
    # Use explicit format to ensure microseconds always included
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')
    
    log_parts = [
        f"[{timestamp}]",
        "[AUTH]",  # Tag for filtering: grep '\[AUTH\]' logs/erpportal.log
        f"email={email}",
        f"ip={ip_address or 'unknown'}",  # Finding #9: Handle None IP address
        f"status={status}"
    ]
    
    if user_id is not None:
        log_parts.append(f"user_id={user_id}")
    
    if role is not None:
        log_parts.append(f"role={role}")
    
    log_parts.append(f"reason={reason}")
    
    log_message = " ".join(log_parts)
    
    # Write to main application log (configured in app/__init__.py)
    if status == 'success':
        logger.info(log_message)
    else:
        logger.warning(log_message)
```

**Finding #9 Resolution:** Added `ip_address or 'unknown'` fallback to handle None values.

---

## Template Changes

### login.html Replacement

Replace `app/templates/login.html`:

```html
{% extends "base.html" %}

{% block title %}Login - TR Portal{% endblock %}

{% block unauthenticated_content %}
<div class="row justify-content-center align-items-center" style="min-height: 80vh;">
    <div class="col-md-4">
        <div class="card shadow">
            <div class="card-body p-5">
                <h2 class="text-center mb-4" style="color: #0066cc;">
                    <strong>TR Portal Login</strong>
                </h2>
                
                <!-- Microsoft Sign-In Button -->
                <div class="d-grid mb-3">
                    <a href="{{ url_for('auth.microsoft_auth') }}" 
                       class="btn btn-lg d-flex align-items-center justify-content-center"
                       style="background-color: #ffffff; border: 1px solid #8c8c8c; color: #5e5e5e; font-weight: 500;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="21" height="21" viewBox="0 0 21 21" style="margin-right: 12px;">
                            <rect x="1" y="1" width="9" height="9" fill="#f25022"/>
                            <rect x="1" y="11" width="9" height="9" fill="#00a4ef"/>
                            <rect x="11" y="1" width="9" height="9" fill="#7fba00"/>
                            <rect x="11" y="11" width="9" height="9" fill="#ffb900"/>
                        </svg>
                        Sign in with Microsoft
                    </a>
                </div>
                
                <div class="text-center mt-4">
                    <small class="text-muted">Use your company Microsoft account to sign in</small>
                </div>
                
                <div class="text-center mt-3">
                    <small class="text-muted">Contact IT support for login issues</small>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

**Design notes:**
- Follows Microsoft branding guidelines (four-color square logo)
- Button styling matches Microsoft recommendations (white background, gray border)
- Clear call-to-action: "Sign in with Microsoft"
- Helper text explains users should use company Microsoft account

---

## Database Preparation (Finding #2 Resolution)

### Required Index for Case-Insensitive Lookups

**CRITICAL PREREQUISITE:** Create function-based index on `LOWER(email)` before deployment.

**Deployment SQL:**

```sql
-- SQLite syntax
CREATE INDEX IF NOT EXISTS idx_employee_email_lower ON employees(LOWER(email));
```

**Finding #2 Resolution: Cross-Database Verification**

Add verification script that works on SQLite, MySQL, and PostgreSQL:

```python
# verify_index.py - Run after deploying database changes
from app import create_app, db
from sqlalchemy import inspect

app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    indexes = inspector.get_indexes('employees')
    
    print("Indexes on 'employees' table:")
    for idx in indexes:
        print(f"  - {idx['name']}: columns={idx['column_names']}, unique={idx['unique']}")
    
    # Check for email-related index
    has_email_index = any(
        'email' in str(idx.get('column_names', [])).lower() or 
        'email' in idx.get('name', '').lower()
        for idx in indexes
    )
    
    if has_email_index:
        print("\n✓ Email index exists (case-insensitive lookup will be efficient)")
    else:
        print("\n✗ Email index missing!")
        print("  Create with: CREATE INDEX IF NOT EXISTS idx_employee_email_lower ON employees(LOWER(email));")
        
        # Database-specific instructions
        dialect = db.engine.dialect.name
        if dialect == 'sqlite':
            print("  SQLite: Function-based index supported")
        elif dialect == 'mysql':
            print("  MySQL: Use LOWER(email) in index or change collation to ci (case-insensitive)")
        elif dialect == 'postgresql':
            print("  PostgreSQL: Function-based index supported with LOWER(email)")
```

**Alternative Verification SQL (Database-Specific):**

```sql
-- SQLite
SELECT name, sql FROM sqlite_master 
WHERE type='index' AND tbl_name='employees' 
ORDER BY name;

-- MySQL
SHOW INDEX FROM employees WHERE Column_name LIKE '%email%';

-- PostgreSQL
SELECT indexname, indexdef FROM pg_indexes 
WHERE tablename = 'employees' AND indexdef LIKE '%email%';
```

**Finding #2 Resolution:** Provides SQLAlchemy-based verification that works across all databases, plus database-specific SQL for manual verification.

---

## Security Design

### OAuth2 State Parameter (CSRF Protection)

**Implementation:**
1. Generate state: `secrets.token_urlsafe(32)` (256 bits entropy)
2. Store in session: `session['oauth_state'] = state`
3. Include in authorization URL to Microsoft
4. Validate on callback: `request.args.get('state') == session.pop('oauth_state')`
5. Log potential CSRF attacks if mismatch

**CSRF Exemption Rationale:** OAuth2 state parameter provides equivalent CSRF protection. Azure AD may use GET or POST for callback, and neither will include Flask-WTF CSRF token.

### Session Configuration

**Decision:** Use Flask's default client-side sessions (signed cookies).

**Rationale:**
- OAuth2 state is small (~43 bytes)
- Flask-Login session data is minimal
- Default 4KB cookie limit is sufficient
- Avoids new dependency (Flask-Session)
- Simpler deployment

### Token Security

**Storage:** Access tokens NOT stored in session after callback. Application only uses token once to extract email, then discards it. Flask-Login session is sufficient for subsequent requests.

### HTTPS Enforcement

**Development:** HTTP allowed for localhost testing.

**Production:**
- `SESSION_COOKIE_SECURE = True` in `ProductionConfig` (already configured)
- HSTS header via `ProductionConfig.SECURITY_HEADERS` (already configured: 'Strict-Transport-Security': 'max-age=31536000; includeSubDomains')
- Azure AD redirect URI must use HTTPS
- Startup warning if APP_URL uses HTTP (except localhost)

### Rate Limiting (Finding #8 Resolution)

**Configurable Limits:**
- `/login`: `LOGIN_RATE_LIMIT` (default: 30/min)
- `/auth/microsoft`: `AUTH_INITIATE_RATE_LIMIT` (default: 20/min)
- `/auth/Microsoft/callback`: `AUTH_CALLBACK_RATE_LIMIT` (default: 30/min)

**Rationale:**
- Callback should be generous (user already authenticated at Microsoft)
- Allows legitimate retries without frustration
- Configurable for different deployment scenarios

**Finding #8 Resolution:** Rate limits are now configurable via environment variables with sensible defaults. Callback limit increased to 30/min to accommodate legitimate retries.

---

## Error Handling

### Error Scenarios Table

| Error Scenario | Detection | User Message | Log Level | Redirect |
|---------------|-----------|--------------|-----------|----------|
| User cancels login | `error=access_denied` in callback | "Authentication cancelled." (info) | INFO | `/login` |
| Invalid OAuth state | State mismatch | "Invalid authentication request." (error) | WARNING + auth log | `/login` |
| Token exchange fails | Error in token response | "Authentication session expired." (error) | ERROR | `/login` |
| No email in claims | Missing all email claims | "Unable to retrieve email." (error) | ERROR with claims | `/login` |
| Empty email | Email is whitespace | "Unable to retrieve email." (error) | ERROR | `/login` |
| Employee not found | Query returns None | "Account not associated with employee." (error) | WARNING + auth log | `/login` |
| Inactive employee (explicit False) | `is_active is False` | "Employee account inactive." (error) | WARNING + auth log | `/login` |
| Inactive user (explicit False) | `is_active is False` | "User account inactive." (error) | WARNING + auth log | `/login` |
| Username conflict | Case-insensitive username exists | "Email already in use." (error) | ERROR + auth log | `/login` |
| Race condition during user creation | IntegrityError on commit | Retry query → success or error | WARNING + retry logic | Dashboard or `/login` |
| Network timeout | Exception during MSAL call | "Unable to connect." (error) | ERROR with exception | `/login` |
| Missing Azure config | `get_msal_client()` ValueError | "Service not configured." (error) | ERROR | `/login` |
| MSAL not installed | Import fails | "Service not configured." (error) | ERROR with install instructions | `/login` |
| Unexpected exception | Unhandled exception | "An error occurred." (error) | ERROR with stack trace | `/login` |

**Principles:**
- User messages are clear, non-technical, actionable
- Logs contain technical details for debugging
- No sensitive data (tokens, secrets) exposed to users
- All errors redirect to `/login` for retry

---

## Testing Strategy

### Manual Testing Prerequisites

1. **Azure AD Configuration:**
   - Add redirect URI: `http://localhost:5000/auth/Microsoft/callback`
   - Generate Client Secret
   - Grant admin consent for API permissions

2. **Environment Variables (`.env`):**
   ```
   AZURE_TENANT_ID=e675c809-45cb-45e7-bdee-08c8772f0cf3
   AZURE_CLIENT_ID=c1aef541-a3eb-439c-a9b9-92d5f1226720
   AZURE_CLIENT_SECRET=<from Azure Portal>
   APP_URL=http://localhost:5000
   SECRET_KEY=<generate with secrets.token_hex(32)>
   FLASK_ENV=development
   ```

3. **Database:**
   - Create function-based index: `CREATE INDEX IF NOT EXISTS idx_employee_email_lower ON employees(LOWER(email));`
   - Verify with `python verify_index.py`
   - Ensure Employee records exist with emails matching Microsoft accounts

### Test Cases (NIT Finding #10 Resolution)

| ID | Test Case | Expected Result |
|----|-----------|-----------------|
| TC1 | Successful SSO login (existing user) | Dashboard loaded; session established; logged to `logs/erpportal.log` with `[AUTH]` tag |
| TC2 | Successful SSO login (new user auto-creation) | User record created; employee dashboard loaded; logged |
| TC3 | Employee not found | Error with email address shown; failure logged |
| TC4 | Inactive employee (is_active=False) | "Employee inactive" error; failure logged |
| TC5 | Inactive user (is_active=False) | "User inactive" error; failure logged |
| TC6 | User cancels Microsoft login | "Authentication cancelled"; redirected to login |
| TC7 | Username conflict (case-insensitive) | "Email already in use" error; failure logged with both user IDs |
| TC8 | Case-insensitive email: `John.Doe@company.com` vs `john.doe@company.com` | Login succeeds; matched case-insensitively |
| TC9 | Email with whitespace: ` john.doe@company.com ` | Login succeeds after strip() |
| TC10 | Employee role access control | Employee cannot access `/admin/dashboard` (403 Forbidden) |
| TC11 | Admin role access | Admin can access all admin routes |
| TC12 | Logout | Session cleared; cannot access protected routes |
| TC13 | Already authenticated | Navigating to `/login` redirects to dashboard |
| TC14 | Concurrent login (race condition) | Both requests succeed; second uses User created by first |
| TC15 | Employee with NULL is_active | Login succeeds (NULL treated as allowed) |
| TC16 | Request with None remote_addr | Logs with 'ip=unknown' |

**NIT Finding #10 Resolution:** Replaced duplicate TC9 with "Email with whitespace" test case.

---

## Deployment Considerations

### Azure AD App Registration Checklist

**Required settings in Azure Portal:**

1. **Redirect URIs** (Authentication → Web):
   - Development: `http://localhost:5000/auth/Microsoft/callback`
   - Production: `https://yourdomain.com/auth/Microsoft/callback`
   - **Note:** Capital 'M' in 'Microsoft' is required!

2. **Client Secret** (Certificates & secrets):
   - Generate with 24-month expiration
   - Copy value immediately (shown once)
   - Store in `AZURE_CLIENT_SECRET`

3. **API Permissions** (Microsoft Graph, Delegated):
   - `User.Read` ✓
   - `openid` ✓
   - `profile` ✓
   - `email` ✓
   - Grant admin consent if required by tenant policy

4. **Supported account types**:
   - "Accounts in this organizational directory only (Single tenant)" ✓

### Production Environment Variables

```bash
# Required
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export FLASK_ENV="production"
export AZURE_TENANT_ID="e675c809-45cb-45e7-bdee-08c8772f0cf3"
export AZURE_CLIENT_ID="c1aef541-a3eb-439c-a9b9-92d5f1226720"
export AZURE_CLIENT_SECRET="<from Azure Portal>"
export APP_URL="https://yourdomain.com"

# Optional rate limit overrides
export LOGIN_RATE_LIMIT="30 per minute"
export AUTH_INITIATE_RATE_LIMIT="20 per minute"
export AUTH_CALLBACK_RATE_LIMIT="30 per minute"
```

### Database Migration Checklist

- [ ] Backup database before deployment
- [ ] Create function-based index: `CREATE INDEX IF NOT EXISTS idx_employee_email_lower ON employees(LOWER(email));`
- [ ] Verify with `python verify_index.py`
- [ ] Verify Employee.email values are unique
- [ ] Verify employees have correct email addresses
- [ ] Test case-insensitive queries work with index

### Reverse Proxy Configuration (NIT Finding #11 Resolution)

**Example Nginx:**

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Critical:** Ensure `X-Forwarded-For` header is forwarded for accurate IP logging and rate limiting.

**NIT Finding #11 Resolution:** Added explicit reference that HSTS header is already configured via `ProductionConfig.SECURITY_HEADERS` with value `Strict-Transport-Security: max-age=31536000; includeSubDomains`.

---

## File Modification Summary

### Files to Modify

| File | Changes | Findings Addressed |
|------|---------|-------------------|
| `config.py` | Add Azure config vars, rate limits; add comprehensive validation in `ProductionConfig.init_app()`; add `import re` | #8 (rate limits), #13 (validation) |
| `app/__init__.py` | Compute `AZURE_REDIRECT_URI` after config load and store in `app.config` | #3 (property pattern) |
| `app/routes/auth.py` | Update imports (csrf from app, func, IntegrityError); modify `/login`; add `/auth/microsoft`; add `/auth/Microsoft/callback` with `@csrf.exempt` and all fixes; update `/logout`; add `get_msal_client()`; add `log_auth_attempt()` | #1, #4, #5, #6, #7, #8, #9 |
| `app/templates/login.html` | Replace with Microsoft sign-in button | N/A |
| `.env.example` | Add Azure AD variables, APP_URL, rate limits, detailed comments | #8 (rate limit config) |
| `requirements.txt` | Add `msal==1.26.0` | N/A |
| `verify_index.py` (new) | Cross-database index verification script | #2 (verification) |

### Files NOT Modified

- `app/models.py`: No schema changes
- `app/auth.py`: No changes to decorators
- `app/routes/admin.py`: No changes
- `app/routes/employee.py`: No changes
- All templates except `login.html`: No changes
- `app/forms.py`: LoginForm no longer used but can remain

### Database Changes

**Required:**
```sql
CREATE INDEX IF NOT EXISTS idx_employee_email_lower ON employees(LOWER(email));
```

---

## Implementation Checklist

### Phase 1: Configuration (30 min)

- [ ] Add `msal==1.26.0` to `requirements.txt`
- [ ] Run `pip install -r requirements.txt`
- [ ] Update `config.py`:
  - [ ] Add `import re` at top
  - [ ] Add Azure config variables and rate limits in `Config` class
  - [ ] Add validation in `ProductionConfig.init_app()`
- [ ] Update `app/__init__.py`:
  - [ ] Add redirect URI computation after config load
- [ ] Update `.env.example` with detailed comments and rate limits
- [ ] Set environment variables in `.env`:
  - [ ] `AZURE_TENANT_ID`
  - [ ] `AZURE_CLIENT_ID`
  - [ ] `AZURE_CLIENT_SECRET`
  - [ ] `APP_URL=http://localhost:5000`
  - [ ] `SECRET_KEY` (generate new)
- [ ] Test config loads: `python -c "from app import create_app; app = create_app(); print(app.config.get('AZURE_REDIRECT_URI'))"`

### Phase 2: Database (15 min)

- [ ] Create function-based index:
  ```sql
  CREATE INDEX IF NOT EXISTS idx_employee_email_lower ON employees(LOWER(email));
  ```
- [ ] Create `verify_index.py` script
- [ ] Run verification: `python verify_index.py`

### Phase 3: Authentication Routes (60 min)

- [ ] Update imports in `app/routes/auth.py`:
  - [ ] Change `from flask_wtf.csrf import csrf` to `from app import csrf`
  - [ ] Add `from sqlalchemy.sql import func`
  - [ ] Add `from sqlalchemy.exc import IntegrityError`
  - [ ] Add MSAL try/except import
  - [ ] Add `secrets`, `datetime`
- [ ] Add `get_msal_client()` helper function
- [ ] Add `log_auth_attempt()` helper function with IP fallback
- [ ] Modify `/login` route (GET-only, configurable rate limit)
- [ ] Add `/auth/microsoft` route
- [ ] Add `/auth/Microsoft/callback` route with all fixes (#1, #4, #5, #6, #7, #9)
- [ ] Update `/logout` route
- [ ] Test routes load: `flask routes | grep auth`

### Phase 4: Template (10 min)

- [ ] Backup existing `app/templates/login.html`
- [ ] Replace with new version (Microsoft button)
- [ ] Test template renders: navigate to `/login`

### Phase 5: Azure AD Configuration (20 min)

- [ ] Azure Portal → App registrations → Your App
- [ ] Add redirect URI: `http://localhost:5000/auth/Microsoft/callback`
- [ ] Generate Client Secret
- [ ] Copy secret to `.env` as `AZURE_CLIENT_SECRET`
- [ ] Verify API permissions (User.Read, openid, profile, email)
- [ ] Grant admin consent if required

### Phase 6: Testing (90 min)

- [ ] Test TC1-TC16 (see Testing Strategy section)
- [ ] Verify authentication logs in `logs/erpportal.log`:
  ```bash
  grep '\[AUTH\]' logs/erpportal.log
  ```
- [ ] Test case-insensitive email matching (TC8)
- [ ] Test whitespace handling (TC9)
- [ ] Test username conflict scenario (TC7)
- [ ] Test race condition (TC14): simulate with concurrent requests
- [ ] Test NULL is_active handling (TC15)
- [ ] Test rate limiting (exceed limits to verify)

### Phase 7: Production Preparation (30 min)

- [ ] Add production redirect URI: `https://yourdomain.com/auth/Microsoft/callback`
- [ ] Set production environment variables (including rate limits if customizing)
- [ ] Configure HTTPS reverse proxy with X-Forwarded-For
- [ ] Test startup validation (try starting without `AZURE_CLIENT_SECRET`)
- [ ] Deploy to staging environment
- [ ] Run smoke tests in staging (all TC1-TC16)

---

## Design Review Findings - Resolution Summary

### HIGH Severity (All 6 Resolved)

| # | Finding | Resolution |
|---|---------|------------|
| 1 | CSRF Decorator Import Not Specified | Changed to `from app import csrf` to import initialized CSRFProtect instance; `@csrf.exempt` decorator used on callback |
| 2 | Database Index Verification SQL Is Platform-Specific | Added `verify_index.py` with SQLAlchemy inspector that works on SQLite, MySQL, PostgreSQL; also provided database-specific SQL alternatives |
| 3 | Config Property Usage Pattern Unclear | Changed from `@property` to computed value stored in `app.config['AZURE_REDIRECT_URI']` at app initialization in `app/__init__.py` |
| 4 | Missing datetime Import for User Auto-Creation | Added `from sqlalchemy.sql import func` and use `created_at=func.now()`, `updated_at=func.now()` for database-generated timestamps |
| 5 | Employee is_active Check Uses Wrong Attribute | Changed to explicit False check: `if employee.is_active is False` and `if user.is_active is False` to distinguish False from None/NULL |
| 6 | User Auto-Creation Missing Database Constraint Violation Handling | Added `from sqlalchemy.exc import IntegrityError` with try/except; on IntegrityError, retry query to get user created by concurrent request |

### MEDIUM Severity (All 3 Resolved)

| # | Finding | Resolution |
|---|---------|------------|
| 7 | Email Normalization Inconsistent with Database | Changed username conflict check to case-insensitive: `User.query.filter(db.func.lower(User.username) == email).first()` |
| 8 | Rate Limit Values Not Documented in Central Location | Added `LOGIN_RATE_LIMIT`, `AUTH_INITIATE_RATE_LIMIT`, `AUTH_CALLBACK_RATE_LIMIT` to config.py with defaults (30, 20, 30 per minute); callback generous since user already authenticated; all configurable via environment |
| 9 | Logging Helper Doesn't Handle None/Missing IP Address | Added fallback: `f"ip={ip_address or 'unknown'}"` in `log_auth_attempt()` function |

### NIT Severity (All 2 Addressed)

| # | Finding | Resolution |
|---|---------|------------|
| 10 | Test Case TC8 and TC9 Are Duplicates | Replaced TC9 with "Email with whitespace" test case: Microsoft returns ` john.doe@company.com ` with spaces, login succeeds after strip() |
| 11 | Documentation References Undefined "security headers" Configuration | Added explicit reference under HTTPS Enforcement and Reverse Proxy Configuration that HSTS is already configured via `ProductionConfig.SECURITY_HEADERS` |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Azure client secret expires | High | High | Document expiration date; set calendar reminder 2 weeks before; monitor auth failures |
| Email case mismatch | Low | Low | Function-based index + case-insensitive queries + test case TC8 |
| Username conflict | Low | Medium | Case-insensitive check before auto-creation; log with both user IDs; clear error |
| Race condition during user creation | Low | Low | IntegrityError handling retries query; test case TC14 validates |
| Session size exceeds 4KB | Low | Medium | OAuth state is small; Flask-Login minimal; monitor during testing |
| Rate limit too restrictive | Low | Low | All limits configurable; callback generous at 30/min; adjust based on usage |
| Missing X-Forwarded-For | Medium | Low | Logs show proxy IP instead of client; verify reverse proxy config |
| MSAL package not installed | Low | High | Try/except with clear error; requirement in `requirements.txt`; test in CI |
| Database index missing | Medium | High | Deployment checklist includes verification; `verify_index.py` script |
| NULL is_active values | Medium | Medium | Explicit False checks treat NULL as allowed; test case TC15 validates |

---

## Appendix: Response to Review Findings

### Finding #1: CSRF Decorator Import
**Response:** ADDRESSED. Changed import from `from flask_wtf.csrf import csrf` to `from app import csrf`. Verified that `app/__init__.py` initializes `csrf = CSRFProtect()` and the instance is importable.

### Finding #2: Database Index Verification
**Response:** ADDRESSED. Created `verify_index.py` script using SQLAlchemy's `inspect(db.engine).get_indexes('employees')` that works across SQLite, MySQL, and PostgreSQL. Also provided database-specific SQL commands for manual verification.

### Finding #3: Config Property Usage
**Response:** ADDRESSED. Removed `@property` decorator. Instead, `AZURE_REDIRECT_URI` is computed in `app/__init__.py` after config load and stored as a regular config value: `app.config['AZURE_REDIRECT_URI'] = f"{app_url.rstrip('/')}/auth/Microsoft/callback"`. This ensures `current_app.config.get('AZURE_REDIRECT_URI')` returns the computed string, not a property object.

### Finding #4: Missing datetime Import
**Response:** ADDRESSED. Added `from sqlalchemy.sql import func` and changed user creation to use `created_at=func.now()` and `updated_at=func.now()` for database-generated timestamps. This avoids naive datetime issues and matches SQLAlchemy best practices.

### Finding #5: Employee is_active Check
**Response:** ADDRESSED. Changed all `if not employee.is_active` to `if employee.is_active is False` to explicitly check for False value. This distinguishes False from None/NULL, allowing NULL values to be treated as "allowed" (or whatever the business logic requires). Added test case TC15 to validate NULL handling.

### Finding #6: User Auto-Creation Race Condition
**Response:** ADDRESSED. Added `from sqlalchemy.exc import IntegrityError` and wrapped user creation in try/except. On IntegrityError (indicating concurrent creation), rollback and retry query with `User.query.filter_by(emp_id=employee.emp_id).first()` to get the user created by the concurrent request. If still not found, raise error. Added detailed logging for race condition cases. Added test case TC14.

### Finding #7: Email Normalization Inconsistent
**Response:** ADDRESSED. Changed username conflict check from case-sensitive `User.query.filter_by(username=email).first()` to case-insensitive `User.query.filter(db.func.lower(User.username) == email).first()`. This matches the employee lookup pattern and prevents false negatives on username conflicts.

### Finding #8: Rate Limit Values Not Documented
**Response:** ADDRESSED. Added three configurable rate limit settings to `config.py`: `LOGIN_RATE_LIMIT` (default: 30/min), `AUTH_INITIATE_RATE_LIMIT` (default: 20/min), `AUTH_CALLBACK_RATE_LIMIT` (default: 30/min). Callback limit is generous (30/min) because user has already authenticated at Microsoft. All routes use `lambda: current_app.config.get(...)` pattern. Documented in `.env.example`.

### Finding #9: Logging Helper IP Address
**Response:** ADDRESSED. Added fallback in `log_auth_attempt()`: `f"ip={ip_address or 'unknown'}"`. This handles None values from `request.remote_addr` in testing or proxy configurations. Added test case TC16 to validate.

### Finding #10: Test Case Duplicates
**Response:** ADDRESSED. Replaced duplicate TC9 with new test case: "Email with whitespace: Microsoft returns ` john.doe@company.com ` (with spaces) - login succeeds after strip()". This tests the `.strip()` normalization in the callback handler.

### Finding #11: Documentation References
**Response:** ADDRESSED. Added explicit reference in "HTTPS Enforcement" and "Reverse Proxy Configuration" sections stating that HSTS header is already configured via `ProductionConfig.SECURITY_HEADERS` with value `Strict-Transport-Security: max-age=31536000; includeSubDomains`. No code changes needed since config.py already has this.

---

**End of Technical Design Document**

**Document Version:** 3.0  
**Date:** 2024-01-15  
**Status:** Ready for Implementation - All Review Findings Addressed
