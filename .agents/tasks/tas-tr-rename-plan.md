# TAS to TR Rename Implementation Plan

## Overview
Replace all occurrences of "TAS" with "TR" in user-facing text throughout the Flask Travel Request ERP portal. This includes page titles, headings, labels, buttons, flash messages, docstrings, and comments. **Critical: PRESERVE all code and database identifiers unchanged.**

## Categorization Summary
After comprehensive exploration of the codebase, occurrences are categorized as:
- **REPLACE**: User-facing text in templates, flash messages, docstrings, comments, CSS comments, README
- **PRESERVE**: Database tables/columns, Python variables/functions/classes, URL routes, file names, Jinja template variables

---

## Implementation Plan

### Phase 1: HTML Template Files

- [ ] 1. **Update app/templates/base.html**
      
      **REPLACE (user-facing text):**
      - Line 6: `<title>{% block title %}TAS ERP System{% endblock %}</title>` → `<title>{% block title %}TR Portal System{% endblock %}</title>`
      - Line 26: `<span class="brand-text">TAS ERP</span>` → `<span class="brand-text">TR Portal</span>`
      - Line 73: `<span>TAS Records</span>` → `<span>TR Records</span>`
      - Line 93: `<span>Submit TAS</span>` → `<span>Submit TR</span>`
      - Line 99: `<span>My TAS History</span>` → `<span>My TR History</span>`
      - Line 125: `<span class="text-muted">&copy; 2024 TAS ERP System. All rights reserved.</span>` → `<span class="text-muted">&copy; 2024 TR Portal System. All rights reserved.</span>`
      
      **PRESERVE (code identifiers adjacent to changes):**
      - All `url_for()` endpoints remain unchanged: `url_for('admin.tas_list')`, `url_for('employee.submit_tas')`, `url_for('employee.tas_history')`
      
      **Files:** app/templates/base.html
      
      **Verify:** Open the portal in a browser and check:
      1. Browser tab title shows "TR Portal System" (not "TAS ERP System")
      2. Top navbar shows "TR Portal" brand text
      3. Sidebar menu shows "TR Records", "Submit TR", "My TR History"
      4. Footer shows "TR Portal System"
      5. All navigation links still work (routes unchanged)

- [ ] 2. **Update app/templates/employee/submit_tas.html**
      
      **REPLACE (user-facing text):**
      - Line 3: `{% block title %}Submit TAS Request - TAS ERP{% endblock %}` → `{% block title %}Submit TR Request - TR Portal{% endblock %}`
      - Line 14: `<h1 class="page-title-submit">Submit Travel Approval Request</h1>` → `<h1 class="page-title-submit">Submit Travel Request</h1>`
      - Line 94: `<span class="btn-text">Submit TAS Request</span>` → `<span class="btn-text">Submit TR Request</span>`
      
      **PRESERVE (code identifiers):**
      - Line 9: `{{ url_for('employee.dashboard') }}` - unchanged
      - Line 21: `{{ form.hidden_tag() }}` - unchanged
      - Line 17: `<form method="POST" action="{{ url_for('employee.submit_tas') }}"` - unchanged
      
      **Files:** app/templates/employee/submit_tas.html
      
      **Verify:** Navigate to Submit TR page and check:
      1. Browser tab shows "Submit TR Request - TR Portal"
      2. Page heading shows "Submit Travel Request" (not "Travel Approval Request")
      3. Submit button shows "Submit TR Request"
      4. Form submission works correctly

- [ ] 3. **Update app/templates/employee/tas_history.html**
      
      **REPLACE (user-facing text):**
      - Line 3: `{% block title %}My TAS History - TAS ERP{% endblock %}` → `{% block title %}My TR History - TR Portal{% endblock %}`
      - Line 7: `<i class="bi bi-clock-history me-2"></i>My TAS History` → `<i class="bi bi-clock-history me-2"></i>My TR History`
      - Line 8: `<p class="page-subtitle-modern">Track and manage all your travel approval submissions</p>` → `<p class="page-subtitle-modern">Track and manage all your travel request submissions</p>`
      - Line 11: `<i class="bi bi-plus-circle me-2"></i>Submit New TAS` → `<i class="bi bi-plus-circle me-2"></i>Submit New TR`
      - Line 26: `<span>TAS NUMBER</span>` → `<span>TR NUMBER</span>`
      - Line 64: `<span class="tas-number-badge">{{ tas.tas_number }}</span>` → Display text only, variable `tas.tas_number` unchanged. Badge displays the value (already TR-1009-0001 format)
      - Line 155: `<p class="empty-subtitle">Start by submitting your first Travel Approval System request</p>` → `<p class="empty-subtitle">Start by submitting your first Travel Request</p>`
      - Line 157: `<i class="bi bi-plus-circle me-2"></i>Submit Your First TAS` → `<i class="bi bi-plus-circle me-2"></i>Submit Your First TR`
      - Line 153: `<h3 class="empty-title">No TAS Submissions Yet</h3>` → `<h3 class="empty-title">No TR Submissions Yet</h3>`
      
      **PRESERVE (code identifiers):**
      - Line 10: `{{ url_for('employee.submit_tas') }}` - unchanged
      - Line 54: `{% for tas in tas_records %}` - variable name unchanged
      - Line 64: Variable reference `{{ tas.tas_number }}` - unchanged (displays value)
      - Line 105: `{{ url_for('employee.tas_detail', tas_id=tas.tas_id) }}` - unchanged
      
      **Files:** app/templates/employee/tas_history.html
      
      **Verify:** Navigate to TR History page and check:
      1. Browser tab shows "My TR History - TR Portal"
      2. Page heading shows "My TR History"
      3. Subtitle shows "travel request submissions"
      4. Table header shows "TR NUMBER"
      5. Submit button shows "Submit New TR"
      6. Empty state shows "No TR Submissions Yet" and "Submit Your First TR"
      7. Clicking on TR numbers navigates correctly

- [ ] 4. **Update app/templates/employee/tas_detail.html**
      
      **REPLACE (user-facing text):**
      - Line 3: `{% block title %}TAS Details - {{ tas_record.tas_number }} - TAS ERP{% endblock %}` → `{% block title %}TR Details - {{ tas_record.tas_number }} - TR Portal{% endblock %}`
      - Line 9: `<h2 class="detail-title">TAS Details</h2>` → `<h2 class="detail-title">TR Details</h2>`
      - Line 17: `<h3>TAS Information</h3>` → `<h3>TR Information</h3>`
      - Line 23: `<span class="key-info-label">TAS NUMBER</span>` → `<span class="key-info-label">TR NUMBER</span>`
      
      **PRESERVE (code identifiers):**
      - Line 11: `{{ url_for('employee.tas_history') }}` - unchanged
      - Line 24: `{{ tas_record.tas_number }}` - variable unchanged (displays value)
      
      **Files:** app/templates/employee/tas_detail.html
      
      **Verify:** Click on a TR record and check:
      1. Browser tab shows "TR Details - TR-1009-0001 - TR Portal"
      2. Page heading shows "TR Details"
      3. Section heading shows "TR Information"
      4. Label shows "TR NUMBER"
      5. Back button navigates to history correctly

- [ ] 5. **Update app/templates/admin/dashboard.html**
      
      **REPLACE (user-facing text):**
      - Line 3: `{% block title %}Admin Dashboard - TAS ERP{% endblock %}` → `{% block title %}Admin Dashboard - TR Portal{% endblock %}`
      - Line 11: `<p class="dashboard-subtitle">Manage and monitor all TAS submissions</p>` → `<p class="dashboard-subtitle">Manage and monitor all TR submissions</p>`
      - Line 42: `<p class="stat-label">Total TAS</p>` → `<p class="stat-label">Total TR</p>`
      - Line 45: `<p class="stat-desc">Travel Approval Requests</p>` → `<p class="stat-desc">Travel Requests</p>`
      - Line 77: `<h3 class="chart-title">TAS Submissions Over Time</h3>` → `<h3 class="chart-title">TR Submissions Over Time</h3>`
      - Line 97: `Recent TAS Submissions` → `Recent TR Submissions`
      - Chart canvas ID line 86: `<canvas id="tasChart"></canvas>` - Keep as is (it's a DOM ID, adjacent to user text but technically code)
      
      **PRESERVE (code identifiers):**
      - Line 43: `{{ total_tas }}` - Python variable unchanged
      - Line 86: `id="tasChart"` - DOM ID for JavaScript reference
      
      **Files:** app/templates/admin/dashboard.html
      
      **Verify:** Login as admin and check dashboard:
      1. Browser tab shows "Admin Dashboard - TR Portal"
      2. Subtitle shows "monitor all TR submissions"
      3. Stat card shows "Total TR" and "Travel Requests"
      4. Chart title shows "TR Submissions Over Time"
      5. Table title shows "Recent TR Submissions"
      6. Chart renders correctly

- [ ] 6. **Update app/templates/admin/tas_list.html**
      
      **REPLACE (user-facing text):**
      - Line 3: `{% block title %}All TAS Records - TAS ERP{% endblock %}` → `{% block title %}All TR Records - TR Portal{% endblock %}`
      - Line 7: `<h1 class="h2"><i class="bi bi-list-check me-2"></i>All TAS Records</h1>` → `<h1 class="h2"><i class="bi bi-list-check me-2"></i>All TR Records</h1>`
      - Line 34: `<!-- TAS Records Table -->` → `<!-- TR Records Table -->`
      - Line 37: `<h5 class="mb-0"><i class="bi bi-table me-2"></i>TAS Records</h5>` → `<h5 class="mb-0"><i class="bi bi-table me-2"></i>TR Records</h5>`
      - Line 45: `<th class="ps-4 py-3">TAS Number</th>` → `<th class="ps-4 py-3">TR Number</th>`
      - Line 155: `<p class="text-muted mb-0">No TAS records found</p>` → `<p class="text-muted mb-0">No TR records found</p>`
      
      **PRESERVE (code identifiers):**
      - Line 16: `{{ url_for('admin.tas_list') }}` - unchanged
      - Line 26: `{{ url_for('admin.tas_list') }}` - unchanged
      - Line 54: `{% for tas_record, employee in results %}` - variable names unchanged
      - Line 57: `{{ url_for('admin.tas_detail', tas_id=tas_record.tas_id) }}` - unchanged
      - Line 59: `{{ tas_record.tas_number }}` - variable unchanged
      
      **Files:** app/templates/admin/tas_list.html
      
      **Verify:** Navigate to admin TR Records page and check:
      1. Browser tab shows "All TR Records - TR Portal"
      2. Page heading shows "All TR Records"
      3. Card heading shows "TR Records"
      4. Table header shows "TR Number"
      5. Empty state shows "No TR records found"
      6. Filtering and links work correctly

- [ ] 7. **Update app/templates/admin/tas_detail.html**
      
      **REPLACE (user-facing text):**
      - Line 3: `{% block title %}TAS Details - {{ tas_record.tas_number }} - TAS ERP{% endblock %}` → `{% block title %}TR Details - {{ tas_record.tas_number }} - TR Portal{% endblock %}`
      - Line 9: `<h2 class="detail-title">TAS Details</h2>` → `<h2 class="detail-title">TR Details</h2>`
      - Line 37: `<span class="key-info-label">TAS NUMBER</span>` → `<span class="key-info-label">TR NUMBER</span>`
      
      **PRESERVE (code identifiers):**
      - Line 12: `{{ url_for('admin.tas_list') }}` - unchanged
      - Line 10, 38: `{{ tas_record.tas_number }}` - variable unchanged
      
      **Files:** app/templates/admin/tas_detail.html
      
      **Verify:** Admin clicks on a TR record and checks:
      1. Browser tab shows "TR Details - TR-1009-0001 - TR Portal"
      2. Page heading shows "TR Details"
      3. Badge and labels show "TR NUMBER"
      4. Back to List button works correctly

### Phase 2: Python Route Files (Flash Messages Only)

- [ ] 8. **Update app/routes/employee.py**
      
      **REPLACE (flash messages - user-facing text):**
      - Line 115: `flash(f'TAS submitted successfully. Your TAS number is {tas_number}', 'success')` → `flash(f'TR submitted successfully. Your TR number is {tas_number}', 'success')`
      - Line 122: `flash('Failed to submit TAS. Please try again.', 'error')` → `flash('Failed to submit TR. Please try again.', 'error')`
      - Line 167: `flash('You do not have permission to view this TAS', 'danger')` - Keep this error message (abort 403) but consider changing to → `flash('You do not have permission to view this TR', 'danger')` for consistency
      
      **PRESERVE (all code identifiers):**
      - Function names: `submit_tas()`, `tas_history()`, `tas_detail()` - unchanged
      - Variable names: `total_tas`, `pending_tas`, `approved_tas`, `rejected_tas`, `recent_tas`, `tas_records`, `tas`, `tas_id`, `tas_record`, `tas_number` - all unchanged
      - Database model: `TASRecord`, `TASForm` - unchanged
      - All URL route decorators: `@employee_bp.route('/submit-tas')`, `@employee_bp.route('/tas-history')`, `@employee_bp.route('/tas/<int:tas_id>')` - unchanged
      
      **Files:** app/routes/employee.py
      
      **Verify:** Test employee workflows:
      1. Submit a new TR and confirm flash message shows "TR submitted successfully. Your TR number is TR-..."
      2. Test error scenario (database issue) and confirm "Failed to submit TR"
      3. Try accessing another employee's TR and confirm "permission to view this TR"
      4. All functionality works correctly with preserved code identifiers

- [ ] 9. **Update app/routes/admin.py**
      
      **REPLACE (flash messages - user-facing text):**
      - Line 234: `flash('TAS approved successfully', 'success')` → `flash('TR approved successfully', 'success')`
      - Line 240: `flash('Error updating TAS status', 'error')` → `flash('Error updating TR status', 'error')`
      - Line 269: `flash('TAS rejected', 'success')` → `flash('TR rejected', 'success')`
      - Line 275: `flash('Error updating TAS status', 'error')` → `flash('Error updating TR status', 'error')`
      - Line 233: `flash('TAS has already been processed', 'warning')` → `flash('TR has already been processed', 'warning')`
      - Line 267: `flash('TAS has already been processed', 'warning')` → `flash('TR has already been processed', 'warning')`
      
      **PRESERVE (all code identifiers):**
      - Function names: `tas_list()`, `tas_detail()`, `approve_tas()`, `reject_tas()`, `export_tas()` - unchanged
      - Variable names: `total_tas`, `tas_record`, `tas_id`, `tas_number` - unchanged
      - Database model: `TASRecord` - unchanged
      - All URL route decorators: `@admin_bp.route('/tas_list')`, `@admin_bp.route('/tas/<int:tas_id>')`, etc. - unchanged
      - Logger messages (not user-facing, but keep for clarity in logs)
      
      **Files:** app/routes/admin.py
      
      **Verify:** Test admin workflows:
      1. Approve a TR and confirm flash message "TR approved successfully"
      2. Reject a TR and confirm flash message "TR rejected"
      3. Try to re-process a TR and confirm "TR has already been processed"
      4. Test error scenarios and confirm "Error updating TR status"
      5. All approval/rejection functionality works correctly

### Phase 3: Python Model and Utility Files (Docstrings and Comments Only)

- [ ] 10. **Update app/utils.py**
      
      **REPLACE (docstrings and comments - developer-facing documentation):**
      - Line 1: `"""Utility functions for the TAS ERP application."""` → `"""Utility functions for the TR Portal application."""`
      - Line 13: `Generate unique TAS number for given employee ID in format TR-{EMPID}-{SEQUENCE}.` → `Generate unique TR number for given employee ID in format TR-{EMPID}-{SEQUENCE}.`
      - Line 27: `str: TAS number in format TR-{EMPID}-{SEQUENCE}` → `str: TR number in format TR-{EMPID}-{SEQUENCE}`
      - Line 30: `RuntimeError: If TAS number generation fails after max retries` → `RuntimeError: If TR number generation fails after max retries`
      - Line 49: `# Format: TR-EMPID-0001` comment - already correct format
      - Line 50: `tas_number = f"TR-{emp_id}-{seq_record.last_sequence:04d}"` - variable name unchanged
      - Line 60: `raise RuntimeError('Failed to generate TAS number after retries')` → `raise RuntimeError('Failed to generate TR number after retries')`
      - Line 80: `if filename.startswith('tas_records_'):` - filename pattern unchanged (code identifier)
      
      **PRESERVE (all code identifiers):**
      - Function name: `generate_tas_number()` - unchanged
      - Variable: `tas_number` - unchanged
      - Database model: `TASSequence` - unchanged
      - Filename pattern: `'tas_records_'` - unchanged (used for file matching)
      
      **Files:** app/utils.py
      
      **Verify:** Run the application and test:
      1. Submit a new TR to verify `generate_tas_number()` function still works
      2. Check that TR numbers are generated correctly (TR-EMPID-0001 format)
      3. Verify error handling with proper error messages

- [ ] 11. **Update app/models.py**
      
      **REPLACE (docstrings - NO CHANGES NEEDED):**
      - The docstrings in models.py already use proper terminology or don't mention TAS/TR explicitly
      - The `__repr__` methods on lines 91 and 101 return code identifiers, not user-facing text, so keep them unchanged
      
      **PRESERVE (all code identifiers - CRITICAL):**
      - Class names: `TASRecord`, `TASSequence` - unchanged
      - Table names: `tas_records`, `tas_sequence` - unchanged
      - Column names: `tas_id`, `tas_number`, `tas_records` (relationship) - unchanged
      - All other identifiers - unchanged
      
      **Files:** app/models.py
      
      **Verify:** Run application and confirm:
      1. Database queries work correctly
      2. No SQLAlchemy errors about missing tables/columns
      3. TR submission and retrieval works

- [ ] 12. **Update app/forms.py**
      
      **REPLACE (docstrings and form labels):**
      - Line 22: `"""Form for rejecting TAS with reason."""` → `"""Form for rejecting TR with reason."""`
      - Line 31: `submit = SubmitField('Reject TAS')` → `submit = SubmitField('Reject TR')` (button label - user-facing)
      - Line 35: `"""Form for employees to submit TAS requests."""` → `"""Form for employees to submit TR requests."""`
      - Line 62: `submit = SubmitField('Submit TAS Request')` → `submit = SubmitField('Submit TR Request')` (button label - user-facing)
      
      **PRESERVE (code identifiers):**
      - Class names: `TASForm`, `RejectTASForm` - unchanged
      - All field names - unchanged
      
      **Files:** app/forms.py
      
      **Verify:** Test forms:
      1. Submit TR form button shows "Submit TR Request"
      2. Reject form button shows "Reject TR"
      3. Form validation works correctly

### Phase 4: CSS Files (Comments Only)

- [ ] 13. **Update app/static/css/style.css**
      
      **REPLACE (CSS comments - developer-facing):**
      - Line 1: `/* TAS ERP Portal - Custom Styles */` → `/* TR Portal - Custom Styles */`
      - Line 363: `/* TAS Detail Info Items */` → `/* TR Detail Info Items */`
      - Line 696: `   Modern Form Styles - Submit TAS` → `   Modern Form Styles - Submit TR`
      - Line 699: `.submit-tas-container {` - CSS class name is a code identifier, keep unchanged
      - Line 1250: `   TAS Detail Page - Modern UI` → `   TR Detail Page - Modern UI`
      - Line 1253: `.tas-detail-container {` - CSS class name unchanged
      - Line 1282: `.tas-number-badge {` - CSS class name unchanged
      - Line 1538: `   Travel Cards - TAS Detail Page` → `   Travel Cards - TR Detail Page`
      - Line 1939: `.tas-number-link {` - CSS class name unchanged
      
      **PRESERVE (all CSS selectors and class names):**
      - All CSS class names like `.submit-tas-container`, `.tas-detail-container`, `.tas-number-badge`, `.tas-number-link` - unchanged (code identifiers referenced in HTML)
      - DOM ID `#tasChart` - unchanged
      
      **Files:** app/static/css/style.css
      
      **Verify:** Visual inspection:
      1. All pages render correctly with unchanged CSS classes
      2. No broken styles due to class name references
      3. Comments updated for developer clarity

### Phase 5: Documentation Files

- [ ] 14. **Update README.md**
      
      **REPLACE (all user-facing documentation text):**
      - Line 1: `# TAS ERP - Travel Approval System` → `# TR Portal - Travel Request System`
      - Line 3: `An Enterprise Resource Planning portal for managing employee travel approval requests.` → `An Enterprise Resource Planning portal for managing employee travel requests.`
      - Line 7: `The TAS ERP system provides a web-based interface for employees to submit travel approval requests (TAS) and for administrators to review, approve, or reject them. The system automatically generates unique TAS numbers in the format TAS-EMPID-SEQUENCE (e.g., TAS-1987-0001).` → `The TR Portal system provides a web-based interface for employees to submit travel requests (TR) and for administrators to review, approve, or reject them. The system automatically generates unique TR numbers in the format TR-EMPID-SEQUENCE (e.g., TR-1987-0001).`
      - Line 11: `- **Super Admin Dashboard**: View all TAS records, import employee data from HR, export TAS records` → `- **Super Admin Dashboard**: View all TR records, import employee data from HR, export TR records`
      - Line 12: `- **Employee Dashboard**: Submit travel approval requests, track submission status` → `- **Employee Dashboard**: Submit travel requests, track submission status`
      - Line 14: `- **Automatic TAS Number Generation**: Unique sequential numbering per employee` → `- **Automatic TR Number Generation**: Unique sequential numbering per employee`
      - Line 15: `- **Import/Export**: Import employee data from CSV/Excel, export TAS records` → `- **Import/Export**: Import employee data from CSV/Excel, export TR records`
      - Line 44: `DATABASE_URL=mysql+pymysql://username:password@localhost/tas_erp` → `DATABASE_URL=mysql+pymysql://username:password@localhost/tr_portal`
      - Line 49: `mysql -u root -p -e "CREATE DATABASE tas_erp;"` → `mysql -u root -p -e "CREATE DATABASE tr_portal;"` (NOTE: If existing database should remain tas_erp, keep this unchanged and add a note)
      - Line 54: `mysql -u root -p tas_erp < schema.sql` → `mysql -u root -p tr_portal < schema.sql` (or keep tas_erp if not changing database)
      - Line 152: References to "TAS" throughout the documentation
      
      **IMPORTANT DECISION FOR DATABASE:**
      The README references database name `tas_erp`. Since the task is to rename USER-FACING text only and preserve database identifiers, we have two options:
      A. Keep database name as `tas_erp` in README (consistent with preserve rule)
      B. Update README to reflect a new conceptual database name `tr_portal` for new installations
      
      **RECOMMENDATION**: Keep database references as `tas_erp` in README to match the preserved database table names (`tas_records`, `tas_sequence`). Add a note explaining that internal database identifiers retain "TAS" for backward compatibility while the user interface shows "TR".
      
      Add after line 7: `*Note: Internal database tables and identifiers use "TAS" for backward compatibility, while the user interface displays "TR" (Travel Request) throughout.*`
      
      Apply selective replacements focusing on user-facing terminology:
      - Change "Travel Approval System" → "Travel Request System"
      - Change "travel approval requests" → "travel requests"
      - Change "TAS number" (when referring to user-visible text) → "TR number"
      - Keep database names, table names, column names unchanged
      
      **Files:** README.md
      
      **Verify:** Read through README:
      1. Title and overview reflect TR Portal branding
      2. User-facing features mention "TR" and "travel requests"
      3. Database setup instructions remain accurate
      4. Technical implementation notes preserve correct table/column names

### Phase 6: Additional Template Files (If Any)

- [ ] 15. **Check and update any remaining template files**
      
      Search for any additional HTML template files not yet covered:
      - app/templates/errors/404.html
      - app/templates/errors/403.html
      - app/templates/errors/500.html
      - app/templates/login.html
      - app/templates/admin/user_management.html
      - app/templates/admin/import_employees.html
      - app/templates/admin/employee_list.html
      - app/templates/admin/create_user.html (if exists)
      
      **For each file:**
      - Replace any occurrence of "TAS ERP" in titles → "TR Portal"
      - Replace "TAS" in user-facing text → "TR"
      - Preserve all `url_for()` endpoints and variable names
      
      **Files:** Various template files
      
      **Verify:** Navigate through all pages:
      1. Check browser tab titles for consistency
      2. Verify all page headings and labels use "TR"
      3. Confirm navigation works correctly

### Phase 7: JavaScript Files (If Any)

- [ ] 16. **Check app/static/js/main.js for TAS references**
      
      Search for any user-facing text in JavaScript (console logs, alert messages, etc.)
      
      **REPLACE:** Any user-facing strings containing "TAS" → "TR"
      **PRESERVE:** Variable names, function names, DOM IDs containing "tas"
      
      **Files:** app/static/js/main.js
      
      **Verify:** Check browser console:
      1. No console errors
      2. JavaScript functionality works correctly
      3. Chart rendering works (tasChart ID preserved)

---

## Final Verification Checklist

After completing all phases, perform comprehensive testing:

- [ ] **Visual Inspection**
  - [ ] All browser tab titles show "TR Portal" (not "TAS ERP")
  - [ ] All page headings refer to "TR" (not "TAS")
  - [ ] Navigation menu shows "TR Records", "Submit TR", "My TR History"
  - [ ] Table headers show "TR Number"
  - [ ] Form buttons show "Submit TR Request", "Reject TR"
  - [ ] Footer shows "TR Portal System"

- [ ] **Functionality Testing - Employee**
  - [ ] Employee can log in successfully
  - [ ] Dashboard displays statistics correctly
  - [ ] Submit TR form works and generates TR number (TR-EMPID-0001 format)
  - [ ] Flash message shows "TR submitted successfully. Your TR number is TR-..."
  - [ ] TR History page displays all submissions
  - [ ] TR Detail page shows complete information
  - [ ] All navigation links work correctly

- [ ] **Functionality Testing - Admin**
  - [ ] Admin can log in successfully
  - [ ] Dashboard shows statistics and chart correctly
  - [ ] TR Records list displays all submissions with filters
  - [ ] TR Detail page shows complete information
  - [ ] Approve TR shows flash message "TR approved successfully"
  - [ ] Reject TR shows flash message "TR rejected"
  - [ ] Export functionality works correctly
  - [ ] Employee import and user management work

- [ ] **Database Integrity**
  - [ ] No SQL errors in logs
  - [ ] Database tables remain unchanged (tas_records, tas_sequence)
  - [ ] Column names remain unchanged (tas_id, tas_number)
  - [ ] Queries execute successfully
  - [ ] TR numbers generated correctly with format TR-EMPID-SEQUENCE

- [ ] **Code Integrity**
  - [ ] All Python imports work correctly
  - [ ] No undefined function/variable errors
  - [ ] URL routing works correctly (all /submit-tas, /tas-history routes functional)
  - [ ] Template rendering works (no Jinja2 undefined variable errors)
  - [ ] CSS classes applied correctly (no broken styles)

- [ ] **Cross-Browser Testing**
  - [ ] Test in Chrome/Edge
  - [ ] Test in Firefox
  - [ ] Mobile responsive layout works
  - [ ] All interactive elements functional

- [ ] **Documentation Review**
  - [ ] README reflects TR Portal branding
  - [ ] Setup instructions remain accurate
  - [ ] Technical documentation preserves correct identifiers
  - [ ] No confusion between user-facing "TR" and internal "TAS" identifiers

---

## Critical Reminders for Implementation

1. **NEVER change these identifiers** (they are code, not user-facing text):
   - Database: `tas_records`, `tas_sequence`, `tas_id`, `tas_number` (table/column names)
   - Python: `TASRecord`, `TASSequence`, `TASForm`, `RejectTASForm` (class names)
   - Python: `submit_tas()`, `tas_history()`, `tas_detail()`, `generate_tas_number()` (function names)
   - Python: `tas_record`, `tas`, `tas_id`, `total_tas`, etc. (variable names)
   - URLs: `/submit-tas`, `/tas-history`, `/tas/<int:tas_id>` (route paths)
   - URLs: `url_for('employee.submit_tas')` (Flask endpoint names)
   - CSS: `.tas-detail-container`, `.tas-number-badge`, `#tasChart` (class names and IDs)
   - Files: `submit_tas.html`, `tas_list.html`, etc. (file names)

2. **Context matters**: When you see `{{ tas_record.tas_number }}`, the Jinja template expression and variable name stay unchanged. The VALUE it displays (e.g., "TR-1009-0001") is correct. Only change the LABEL text next to it (e.g., "TAS Number" → "TR Number").

3. **Adjacent text is tricky**: In `<a href="{{ url_for('admin.tas_list') }}">TAS Records</a>`, change ONLY the visible text "TAS Records" → "TR Records". The `url_for('admin.tas_list')` stays exactly as is.

4. **Test after each phase**: Don't wait until the end. After updating each template or route file, test that specific page/feature to catch issues early.

5. **Phrase replacements** (as specified in the task):
   - "Travel Approval System" → "Travel Request System" or just "Travel Request"
   - "Travel Approval" → "Travel Request"
   - "TAS ERP" → "TR Portal"

6. **Case matching**:
   - TAS → TR
   - Tas → Tr
   - tas → tr (where contextually appropriate in prose, not in code identifiers)

---

## Implementation Notes

- **Estimated time**: 2-3 hours for careful, methodical implementation
- **Risk level**: Low (primarily text changes with clear preservation rules)
- **Backup recommendation**: Commit current state before starting: `git add -A && git commit -m "Backup before TAS to TR rename"`
- **Testing strategy**: Incremental testing after each phase prevents compounding errors
- **Rollback plan**: If issues arise, use `git diff` to review changes and `git checkout -- <file>` to revert specific files

---

## Success Criteria

The implementation is successful when:

1. ✅ Every user-visible occurrence of "TAS" has been replaced with "TR"
2. ✅ Every user-visible occurrence of "Travel Approval" has been replaced with "Travel Request"
3. ✅ All database operations continue to work without modification
4. ✅ All URLs and routing continue to function correctly
5. ✅ All Python code executes without NameError or AttributeError
6. ✅ All templates render without Jinja2 UndefinedError
7. ✅ All CSS styles apply correctly without broken selectors
8. ✅ The user experience is consistent with "TR" terminology throughout
9. ✅ No functionality is broken or degraded
10. ✅ The codebase remains maintainable with clear separation between user-facing text and code identifiers

---

**Plan completed. Ready for implementation.**
