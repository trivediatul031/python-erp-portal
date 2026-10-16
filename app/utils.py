"""Utility functions for the TAS ERP application."""
from app.models import db, TASSequence
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger(__name__)


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


def cleanup_old_exports(upload_folder, hours=24):
    """
    Remove export files older than specified hours.
    
    Args:
        upload_folder: Path to the upload folder
        hours: Age threshold in hours (default: 24)
    """
    try:
        if not os.path.exists(upload_folder):
            logger.warning(f"Upload folder does not exist: {upload_folder}")
            return
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        deleted_count = 0
        
        for filename in os.listdir(upload_folder):
            if filename.startswith('tas_records_'):
                filepath = os.path.join(upload_folder, filename)
                try:
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if file_mtime < cutoff_time:
                        os.remove(filepath)
                        deleted_count += 1
                        logger.info(f"Deleted old export file: {filename}")
                except Exception as e:
                    logger.error(f"Error deleting file {filename}: {str(e)}")
        
        if deleted_count > 0:
            logger.info(f"Cleanup complete: removed {deleted_count} old export files")
        else:
            logger.info("Cleanup complete: no old files found")
            
    except Exception as e:
        logger.error(f"Error during cleanup_old_exports: {str(e)}", exc_info=True)

