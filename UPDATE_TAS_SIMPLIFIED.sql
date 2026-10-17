-- ========================================
-- UPDATE TAS_RECORDS TABLE - SIMPLIFIED VERSION
-- ========================================
-- This updates the tas_records table to remove unnecessary fields
-- and add travel_mode dropdown

-- First, add the new travel_mode column if using the previous migration
-- Skip this if you haven't run UPDATE_TAS_FIELDS.sql yet
ALTER TABLE tas_records
ADD COLUMN IF NOT EXISTS travel_mode VARCHAR(20) NULL;

-- If you already ran UPDATE_TAS_FIELDS.sql, drop the removed columns
ALTER TABLE tas_records
DROP COLUMN IF EXISTS travel_from,
DROP COLUMN IF EXISTS travel_to,
DROP COLUMN IF EXISTS travel_date_end,
DROP COLUMN IF EXISTS estimated_cost;

-- Update existing records to set default travel_mode
UPDATE tas_records
SET travel_mode = 'Bus'
WHERE travel_mode IS NULL;

-- Make travel_mode NOT NULL
ALTER TABLE tas_records
MODIFY COLUMN travel_mode VARCHAR(20) NOT NULL;

-- Verify the final structure
DESCRIBE tas_records;

-- Show sample data
SELECT 
    tas_id,
    tas_number,
    emp_name,
    department,
    travel_type,
    travel_mode,
    purpose,
    travel_date_start,
    status
FROM tas_records
LIMIT 5;
