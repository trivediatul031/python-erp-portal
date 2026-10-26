"""Utility functions for the TAS ERP application."""
from app.models import db
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger(__name__)


def generate_tas_number(emp_code):
    """
    Generate unique TR (Travel Request) number for given employee code in format TR-{emp_code}-{seq}.
    Example: TR-1943-0001
    
    Uses database query to find the highest sequence number for the employee globally (not per-date),
    then increments it. This approach works without requiring a separate sequences table.
    
    IMPORTANT: Must be called within active transaction. Does NOT commit internally - 
    caller must commit. The uniqueness constraint on tas_records.tas_number ensures no duplicates.
    
    Args:
        emp_code: Employee code string
        
    Returns:
        str: TR number in format TR-{emp_code}-{seq:04d}
        
    Raises:
        RuntimeError: If TR number generation fails after max retries
    """
    max_retries = 5
    prefix = "TR-" + str(emp_code) + "-"
    prefix_length = len(prefix)
    
    for attempt in range(max_retries):
        try:
            # Get the highest sequence number for this employee (all time, not just today)
            # Using LIKE with % to match all sequences for this emp_code
            # Extract numeric part after prefix and find MAX
            result = db.session.execute(
                text("""
                    SELECT COALESCE(MAX(
                        CAST(SUBSTRING(tas_number, :prefix_len + 1) AS UNSIGNED)
                    ), 0) as max_seq
                    FROM tas_records 
                    WHERE tas_number LIKE :pattern
                """),
                {
                    "prefix_len": prefix_length,
                    "pattern": prefix + "%"
                }
            ).fetchone()
            
            # Get next sequence number
            last_seq = result[0] if result and result[0] is not None else 0
            sequence = last_seq + 1
            
            # Format: TR-{emp_code}-{seq:04d}
            tas_number = prefix + str(sequence).zfill(4)
            
            return tas_number
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError('Failed to generate TR number after ' + str(max_retries) + ' retries: ' + str(e))
            # Wait a bit before retry to avoid race conditions
            import time
            time.sleep(0.1 * (attempt + 1))
    
    raise RuntimeError('Failed to generate TR number after ' + str(max_retries) + ' retries')


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

