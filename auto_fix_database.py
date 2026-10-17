"""
Automatically fix the tas_records table structure
"""

from sqlalchemy import create_engine, text
import sys

# Database connection
engine = create_engine('mysql+pymysql://root:@localhost/tas_erp')

print("=" * 70)
print("AUTOMATIC DATABASE FIX FOR TAS_RECORDS TABLE")
print("=" * 70)

def execute_sql(conn, sql, description):
    """Execute SQL and report result"""
    try:
        conn.execute(text(sql))
        conn.commit()
        print(f"✓ {description}")
        return True
    except Exception as e:
        error_msg = str(e)
        if "Duplicate column name" in error_msg:
            print(f"⊘ {description} (already exists)")
            return True
        else:
            print(f"✗ {description}")
            print(f"  Error: {error_msg}")
            return False

try:
    with engine.connect() as conn:
        print("\nStep 1: Checking current table structure...")
        result = conn.execute(text("DESCRIBE tas_records"))
        current_columns = [row[0] for row in result]
        print(f"Current columns: {', '.join(current_columns)}")
        
        # Check which columns are missing
        required_new = ['emp_name', 'department', 'travel_type', 'travel_mode']
        missing = [col for col in required_new if col not in current_columns]
        
        if missing:
            print(f"\nMissing columns: {', '.join(missing)}")
            print("\nStep 2: Adding missing columns...")
            
            if 'emp_name' not in current_columns:
                execute_sql(conn, 
                    "ALTER TABLE tas_records ADD COLUMN emp_name VARCHAR(100) NULL AFTER emp_id",
                    "Added emp_name column")
            
            if 'department' not in current_columns:
                execute_sql(conn,
                    "ALTER TABLE tas_records ADD COLUMN department VARCHAR(100) NULL AFTER emp_name",
                    "Added department column")
            
            if 'travel_type' not in current_columns:
                execute_sql(conn,
                    "ALTER TABLE tas_records ADD COLUMN travel_type VARCHAR(20) NULL AFTER department",
                    "Added travel_type column")
            
            if 'travel_mode' not in current_columns:
                execute_sql(conn,
                    "ALTER TABLE tas_records ADD COLUMN travel_mode VARCHAR(20) NULL AFTER travel_type",
                    "Added travel_mode column")
        else:
            print("\n✓ All required columns already exist!")
        
        # Step 3: Fill data for existing records
        print("\nStep 3: Filling data for existing records...")
        execute_sql(conn,
            """UPDATE tas_records tr
               INNER JOIN employees e ON tr.emp_id = e.emp_id
               SET tr.emp_name = e.name,
                   tr.department = COALESCE(e.department, 'N/A'),
                   tr.travel_type = COALESCE(tr.travel_type, 'Domestic'),
                   tr.travel_mode = COALESCE(tr.travel_mode, 'Bus')
               WHERE tr.emp_name IS NULL OR tr.department IS NULL""",
            "Populated existing records with employee data")
        
        # Step 4: Make columns NOT NULL
        print("\nStep 4: Making columns required (NOT NULL)...")
        execute_sql(conn,
            "ALTER TABLE tas_records MODIFY COLUMN emp_name VARCHAR(100) NOT NULL",
            "Made emp_name NOT NULL")
        
        execute_sql(conn,
            "ALTER TABLE tas_records MODIFY COLUMN department VARCHAR(100) NOT NULL",
            "Made department NOT NULL")
        
        execute_sql(conn,
            "ALTER TABLE tas_records MODIFY COLUMN travel_type VARCHAR(20) NOT NULL",
            "Made travel_type NOT NULL")
        
        execute_sql(conn,
            "ALTER TABLE tas_records MODIFY COLUMN travel_mode VARCHAR(20) NOT NULL",
            "Made travel_mode NOT NULL")
        
        # Step 5: Fix purpose column
        print("\nStep 5: Fixing purpose column...")
        execute_sql(conn,
            "ALTER TABLE tas_records MODIFY COLUMN purpose VARCHAR(100) NOT NULL",
            "Changed purpose to VARCHAR(100)")
        
        # Step 6: Fix timestamp columns
        print("\nStep 6: Fixing timestamp columns...")
        execute_sql(conn,
            "ALTER TABLE tas_records MODIFY COLUMN submitted_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP",
            "Fixed submitted_at timestamp")
        
        execute_sql(conn,
            "ALTER TABLE tas_records MODIFY COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "Fixed created_at timestamp")
        
        execute_sql(conn,
            "ALTER TABLE tas_records MODIFY COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
            "Fixed updated_at timestamp")
        
        # Step 7: Remove old columns if they exist
        print("\nStep 7: Removing old columns...")
        old_columns = ['travel_from', 'travel_to', 'travel_date_end', 'estimated_cost']
        
        for col in old_columns:
            if col in current_columns:
                execute_sql(conn,
                    f"ALTER TABLE tas_records DROP COLUMN {col}",
                    f"Removed {col} column")
            else:
                print(f"⊘ Column {col} already removed")
        
        # Step 8: Verify final structure
        print("\n" + "=" * 70)
        print("FINAL TABLE STRUCTURE:")
        print("=" * 70)
        result = conn.execute(text("DESCRIBE tas_records"))
        print(f"\n{'Column':<25} {'Type':<20} {'Null':<5} {'Key':<5}")
        print("-" * 70)
        for row in result:
            print(f"{row[0]:<25} {row[1]:<20} {row[2]:<5} {row[3]:<5}")
        
        print("\n" + "=" * 70)
        print("✓ DATABASE MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nYou can now submit TAS forms without errors.")
        print("Go to: http://127.0.0.1:5000/employee/submit-tas")

except Exception as e:
    print("\n" + "=" * 70)
    print("✗ ERROR OCCURRED")
    print("=" * 70)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    engine.dispose()
