-- ============================================================
-- SIMPLE FIX - Run each ALTER TABLE one at a time
-- ============================================================
-- Copy and paste ONE statement at a time into phpMyAdmin SQL tab

-- 1. Add emp_name column
ALTER TABLE tas_records 
ADD COLUMN emp_name VARCHAR(100) NULL AFTER emp_id;

-- 2. Add department column
ALTER TABLE tas_records 
ADD COLUMN department VARCHAR(100) NULL AFTER emp_name;

-- 3. Add travel_type column
ALTER TABLE tas_records 
ADD COLUMN travel_type VARCHAR(20) NULL AFTER department;

-- 4. Add travel_mode column (THIS IS THE MISSING ONE!)
ALTER TABLE tas_records 
ADD COLUMN travel_mode VARCHAR(20) NULL AFTER travel_type;

-- 5. Fill in data for existing records
UPDATE tas_records tr
INNER JOIN employees e ON tr.emp_id = e.emp_id
SET 
    tr.emp_name = e.name,
    tr.department = COALESCE(e.department, 'N/A'),
    tr.travel_type = 'Domestic',
    tr.travel_mode = 'Bus'
WHERE tr.emp_name IS NULL;

-- 6. Make columns required
ALTER TABLE tas_records
MODIFY COLUMN emp_name VARCHAR(100) NOT NULL;

ALTER TABLE tas_records
MODIFY COLUMN department VARCHAR(100) NOT NULL;

ALTER TABLE tas_records
MODIFY COLUMN travel_type VARCHAR(20) NOT NULL;

ALTER TABLE tas_records
MODIFY COLUMN travel_mode VARCHAR(20) NOT NULL;

-- 7. Fix purpose column
ALTER TABLE tas_records
MODIFY COLUMN purpose VARCHAR(100) NOT NULL;

-- 8. Fix timestamps
ALTER TABLE tas_records
MODIFY COLUMN submitted_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE tas_records
MODIFY COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE tas_records
MODIFY COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

-- 9. Remove old columns
ALTER TABLE tas_records DROP COLUMN travel_from;
ALTER TABLE tas_records DROP COLUMN travel_to;
ALTER TABLE tas_records DROP COLUMN travel_date_end;
ALTER TABLE tas_records DROP COLUMN estimated_cost;

-- 10. Verify it worked
DESCRIBE tas_records;
