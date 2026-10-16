-- Set timezone to UTC
SET time_zone = '+00:00';

-- Employees table
CREATE TABLE IF NOT EXISTS employees (
    emp_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    department VARCHAR(100),
    designation VARCHAR(100),
    manager_id VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES employees(emp_id) ON DELETE SET NULL,
    INDEX idx_department (department),
    INDEX idx_manager (manager_id),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'employee') NOT NULL,
    emp_id VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE SET NULL,
    INDEX idx_username (username),
    INDEX idx_role (role),
    INDEX idx_emp_id (emp_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- TAS Records table
CREATE TABLE IF NOT EXISTS tas_records (
    tas_id INT AUTO_INCREMENT PRIMARY KEY,
    tas_number VARCHAR(30) UNIQUE NOT NULL,
    emp_id VARCHAR(20) NOT NULL,
    travel_from VARCHAR(255) NOT NULL,
    travel_to VARCHAR(255) NOT NULL,
    travel_date_start DATE NOT NULL,
    travel_date_end DATE NOT NULL,
    purpose TEXT NOT NULL,
    estimated_cost DECIMAL(10,2) NOT NULL,
    status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
    submitted_at TIMESTAMP NULL,
    reviewed_at TIMESTAMP NULL,
    reviewed_by INT,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_emp_id (emp_id),
    INDEX idx_tas_number (tas_number),
    INDEX idx_status (status),
    INDEX idx_submitted_at (submitted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- TAS Sequence table
CREATE TABLE IF NOT EXISTS tas_sequence (
    emp_id VARCHAR(20) PRIMARY KEY,
    last_sequence INT DEFAULT 0,
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Seed admin user with bcrypt hash for password 'admin123'
-- First insert an admin employee record
INSERT INTO employees (emp_id, name, email, department, designation, is_active) 
VALUES ('ADMIN', 'System Administrator', 'admin@tas-erp.com', 'IT', 'Administrator', TRUE)
ON DUPLICATE KEY UPDATE name=name;

-- Then insert admin user with bcrypt hash for 'admin123'
INSERT INTO users (username, password_hash, role, emp_id, is_active)
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7Plj3r9D4W', 'admin', 'ADMIN', TRUE)
ON DUPLICATE KEY UPDATE username=username;
