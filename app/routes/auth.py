import secrets
import logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, current_user
from app import csrf  # Finding #1: Import initialized CSRFProtect instance
from app.models import Employee, db
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
        
        # Build authorization URL with parameters to request password auth
        auth_url = msal_client.get_authorization_request_url(
            scopes=current_app.config.get('AZURE_SCOPE'),
            state=state,
            redirect_uri=redirect_uri,
            prompt='select_account',  # Let user choose account (may bypass some MFA)
            # Add claims to request password authentication method
            claims='{"access_token":{"amr":{"values":["pwd"]}}}'
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
        
        # Check if employee is active (explicit False check)
        if employee.is_active is False:
            logger.warning(f"Inactive employee login attempt: {email} (emp_code={employee.emp_code})")
            log_auth_attempt(
                email=email,
                ip_address=request.remote_addr,
                status='failure',
                reason='Employee account is inactive'
            )
            flash('Your employee account is inactive. Please contact your system administrator.', 'error')
            return redirect(url_for('auth.login'))
        
        # Create Flask-Login session directly with Employee
        login_user(employee)
        
        # Log successful authentication
        log_auth_attempt(
            email=email,
            ip_address=request.remote_addr,
            status='success',
            reason='Authenticated via Microsoft SSO',
            user_id=employee.emp_code,
            role=employee.role
        )
        
        logger.info(f"User logged in via SSO: {email} (emp_code={employee.emp_code}, role={employee.role})")
        
        # Redirect to role-based dashboard
        if employee.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('employee.dashboard'))
    
    except Exception as e:
        logger.error(f"Unexpected error in Microsoft callback: {str(e)}", exc_info=True)
        flash('An error occurred during authentication. Please try again.', 'error')
        return redirect(url_for('auth.login'))


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
