"""Check which database Flask is connected to"""

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Get the database URL being used
    db_url = str(db.engine.url)
    print("=" * 60)
    print("FLASK DATABASE CONNECTION CHECK")
    print("=" * 60)
    print(f"\nDatabase URL: {db_url}")
    
    if 'sqlite' in db_url.lower():
        print("\n❌ ERROR: Still using SQLite!")
        print("The Flask app needs to be restarted to pick up .env changes")
    elif 'mysql' in db_url.lower():
        print("\n✓ SUCCESS: Using MySQL!")
        
        # Check if emp_name column exists
        try:
            result = db.session.execute(text("DESCRIBE tas_records"))
            columns = [row[0] for row in result]
            print("\nColumns in tas_records table:")
            for col in columns:
                print(f"  - {col}")
            
            if 'emp_name' in columns:
                print("\n✓ emp_name column EXISTS in MySQL!")
            else:
                print("\n❌ emp_name column MISSING in MySQL!")
        except Exception as e:
            print(f"\n❌ Error checking columns: {e}")
    else:
        print(f"\n⚠ Unknown database type: {db_url}")
    
    print("=" * 60)
