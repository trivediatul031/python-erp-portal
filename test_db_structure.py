"""
Check database structure to diagnose TAS submission issue
"""

from sqlalchemy import create_engine, text, inspect
import sys

# Database connection
engine = create_engine('mysql+pymysql://root:@localhost/tas_erp')

print("=" * 60)
print("CHECKING TAS_RECORDS TABLE STRUCTURE")
print("=" * 60)

try:
    with engine.connect() as conn:
        # Get table columns
        result = conn.execute(text("DESCRIBE tas_records"))
        
        print("\nCurrent table structure:")
        print("-" * 60)
        columns = []
        for row in result:
            columns.append(row[0])
            print(f"  {row[0]:25} {row[1]:20} {row[2]:5} {row[3]:5}")
        
        print("\n" + "=" * 60)
        print("REQUIRED COLUMNS FOR NEW MODEL:")
        print("=" * 60)
        
        required_columns = [
            'tas_id',
            'tas_number',
            'emp_id',
            'emp_name',
            'department',
            'travel_type',
            'travel_mode',  # NEW - required
            'travel_date_start',
            'purpose',
            'status',
            'submitted_at',
            'reviewed_at',
            'reviewed_by',
            'rejection_reason',
            'created_at',
            'updated_at'
        ]
        
        removed_columns = [
            'travel_from',
            'travel_to',
            'travel_date_end',
            'estimated_cost'
        ]
        
        print("\nRequired columns:")
        missing = []
        for col in required_columns:
            if col in columns:
                print(f"  ✓ {col}")
            else:
                print(f"  ✗ {col} - MISSING!")
                missing.append(col)
        
        print("\nColumns that should be removed:")
        extra = []
        for col in removed_columns:
            if col in columns:
                print(f"  ✗ {col} - STILL EXISTS!")
                extra.append(col)
            else:
                print(f"  ✓ {col} - Removed")
        
        print("\n" + "=" * 60)
        if missing or extra:
            print("⚠️  DATABASE MIGRATION REQUIRED!")
            print("=" * 60)
            if missing:
                print(f"\nMissing columns: {', '.join(missing)}")
            if extra:
                print(f"Extra columns to remove: {', '.join(extra)}")
            print("\nPlease run the database migration SQL file:")
            print("  - FRESH_TAS_MIGRATION.sql (recommended)")
            print("  - or UPDATE_TAS_SIMPLIFIED.sql")
        else:
            print("✓ Database structure is correct!")
            print("=" * 60)
        
except Exception as e:
    print(f"\n✗ Error connecting to database: {e}")
    print("\nMake sure:")
    print("  1. MySQL is running")
    print("  2. Database 'tas_erp' exists")
    print("  3. Connection credentials are correct")
    sys.exit(1)
finally:
    engine.dispose()
