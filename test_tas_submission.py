"""
Test TAS submission to identify the exact error
"""

from app import create_app, db
from app.models import TASRecord, Employee
from datetime import date, datetime

app = create_app()

def test_submission():
    with app.app_context():
        print("=" * 60)
        print("TESTING TAS SUBMISSION")
        print("=" * 60)
        
        # Check if employee exists
        emp_id = '1987'
        employee = Employee.query.get(emp_id)
        
        if not employee:
            print(f"\n✗ Employee {emp_id} not found!")
            print("Creating test employee...")
            # You may need to create one first
            return
        
        print(f"\n✓ Found employee: {employee.name} ({employee.emp_id})")
        print(f"  Department: {employee.department}")
        
        # Try to create a TAS record with the new structure
        print("\nAttempting to create TAS record...")
        
        try:
            tas = TASRecord(
                tas_number='TAS-TEST-9999',
                emp_id=emp_id,
                emp_name=employee.name,
                department=employee.department or 'N/A',
                travel_type='Domestic',
                travel_mode='Bus',
                travel_date_start=date.today(),
                purpose='Conference',
                status='Pending'
            )
            
            print("✓ TAS object created successfully")
            print(f"  TAS Number: {tas.tas_number}")
            print(f"  Employee: {tas.emp_name}")
            print(f"  Department: {tas.department}")
            print(f"  Travel Type: {tas.travel_type}")
            print(f"  Travel Mode: {tas.travel_mode}")
            print(f"  Purpose: {tas.purpose}")
            print(f"  Date: {tas.travel_date_start}")
            
            # Try to add to database
            print("\nAttempting database insert...")
            db.session.add(tas)
            db.session.commit()
            
            print("✓ TAS record saved to database successfully!")
            print("\n" + "=" * 60)
            print("SUCCESS! TAS submission works correctly.")
            print("=" * 60)
            
            # Clean up test record
            db.session.delete(tas)
            db.session.commit()
            print("\n✓ Test record cleaned up")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ ERROR occurred: {type(e).__name__}")
            print(f"  Message: {str(e)}")
            print("\n" + "=" * 60)
            
            import traceback
            print("\nFull traceback:")
            print("-" * 60)
            traceback.print_exc()
            
            # Check what columns are expected vs what exists
            print("\n" + "=" * 60)
            print("CHECKING DATABASE COLUMNS")
            print("=" * 60)
            
            from sqlalchemy import text
            result = db.session.execute(text("DESCRIBE tas_records"))
            print("\nColumns in database:")
            for row in result:
                print(f"  - {row[0]}")

if __name__ == '__main__':
    test_submission()
