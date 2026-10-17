-- ============================================================
-- COMPLETE FIX - Run this entire script in phpMyAdmin
-- ============================================================

-- Step 1: Check current structure
SELECT 'BEFORE MIGRATION:' as status;
DESCRIBE tas_records;

-- Step 2: Add new columns (emp_name, department, travel_type, travel_mode)
-- Use IF NOT EXISTS logic by checking if column exists first

-- Add emp_name if it doesn't exist
SET @exist := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'tas_erp' 
    AND TABLE_NAME = 'tas_records' 
    AND COLUMN_NAME = 'emp_name');

SET @sqlstmt := IF(@exist = 0, 
    'ALTER TABLE tas_records ADD COLUMN emp_name VARCHAR(100) NULL AFTER emp_id', 
    'SELECT ''emp_name already exists'' as status');
PREPARE stmt FROM @sqlstmt;
EXECUTE stmt;

-- Add department if it doesn't exist
SET @exist := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'tas_erp' 
    AND TABLE_NAME = 'tas_records' 
    AND COLUMN_NAME = 'department');

SET @sqlstmt := IF(@exist = 0, 
    'ALTER TABLE tas_records ADD COLUMN department VARCHAR(100) NULL AFTER emp_name', 
    'SELECT ''department already exists'' as status');
PREPARE stmt FROM @sqlstmt;
EXECUTE stmt;

-- Add travel_type if it doesn't exist
SET @exist := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'tas_erp' 
    AND TABLE_NAME = 'tas_records' 
    AND COLUMN_NAME = 'travel_type');

SET @sqlstmt := IF(@exist = 0, 
    'ALTER TABLE tas_records ADD COLUMN travel_type VARCHAR(20) NULL AFTER department', 
    'SELECT ''travel_type already exists'' as status');
PREPARE stmt FROM @sqlstmt;
EXECUTE stmt;

-- Add travel_mode if it doesn't exist
SET @exist := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'tas_erp' 
    AND TABLE_NAME = 'tas_records' 
    AND COLUMN_NAME = 'travel_mode');

SET @sqlstmt := IF(@exist = 0, 
    'ALTER TABLE tas_records ADD COLUMN travel_mode VARCHAR(20) NULL AFTER travel_type', 
    'SELECT ''travel_mode already exists'' as status');
PREPARE stmt FROM @sqlstmt;
EXECUTE stmt;

-- Step 3: Update existing records with data from employees table
UPDATE tas_records tr
INNER JOIN employees e ON tr.emp_id = e.emp_id
SET 
    tr.emp_name = e.name,
    tr.department = COALESCE(e.department, 'N/A'),
    tr.travel_type = 'Domestic',
    tr.travel_mode = 'Bus'
WHERE tr.emp_name IS NULL;

-- Step 4: Change purpose from TEXT to VARCHAR(100)
ALTER TABLE tas_records
MODIFY COLUMN purpose VARCHAR(100) NOT NULL;

-- Step 5: Make new columns NOT NULL
ALTER TABLE tas_records
MODIFY COLUMN emp_name VARCHAR(100) NOT NULL,
MODIFY COLUMN department VARCHAR(100) NOT NULL,
MODIFY COLUMN travel_type VARCHAR(20) NOT NULL,
MODIFY COLUMN travel_mode VARCHAR(20) NOT NULL;

-- Step 6: Fix timestamp columns
ALTER TABLE tas_records
MODIFY COLUMN submitted_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
MODIFY COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
MODIFY COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

-- Step 7: Remove old columns if they exist
SET @exist := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'tas_erp' 
    AND TABLE_NAME = 'tas_records' 
    AND COLUMN_NAME = 'travel_from');

SET @sqlstmt := IF(@exist > 0, 
    'ALTER TABLE tas_records DROP COLUMN travel_from', 
    'SELECT ''travel_from already removed'' as status');
PREPARE stmt FROM @sqlstmt;
EXECUTE stmt;

SET @exist := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'tas_erp' 
    AND TABLE_NAME = 'tas_records' 
    AND COLUMN_NAME = 'travel_to');

SET @sqlstmt := IF(@exist > 0, 
    'ALTER TABLE tas_records DROP COLUMN travel_to', 
    'SELECT ''travel_to already removed'' as status');
PREPARE stmt FROM @sqlstmt;
EXECUTE stmt;

SET @exist := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'tas_erp' 
    AND TABLE_NAME = 'tas_records' 
    AND COLUMN_NAME = 'travel_date_end');

SET @sqlstmt := IF(@exist > 0, 
    'ALTER TABLE tas_records DROP COLUMN travel_date_end', 
    'SELECT ''travel_date_end already removed'' as status');
PREPARE stmt FROM @sqlstmt;
EXECUTE stmt;

SET @exist := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'tas_erp' 
    AND TABLE_NAME = 'tas_records' 
    AND COLUMN_NAME = 'estimated_cost');

SET @sqlstmt := IF(@exist > 0, 
    'ALTER TABLE tas_records DROP COLUMN estimated_cost', 
    'SELECT ''estimated_cost already removed'' as status');
PREPARE stmt FROM @sqlstmt;
EXECUTE stmt;

-- Step 8: Verify final structure
SELECT 'AFTER MIGRATION:' as status;
DESCRIBE tas_records;

-- Step 9: Show column list
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'tas_erp' 
  AND TABLE_NAME = 'tas_records'
ORDER BY ORDINAL_POSITION;

SELECT '✓ MIGRATION COMPLETE!' as message;
