-- ========================================
-- COMPLETE TAS_RECORDS TABLE UPDATE
-- ========================================
-- Run this in phpMyAdmin to update tas_records table structure

-- OPTION 1: If you have existing data and want to keep it
-- First backup your data
CREATE TABLE IF NOT EXISTS tas_records_backup AS SELECT * FROM tas_records;

-- Drop old table and create new structure
DROP TABLE IF EXISTS tas_records;

CREATE TABLE tas_records (
    tas_id INT AUTO_INCREMENT PRIMARY KEY,
    tas_number VARCHAR(30) UNIQUE NOT NULL,
    emp_id VARCHAR(20) NOT NULL,
    emp_name VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    travel_type VARCHAR(20) NOT NULL COMMENT 'Domestic or International',
    travel_mode VARCHAR(20) NOT NULL COMMENT 'Bus, Train, or Air',
    travel_date_start DATE NOT NULL,
    purpose VARCHAR(100) NOT NULL COMMENT 'Road Show, Event, Conference, Site Visit, Invest India Event',
    status VARCHAR(20) DEFAULT 'Pending' COMMENT 'Pending, Approved, or Rejected',
    submitted_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP NULL,
    reviewed_by INT NULL,
    rejection_reason TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id),
    FOREIGN KEY (reviewed_by) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- If you had data backed up, restore minimal fields (adjust as needed)
-- INSERT INTO tas_records (tas_number, emp_id, emp_name, department, travel_type, travel_mode, travel_date_start, purpose, status, submitted_at)
-- SELECT tas_number, emp_id, emp_name, department, travel_type, 'Bus', travel_date_start, purpose, status, submitted_at
-- FROM tas_records_backup;

-- Verify the structure
DESCRIBE tas_records;

SELECT 'TAS Records table updated successfully!' as message;
