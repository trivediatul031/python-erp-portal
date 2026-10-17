"""Direct password fix - minimal dependencies"""
import pymysql
from flask_bcrypt import Bcrypt

# Create bcrypt instance
bcrypt = Bcrypt()

# Connect to database
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='tas_erp'
)

cursor = conn.cursor()

try:
    # Get all users
    cursor.execute("SELECT user_id, username FROM users")
    users = cursor.fetchall()
    
    print(f"Found {len(users)} users")
    
    updated = 0
    for user_id, username in users:
        # Determine password
        if username == 'admin':
            password = 'admin123'
        else:
            password = f"{username}emp@123"
        
        # Generate bcrypt hash
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Update database
        cursor.execute(
            "UPDATE users SET password_hash = %s, is_active = 1 WHERE user_id = %s",
            (password_hash, user_id)
        )
        
        updated += 1
        if updated % 50 == 0:
            conn.commit()
            print(f"  Updated {updated}/{len(users)}...")
    
    # Final commit
    conn.commit()
    print(f"\n✅ Updated {updated} users!")
    print("\n📋 Login credentials:")
    print("   Admin: admin / admin123")
    print("   Employee: [emp_code] / [emp_code]emp@123")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    cursor.close()
    conn.close()
