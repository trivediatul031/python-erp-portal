-- ============================================================
-- RUN THIS IN PHPMYADMIN - TAS Records Table Migration
-- ============================================================
-- This updates the tas_records table to match the new simplified form

-- Step 1: Add new columns
ALTER TABLE tas_records
ADD COLUMN emp_name VARCHAR(100) NULL AFTER emp_id,
ADD COLUMN department VARCHAR(100) NULL AFTER emp_name,
ADD COLUMN travel_type VARCHAR(20) NULL AFTER department,
ADD COLUMN travel_mode VARCHAR(20) NULL AFTER travel_type;

-- Step 2: Populate new columns with data from employees table
UPDATE tas_records tr
INNER JOIN employees e ON tr.emp_id = e.emp_id
SET 
    tr.emp_name = e.name,
    tr.department = COALESCE(e.department, 'N/A'),
    tr.travel_type = 'Domestic',
    tr.travel_mode = 'Bus';

-- Step 3: Change purpose column from TEXT to VARCHAR(100)
ALTER TABLE tas_records
MODIFY COLUMN purpose VARCHAR(100) NOT NULL;

-- Step 4: Make new columns NOT NULL
ALTER TABLE tas_records
MODIFY COLUMN emp_name VARCHAR(100) NOT NULL,
MODIFY COLUMN department VARCHAR(100) NOT NULL,
MODIFY COLUMN travel_type VARCHAR(20) NOT NULL,
MODIFY COLUMN travel_mode VARCHAR(20) NOT NULL;

-- Step 5: Remove old columns that are no longer needed
ALTER TABLE tas_records
DROP COLUMN travel_from,
DROP COLUMN travel_to,
DROP COLUMN travel_date_end,
DROP COLUMN estimated_cost;

-- Step 6: Verify the changes
SELECT 
    'Migration complete!' as status,
    COUNT(*) as total_records
FROM tas_records;

-- Show updated structure
DESCRIBE tas_records;
