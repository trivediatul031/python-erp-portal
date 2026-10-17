-- ========================================
-- UPDATE TAS_RECORDS TABLE WITH NEW FIELDS
-- ========================================
-- Run this SQL in phpMyAdmin to add new fields to tas_records table

-- Add new columns to tas_records table
ALTER TABLE tas_records
ADD COLUMN emp_name VARCHAR(100) NULL AFTER emp_id,
ADD COLUMN department VARCHAR(100) NULL AFTER emp_name,
ADD COLUMN travel_type VARCHAR(20) NULL AFTER department;

-- Update existing records with data from employees table
UPDATE tas_records tr
INNER JOIN employees e ON tr.emp_id = e.emp_id
SET 
    tr.emp_name = e.name,
    tr.department = e.department,
    tr.travel_type = 'Domestic';  -- Default existing records to Domestic

-- Change purpose column from TEXT to VARCHAR(100) for dropdown
ALTER TABLE tas_records
MODIFY COLUMN purpose VARCHAR(100) NOT NULL;

-- Now make the new columns NOT NULL after populating them
ALTER TABLE tas_records
MODIFY COLUMN emp_name VARCHAR(100) NOT NULL,
MODIFY COLUMN department VARCHAR(100) NOT NULL,
MODIFY COLUMN travel_type VARCHAR(20) NOT NULL;

-- Verify the changes
SELECT 
    tas_id,
    tas_number,
    emp_id,
    emp_name,
    department,
    travel_type,
    purpose,
    status
FROM tas_records
LIMIT 5;
