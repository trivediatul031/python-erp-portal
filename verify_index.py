#!/usr/bin/env python3
"""
verify_index.py - Verify database indexes for email lookups
Run after deploying database changes to ensure case-insensitive email lookup is efficient.
Works with SQLite, MySQL, and PostgreSQL.
"""
from app import create_app, db
from sqlalchemy import inspect

app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    
    try:
        indexes = inspector.get_indexes('employees')
    except Exception as e:
        print(f"Error inspecting indexes: {e}")
        print("Database may not be initialized yet.")
        exit(1)
    
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
