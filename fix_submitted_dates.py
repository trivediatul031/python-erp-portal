"""
Fix script to set submitted_at dates for TAS records that have NULL values.
Uses the record creation timestamp or current time.
"""
from app import create_app
from app.models import db, TASRecord
from datetime import datetime

def fix_submitted_dates():
    """Set submitted_at for all TAS records with NULL values."""
    app = create_app()
    
    with app.app_context():
        try:
            # Get all TAS records with NULL submitted_at
            tas_records = TASRecord.query.filter(TASRecord.submitted_at.is_(None)).all()
            
            if not tas_records:
                print("✅ All TAS records have submitted_at dates. No fix needed.")
                return
            
            print(f"Found {len(tas_records)} TAS records with missing submitted_at...")
            updated_count = 0
            
            for tas in tas_records:
                # Set submitted_at to current time
                # In a real scenario, you might want to use created_at if available
                tas.submitted_at = datetime.utcnow()
                updated_count += 1
                print(f"  Fixed: {tas.tas_number} -> {tas.submitted_at.strftime('%d %b %Y, %I:%M %p')}")
            
            # Commit all changes
            db.session.commit()
            
            print(f"\n✅ Successfully updated {updated_count} TAS records!")
            print(f"All TAS records now have submitted_at dates.")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error fixing submitted dates: {str(e)}")
            raise

if __name__ == '__main__':
    print("=" * 60)
    print("Fix Missing Submitted Dates")
    print("=" * 60)
    print()
    
    fix_submitted_dates()
