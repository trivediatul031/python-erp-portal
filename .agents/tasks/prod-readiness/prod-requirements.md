# Production Readiness Requirements
## Flask ERP Travel Approval System

---

## Summary

This document defines the requirements to make the Flask ERP Travel Approval System production-ready. The application currently has basic security and configuration in place but requires additional hardening, deployment infrastructure, comprehensive error handling, production logging, performance optimization, health monitoring, and deployment documentation to safely run in a production environment without issues.

---

## Functional Requirements

### FR-1: Security Hardening

**FR-1.1** Remove DEBUG mode from production execution
- **Current State**: `run.py` hardcodes `app.run(debug=True)`. `config.py` has `ProductionConfig` with `DEBUG = False`.
- **Required**: Modify `run.py` to respect environment-based configuration and never enable debug mode in production.

**FR-1.2** Enforce SECRET_KEY from environment in production
- **Current State**: `config.py` falls back to `'dev-secret-key-please-change'` if `SECRET_KEY` env var is unset.
- **Required**: In production configuration, the app must fail to start with a clear error message if `SECRET_KEY` is not set or uses the dev default value.

**FR-1.3** Add security headers to all responses
- **Current State**: No security headers are set.
- **Required**: Add the following HTTP security headers:
  - `Content-Security-Policy` (restrictive default, can be refined later)
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `Strict-Transport-Security` (HSTS) for production HTTPS
  - `Referrer-Policy: strict-origin-when-cross-origin`

**FR-1.4** Implement rate limiting on login endpoint
- **Current State**: No rate limiting exists.
- **Required**: Limit failed login attempts to prevent brute-force attacks (e.g., max 5 attempts per IP per 15 minutes).

**FR-1.5** Input sanitization review
- **Current State**: Forms use WTForms validators; database queries use SQLAlchemy ORM.
- **Required**: Review all user inputs for XSS prevention in templates; verify all file uploads are validated; ensure HTML output is properly escaped in templates.

**FR-1.6** CSRF protection verification
- **Current State**: Flask-WTF CSRF enabled in `config.py`; forms inherit from FlaskForm; manual CSRF validation in approve/reject routes.
- **Required**: Audit all POST/PUT/DELETE routes to ensure CSRF tokens are validated (either via form submission or manual `validate_csrf` call).

### FR-2: Configuration Management

**FR-2.1** Environment-based configuration selection
- **Current State**: `create_app()` accepts `config_name` parameter but defaults to 'default' (DevelopmentConfig).
- **Required**: Automatically select configuration based on `FLASK_ENV` environment variable (development/production).

**FR-2.2** Production environment variable documentation
- **Current State**: `.env.example` exists with basic variables.
- **Required**: Expand `.env.example` with all required production variables, descriptions, and examples; document which variables are mandatory vs. optional.

**FR-2.3** Validate .gitignore excludes secrets
- **Current State**: `.gitignore` already excludes `.env`, `*.db`, `logs/`, `app/static/uploads/*`.
- **Status**: ✅ Already satisfied. No changes needed.

**FR-2.4** Database connection pooling configuration
- **Current State**: `pool_pre_ping: True` and `isolation_level: READ COMMITTED` are set.
- **Required**: Add production-appropriate pool settings: `pool_size`, `max_overflow`, `pool_timeout`, `pool_recycle`.

### FR-3: Error Handling

**FR-3.1** Custom error pages for all HTTP error codes
- **Current State**: Error handlers for 403, 404, 500 exist in `app/__init__.py` and render templates in `errors/` folder.
- **Required**: Verify error templates exist at `app/templates/errors/403.html`, `404.html`, `500.html`; create them if missing; add handler for 413 (file too large).

**FR-3.2** Global exception handler
- **Current State**: 500 handler logs via `app.logger.error()` with `exc_info=True`.
- **Status**: ✅ Already implemented. No changes needed unless enhanced logging is desired.

**FR-3.3** Never expose stack traces to users
- **Current State**: Custom error handlers return simple error pages; debug mode disabled in production.
- **Required**: Verify all error responses in production return user-friendly messages without technical details.

### FR-4: Logging

**FR-4.1** Production-grade file and console logging
- **Current State**: `RotatingFileHandler` configured in `app/__init__.py` for non-debug mode (10MB files, 10 backups).
- **Status**: ✅ Already implemented. Enhancement: add console logging in production for containerized deployments.

**FR-4.2** Log security events
- **Current State**: `auth.py` logs successful logins, failed logins, and inactive user attempts.
- **Required**: Add logging for:
  - Password reset attempts (if feature added)
  - Admin actions (approve/reject TAS, user creation, employee imports)
  - Unauthorized access attempts (403 errors)
  - File upload/download events

**FR-4.3** Log application errors with context
- **Current State**: Various routes log errors with `exc_info=True`.
- **Required**: Standardize error logging format across all routes; include request context (user, IP, endpoint) in log entries.

**FR-4.4** Environment-specific log levels
- **Current State**: Production logging set to INFO level.
- **Required**: Add configuration for log levels per environment (DEBUG in dev, INFO in production, with ability to override via env var).

### FR-5: Database

**FR-5.1** Database migration system
- **Current State**: No migration system detected.
- **Required**: Integrate Flask-Migrate/Alembic; create initial migration capturing current schema; document migration workflow for future schema changes.

**FR-5.2** Database health check endpoint
- **Current State**: No health check endpoint exists.
- **Required**: Create `/health` endpoint that verifies database connectivity and returns JSON status (used by load balancers, monitoring, Docker health checks).

**FR-5.3** Database connection error handling
- **Current State**: `pool_pre_ping: True` configured; various routes have try/except blocks with `db.session.rollback()`.
- **Required**: Add connection retry logic with exponential backoff at startup; improve error messages for connection failures.

### FR-6: Performance

**FR-6.1** WSGI server configuration (Gunicorn)
- **Current State**: No Gunicorn configuration exists.
- **Required**: Create `gunicorn.conf.py` with production settings (workers, threads, timeout, max_requests, logging); document that Gunicorn is Linux-only and Windows dev uses Flask dev server.

**FR-6.2** Static file serving strategy
- **Current State**: Flask serves static files directly.
- **Required**: Document two deployment options:
  - Option A: Use WhiteNoise middleware for Flask to serve static files efficiently
  - Option B: Use nginx reverse proxy to serve static files (provide nginx config example)

**FR-6.3** Caching headers for static assets
- **Current State**: Default Flask static file handling.
- **Required**: Configure cache-control headers for static assets (CSS, JS, images) with appropriate max-age values.

**FR-6.4** Query optimization review
- **Current State**: Routes use joins and filters; some use `joinedload` for eager loading.
- **Required**: Review and optimize N+1 query patterns; add indexes to frequently queried columns (status, submitted_at, emp_id).

**FR-6.5** Response compression
- **Current State**: No compression middleware.
- **Required**: Enable gzip compression for text responses (HTML, JSON, CSS, JS) via Flask-Compress or nginx.

### FR-7: Deployment Files

**FR-7.1** Production requirements.txt
- **Current State**: `requirements.txt` exists with pinned versions; includes Flask-Bcrypt, Flask-WTF.
- **Required**: Add production dependencies: `gunicorn`, `Flask-Migrate`, optional `Flask-Compress`, optional `Flask-Limiter`; verify all versions are pinned.

**FR-7.2** Dockerfile for containerized deployment
- **Current State**: No Dockerfile exists.
- **Required**: Create `Dockerfile` with:
  - Python 3.10+ base image
  - Multi-stage build for smaller image size
  - Non-root user for security
  - Health check instruction
  - Gunicorn as entrypoint
  - Environment variable configuration

**FR-7.3** Docker Compose for full stack
- **Current State**: No `docker-compose.yml` exists.
- **Required**: Create `docker-compose.yml` with services:
  - Flask app container
  - Database container (MySQL or PostgreSQL)
  - Volume mounts for persistence
  - Environment variable configuration
  - Health checks

**FR-7.4** Gunicorn configuration file
- **Current State**: No gunicorn config exists.
- **Required**: Create `gunicorn.conf.py` with production settings (bind address, workers based on CPU count, timeout, logging, max_requests for memory leak mitigation).

**FR-7.5** Nginx configuration example
- **Current State**: No nginx config exists.
- **Required**: Create `nginx.conf.example` demonstrating:
  - Reverse proxy to Gunicorn
  - Static file serving
  - SSL/TLS configuration
  - Security headers
  - Request size limits

**FR-7.6** Health check endpoint
- **Current State**: No `/health` endpoint exists (see FR-5.2).
- **Required**: Implement `/health` endpoint returning JSON `{"status": "healthy", "database": "connected"}` with 200 status, or 503 if unhealthy.

**FR-7.7** Systemd service file example
- **Current State**: No systemd service file exists.
- **Required**: Create `erpportal.service.example` for Linux deployments without Docker (ExecStart, restart policy, environment file, user/group).

### FR-8: Testing & Validation

**FR-8.1** Smoke tests for critical routes
- **Current State**: No tests exist.
- **Required**: Create basic smoke tests covering:
  - Login (valid/invalid credentials)
  - Dashboard access (admin/employee)
  - TAS submission (employee)
  - TAS approval/rejection (admin)
  - Health check endpoint

**FR-8.2** Deployment checklist
- **Current State**: No checklist exists.
- **Required**: Create `DEPLOYMENT_CHECKLIST.md` with pre-deployment and post-deployment verification steps.

**FR-8.3** Database connection verification script
- **Current State**: No verification script exists.
- **Required**: Create `scripts/verify_db.py` to test database connectivity with the configured DATABASE_URL before deployment.

### FR-9: Documentation

**FR-9.1** Deployment guide
- **Current State**: No deployment documentation exists.
- **Required**: Create `DEPLOYMENT.md` with:
  - Environment setup (production)
  - Database initialization and migrations
  - Docker deployment steps
  - Traditional server deployment steps (systemd)
  - Environment variable reference
  - Troubleshooting common issues

**FR-9.2** Environment variables documentation
- **Current State**: `.env.example` exists with minimal comments.
- **Required**: Add inline comments in `.env.example` explaining each variable, required vs. optional, default values, and production recommendations.

**FR-9.3** Troubleshooting guide
- **Current State**: No troubleshooting guide exists.
- **Required**: Add troubleshooting section to `DEPLOYMENT.md` covering:
  - Database connection failures
  - Permission errors
  - Import/export issues
  - Login/session issues
  - Log location and interpretation

**FR-9.4** README production updates
- **Current State**: README content not reviewed.
- **Required**: Update README with:
  - Production deployment overview
  - Link to DEPLOYMENT.md
  - Security best practices summary
  - Windows dev vs. Linux production note

---

## Non-Functional Requirements

### NFR-1: Security
- All production deployments must use HTTPS with valid TLS certificates
- SECRET_KEY must be cryptographically random (min 32 bytes)
- Database credentials must never be committed to version control
- File uploads limited to 10MB (already configured)
- Session timeout of 1 hour (already configured)

### NFR-2: Performance
- Application startup time < 10 seconds
- Login response time < 1 second under normal load
- Dashboard load time < 2 seconds with < 1000 TAS records
- Support minimum 10 concurrent users without degradation

### NFR-3: Reliability
- Application must recover gracefully from transient database connection failures
- Log rotation must prevent disk space exhaustion
- Database connection pool must handle connection drops

### NFR-4: Maintainability
- All configuration must be externalized (no hardcoded values in production)
- Logging must provide sufficient detail for debugging production issues
- Database schema changes must use versioned migrations

### NFR-5: Compatibility
- Support Python 3.10+
- Support MySQL 5.7+ or PostgreSQL 12+ (via DATABASE_URL)
- Support SQLite for development (default)
- Gunicorn deployment targets Linux only; Windows development uses Flask dev server

---

## Acceptance Criteria

### AC-1: Security Hardening
1. Running the application in production configuration with `debug=True` must be impossible
2. Starting the application without SECRET_KEY environment variable must fail with clear error message in production
3. All HTTP responses include required security headers (CSP, X-Frame-Options, HSTS, etc.)
4. Login endpoint enforces rate limiting (5 failed attempts per IP per 15 minutes)
5. All POST/PUT/DELETE routes validate CSRF tokens
6. All templates properly escape user-generated content

### AC-2: Configuration Management
7. Setting `FLASK_ENV=production` loads ProductionConfig automatically
8. `.env.example` documents all required and optional environment variables with descriptions
9. Database connection pool settings are configurable via environment variables
10. `.gitignore` excludes all secrets (`.env`, `*.db`, logs, uploads) — already satisfied ✅

### AC-3: Error Handling
11. Custom error templates render for 403, 404, 500, and 413 errors
12. Production error pages do not expose stack traces or internal paths
13. All errors are logged with sufficient context for debugging

### AC-4: Logging
14. Production logs are written to rotating files (10MB max, 10 backups) — already satisfied ✅
15. Console logging is available for containerized deployments
16. Security events are logged (login attempts, admin actions, 403 errors)
17. Log level is configurable per environment via environment variable
18. Log entries include timestamp, level, message, file, and line number — already satisfied ✅

### AC-5: Database
19. Flask-Migrate is integrated with initial migration
20. `/health` endpoint returns 200 with `{"status": "healthy"}` when database is connected
21. `/health` endpoint returns 503 when database is unreachable
22. Database connection failures at startup trigger retry with exponential backoff (3 attempts)
23. Schema migrations can be applied via `flask db upgrade` command

### AC-6: Performance
24. `gunicorn.conf.py` exists with production settings (workers = 2*CPU+1, timeout=30s)
25. Static files include cache-control headers with max-age=31536000 for versioned assets
26. Response compression is enabled for text content
27. Database queries avoid N+1 patterns (verified via logging or profiling)

### AC-7: Deployment Files
28. `Dockerfile` builds successfully and creates image < 500MB
29. `docker-compose.yml` starts full stack (app + database) with single command
30. Container health check succeeds within 30 seconds of startup
31. `requirements.txt` includes `gunicorn`, `Flask-Migrate`, and all dependencies with pinned versions
32. `nginx.conf.example` demonstrates reverse proxy, static serving, and security headers
33. `erpportal.service.example` provides systemd service template

### AC-8: Testing & Validation
34. Smoke tests cover login, dashboard, TAS submission, TAS approval, and health check
35. All smoke tests pass in production configuration
36. `scripts/verify_db.py` successfully tests database connectivity
37. `DEPLOYMENT_CHECKLIST.md` provides step-by-step pre- and post-deployment verification

### AC-9: Documentation
38. `DEPLOYMENT.md` provides complete Docker deployment instructions
39. `DEPLOYMENT.md` provides complete systemd deployment instructions
40. `.env.example` has inline comments for every variable
41. `DEPLOYMENT.md` includes troubleshooting section with common issues
42. README.md links to DEPLOYMENT.md and notes Windows dev vs. Linux production

### AC-10: Production Validation
43. Application starts successfully in production configuration with all required env vars set
44. Application fails to start in production configuration if SECRET_KEY is unset or uses dev default
45. `/health` endpoint is accessible without authentication
46. Logs are written to `logs/erpportal.log` and rotated at 10MB
47. Rate limiting triggers after 5 failed login attempts
48. Database migrations run successfully on fresh database
49. Docker container restarts automatically on failure (via restart policy)
50. All existing functionality works after production hardening (login, TAS submission, approval, export, import)

---

## Out of Scope

The following items are explicitly **not** included in this production readiness effort:

1. **New Features**: No new application features (e.g., password reset, email notifications, advanced reporting)
2. **Cloud-Specific Deployment**: AWS/Azure/GCP-specific deployment guides or infrastructure-as-code (Terraform, CloudFormation)
3. **Monitoring & Observability**: Integration with monitoring tools (Prometheus, Grafana, Datadog, Sentry) — beyond basic logging and health check
4. **Load Balancer Configuration**: External load balancer setup (HAProxy, AWS ELB, etc.)
5. **CI/CD Pipeline**: Automated build, test, and deployment pipelines (GitHub Actions, GitLab CI, Jenkins)
6. **High Availability**: Multi-instance deployment, session replication, database clustering
7. **Backup & Restore**: Automated database backup and disaster recovery procedures
8. **SSL Certificate Management**: Let's Encrypt automation or certificate renewal processes
9. **Performance Testing**: Load testing, stress testing, or benchmarking under high concurrency
10. **UI/UX Changes**: No changes to the user interface, styling, or user experience (already addressed in previous work)
11. **Database Migration of Existing Data**: Assuming clean deployment or existing compatible schema
12. **Third-Party Integrations**: No integration with external services (email, SMS, payment gateways, etc.)
13. **Windows Production Deployment**: Production deployment on Windows servers (Gunicorn is Linux-only; Windows should use IIS with waitress or similar)

---

## Assumptions

1. **Target Platform**: Production deployment targets Linux servers or containers (Docker)
2. **Database**: Production will use MySQL or PostgreSQL (configurable via DATABASE_URL); SQLite is for development only
3. **HTTPS Termination**: SSL/TLS termination handled by nginx reverse proxy or cloud load balancer (not by Gunicorn)
4. **Python Version**: Python 3.10 or higher is available in production environment
5. **File Storage**: Static file uploads stored on persistent volume or shared filesystem (not S3/blob storage)
6. **Single Database**: Application connects to single database instance (no read replicas)
7. **Logging Storage**: Logs written to local filesystem (not centralized logging service)
8. **Existing Functionality**: All existing routes, templates, and features remain functional and unchanged
9. **Development Workflow**: Local development on Windows continues to use Flask dev server (not Gunicorn)
10. **Authentication**: Current username/password authentication remains unchanged (no OAuth, SAML, or SSO)

---

## Dependencies

- Python 3.10+
- Flask 2.3.3
- SQLAlchemy 2.0.20
- Flask-Login 0.6.2
- Flask-WTF 1.1.1
- Flask-Bcrypt 1.0.1
- **New**: gunicorn (to be added)
- **New**: Flask-Migrate (to be added)
- **Optional**: Flask-Compress (for response compression)
- **Optional**: Flask-Limiter (for rate limiting)
- PyMySQL 1.1.0 (for MySQL connectivity)
- pandas 2.1.0 (for import/export)
- openpyxl 3.1.2 (for Excel files)
- python-dotenv 1.0.0

---

## Notes on Current Implementation

### Already Satisfied Requirements
The following items from the task are **already implemented** and require no changes:

- **Config Classes**: `config.py` has base Config, DevelopmentConfig, and ProductionConfig ✅
- **CSRF Protection**: Flask-WTF CSRF enabled globally ✅
- **Password Hashing**: User model uses Flask-Bcrypt with `set_password()` and `check_password()` ✅
- **SQL Injection Prevention**: All queries use SQLAlchemy ORM (parameterized) ✅
- **Session Security**: `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE=Lax`, `SESSION_COOKIE_SECURE=True` in production ✅
- **Database Connection Pooling**: `pool_pre_ping=True` configured ✅
- **.env.example**: Exists with basic structure ✅
- **.gitignore**: Excludes `.env`, `*.db`, `logs/`, uploads ✅
- **Custom Error Handlers**: 403, 404, 500 handlers implemented ✅
- **Production Logging**: RotatingFileHandler with 10MB/10 backups configured ✅
- **Security Event Logging**: Login attempts, failures logged in auth.py ✅
- **requirements.txt with pinned versions**: Exists ✅

### Implementation Priorities

**High Priority** (Critical for production safety):
- FR-1.2: Enforce SECRET_KEY validation in production
- FR-1.3: Add security headers
- FR-1.4: Rate limiting on login
- FR-2.1: Environment-based config selection
- FR-5.2: Health check endpoint
- FR-7.1: Update requirements.txt with production dependencies
- FR-7.2: Dockerfile
- FR-7.3: Docker Compose
- FR-9.1: DEPLOYMENT.md

**Medium Priority** (Important for operations):
- FR-1.1: Fix run.py debug mode
- FR-5.1: Database migrations
- FR-6.1: Gunicorn configuration
- FR-8.1: Basic smoke tests
- FR-8.2: Deployment checklist

**Lower Priority** (Enhanced production quality):
- FR-4.2: Enhanced security event logging
- FR-6.2: Static file serving strategy
- FR-6.5: Response compression
- FR-7.5: Nginx configuration example
- FR-9.3: Enhanced troubleshooting guide

---

**Document Version**: 1.0  
**Created**: 2026-10-18  
**Project**: Flask ERP Travel Approval System Production Readiness
