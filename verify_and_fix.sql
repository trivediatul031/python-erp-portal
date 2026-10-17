-- Verify current table structure and fix any issues
DESCRIBE tas_records;

-- Check if timestamps have proper defaults
SHOW CREATE TABLE tas_records;

-- Fix timestamp columns to have proper defaults
ALTER TABLE tas_records
MODIFY COLUMN submitted_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
MODIFY COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
MODIFY COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

-- Verify the fix
SELECT 'Table structure updated!' as message;
DESCRIBE tas_records;
