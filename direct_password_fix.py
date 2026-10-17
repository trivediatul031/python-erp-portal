"""
Direct database password fix using SQLAlchemy Core
"""

from sqlalchemy import create_engine, text
import bcrypt

# Database connection
engine = create_engine('mysql+pymysql://root:@localhost/tas_erp')

# Generate a proper bcrypt hash
password = 'admin123'
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

print(f"Generated hash: {password_hash[:50]}...\n")

with engine.connect() as conn:
    # Show current users
    result = conn.execute(text("SELECT user_id, username, role, LEFT(password_hash, 50) as hash_preview FROM users"))
    print("Current users:")
    for row in result:
        print(f"  ID {row.user_id}: {row.username:15} ({row.role:10}) Hash: {row.hash_preview}...")
    
    print("\n" + "="*60)
    
    # Update all employee users
    result = conn.execute(
        text("UPDATE users SET password_hash = :hash WHERE role = 'employee'"),
        {"hash": password_hash}
    )
    conn.commit()
    
    print(f"\n✓ Updated {result.rowcount} employee user(s)")
    
    # Verify the update
    result = conn.execute(text("SELECT user_id, username, role, password_hash FROM users WHERE role = 'employee'"))
    print("\nUpdated employees:")
    for row in result:
        # Verify hash works
        check = bcrypt.checkpw(password.encode('utf-8'), row.password_hash.encode('utf-8'))
        status = "✓ VALID" if check else "✗ INVALID"
        print(f"  {row.username}: {status}")
    
    print("\n" + "="*60)
    print("\n✓ All done! You can now login with:")
    print("  Username: john.doe")
    print("  Password: admin123")

print("\nClosing connection...")
engine.dispose()
print("✓ Complete!")
