"""Utility functions for the TAS ERP application."""
from app.models import db, TASSequence
from sqlalchemy.exc import IntegrityError


def generate_tas_number(emp_id):
    """
    Generate unique TAS number in format: TAS-{EMPID}-{SEQ}
    Example: TAS-1987-0001
    
    Uses row-level locking to prevent race conditions.
    Retries up to 3 times on IntegrityError.
    """
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # Lock the sequence record for this employee
            seq_record = TASSequence.query.filter_by(emp_id=emp_id).with_for_update().first()
            
            if not seq_record:
                # Create new sequence record for this employee
                seq_record = TASSequence(emp_id=emp_id, last_sequence=0)
                db.session.add(seq_record)
                db.session.flush()  # Detect conflict immediately
            
            # Increment sequence
            seq_record.last_sequence += 1
            new_sequence = seq_record.last_sequence
            
            # Commit the transaction
            db.session.commit()
            
            # Format: TAS-EMPID-0001
            return f"TAS-{emp_id}-{new_sequence:04d}"
            
        except IntegrityError:
            # Race condition: another transaction created the record
            db.session.rollback()
            if attempt == max_retries - 1:
                raise RuntimeError(f"Failed to generate TAS number for {emp_id} after {max_retries} retries")
            continue
    
    raise RuntimeError(f"Failed to generate TAS number for {emp_id}")

