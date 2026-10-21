"""
Migration script to update all TAS numbers from TAS- to TR- format.
Run this once to update existing records in the database.
"""
from app import create_app
from app.models import db, TASRecord

def update_tas_numbers():
    """Update all TAS numbers from TAS- prefix to TR- prefix."""
    app = create_app()
    
    with app.app_context():
        try:
            # Get all TAS records
            tas_records = TASRecord.query.all()
            
            if not tas_records:
                print("No TAS records found in database.")
                return
            
            print(f"Found {len(tas_records)} TAS records to update...")
            updated_count = 0
            
            for tas in tas_records:
                if tas.tas_number.startswith('TAS-'):
                    # Replace TAS- with TR-
                    old_number = tas.tas_number
                    new_number = tas.tas_number.replace('TAS-', 'TR-', 1)
                    tas.tas_number = new_number
                    updated_count += 1
                    print(f"  Updated: {old_number} -> {new_number}")
            
            # Commit all changes
            db.session.commit()
            
            print(f"\n✅ Successfully updated {updated_count} TAS records!")
            print(f"All TAS numbers now use TR- prefix format.")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error updating TAS numbers: {str(e)}")
            raise

if __name__ == '__main__':
    print("=" * 60)
    print("TAS Number Migration: TAS- → TR-")
    print("=" * 60)
    print()
    
    update_tas_numbers()
