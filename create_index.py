#!/usr/bin/env python3
"""
Script to create database index for case-insensitive email lookups.
Creates index if database exists, or creates database if it doesn't exist.
"""
import sqlite3
import os
import sys

DB_PATH = 'tas_erp.db'

def create_index():
    """Create case-insensitive email index on employees table."""
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        print("The database will be created when the application first runs.")
        print("The index creation SQL will be executed then.")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if employees table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='employees';
        """)
        
        if not cursor.fetchone():
            print("Warning: 'employees' table does not exist yet.")
            print("The index will be created when the table is created.")
            conn.close()
            return False
        
        # Create the index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_employee_email_lower 
            ON employees(LOWER(email));
        """)
        
        conn.commit()
        
        # Verify index was created
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name='idx_employee_email_lower';
        """)
        
        if cursor.fetchone():
            print("✓ Successfully created index: idx_employee_email_lower")
            print("  Index on: employees(LOWER(email))")
            return True
        else:
            print("✗ Failed to create index")
            return False
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    success = create_index()
    sys.exit(0 if success else 1)
