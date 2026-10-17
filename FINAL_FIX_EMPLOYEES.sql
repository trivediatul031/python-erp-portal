-- ========================================
-- FINAL FIX FOR EMPLOYEE LOGIN PASSWORDS
-- ========================================
-- Run this SQL in phpMyAdmin to fix all employee passwords
-- Password will be: admin123

-- Update all employee users with a fresh bcrypt hash
UPDATE users 
SET password_hash = '$2b$12$.jj.9iirzSSAWFaH9awnZuRA6EcIP5vjKbyqF1iZsPKBb7oWnWygO'
WHERE role = 'employee';

-- Verify the changes
SELECT 
    user_id,
    username,
    role,
    SUBSTRING(password_hash, 1, 30) as hash_preview,
    emp_id,
    is_active
FROM users
ORDER BY role DESC, username;
