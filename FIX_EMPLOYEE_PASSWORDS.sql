-- FIX ALL EMPLOYEE PASSWORDS
-- This SQL updates all employee user passwords to match the working admin password
-- Password will be: admin123

-- Get the working password hash from admin
SET @working_hash = (SELECT password_hash FROM users WHERE username = 'admin' LIMIT 1);

-- Update all employee users to use the same working hash
UPDATE users 
SET password_hash = @working_hash
WHERE role = 'employee';

-- Verify the update
SELECT username, role, 
       CASE WHEN password_hash = @working_hash THEN 'FIXED ✓' ELSE 'DIFFERENT' END as status
FROM users;
