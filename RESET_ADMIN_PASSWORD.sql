-- ============================================================
-- RESET ADMIN PASSWORD
-- ============================================================
-- Run this in phpMyAdmin to reset admin password to: admin123

-- First, check if admin user exists
SELECT user_id, username, role, is_active 
FROM users 
WHERE username = 'admin';

-- If admin exists, update the password
-- This hash is for password: admin123
UPDATE users 
SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7Plj3r9D4W',
    is_active = 1
WHERE username = 'admin';

-- If admin doesn't exist, create it
-- First ensure ADMIN employee exists
INSERT IGNORE INTO employees (emp_id, name, email, department, designation, is_active, created_at, updated_at)
VALUES ('ADMIN', 'System Administrator', 'admin@test.com', 'IT', 'Administrator', 1, NOW(), NOW());

-- Then create admin user
INSERT IGNORE INTO users (username, password_hash, role, emp_id, is_active, created_at, updated_at)
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7Plj3r9D4W', 'admin', 'ADMIN', 1, NOW(), NOW());

-- Verify the admin account
SELECT u.user_id, u.username, u.role, u.emp_id, e.name as employee_name, u.is_active
FROM users u
LEFT JOIN employees e ON u.emp_id = e.emp_id
WHERE u.username = 'admin';

-- Success message
SELECT 'Admin account ready! Login with username: admin, password: admin123' as message;
