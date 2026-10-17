"""Quick check of what's wrong"""
from sqlalchemy import create_engine, text

engine = create_engine('mysql+pymysql://root:@localhost/tas_erp')

with engine.connect() as conn:
    result = conn.execute(text("DESCRIBE tas_records"))
    print("Current columns in tas_records:")
    for row in result:
        print(f"  - {row[0]}")
    
print("\nChecking for required new column:")
with engine.connect() as conn:
    result = conn.execute(text("SHOW COLUMNS FROM tas_records LIKE 'travel_mode'"))
    rows = list(result)
    if rows:
        print("  ✓ travel_mode exists")
    else:
        print("  ✗ travel_mode MISSING - Run migration SQL!")

engine.dispose()
