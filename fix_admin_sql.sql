-- Fix admin account in users table
-- This will make 'admin' a true super admin with access to admin dashboard

-- Update the admin user
UPDATE users 
SET 
    role = 'admin',
    emp_id = NULL,
    is_active = 1
WHERE username = 'admin';

-- Verify the change
SELECT 
    user_id,
    username,
    role,
    emp_id,
    is_active,
    'FIXED - Admin is now super admin' as status
FROM users 
WHERE username = 'admin';
