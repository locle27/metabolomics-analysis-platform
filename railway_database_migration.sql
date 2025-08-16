-- =====================================================
-- Railway Database Schema Migration
-- =====================================================
-- 
-- This file contains SQL commands to fix the database schema mismatch
-- between the local development database and the Railway production database.
-- 
-- ISSUE: Column "contacted_at" and "notes" of relation "schedule_requests" do not exist
-- SOLUTION: Add the missing columns to match the SQLAlchemy model
-- 
-- =====================================================

-- Check current table structure (for reference)
-- Run this first to see current structure:
-- \d schedule_requests;

-- Add missing columns to schedule_requests table
-- These columns exist in the SQLAlchemy model but are missing from Railway database

-- 1. Add contacted_at column (nullable timestamp)
ALTER TABLE schedule_requests 
ADD COLUMN IF NOT EXISTS contacted_at TIMESTAMP WITHOUT TIME ZONE;

-- 2. Add notes column (nullable text)
ALTER TABLE schedule_requests 
ADD COLUMN IF NOT EXISTS notes TEXT;

-- 3. Verify the changes (optional - for manual verification)
-- \d schedule_requests;

-- =====================================================
-- Additional Safety Checks
-- =====================================================

-- Check if columns already exist (this will show an error if they don't exist, which is expected)
-- SELECT contacted_at, notes FROM schedule_requests LIMIT 1;

-- Update any existing records to have NULL values (they already will, but this confirms it)
-- UPDATE schedule_requests SET contacted_at = NULL, notes = NULL WHERE contacted_at IS NOT NULL OR notes IS NOT NULL;

-- =====================================================
-- Verification Queries
-- =====================================================

-- 1. Check table structure after migration
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'schedule_requests' 
ORDER BY ordinal_position;

-- 2. Count total records (should be unchanged)
SELECT COUNT(*) as total_schedule_requests FROM schedule_requests;

-- 3. Check that new columns are properly nullable
SELECT 
    COUNT(*) as total_records,
    COUNT(contacted_at) as records_with_contacted_at,
    COUNT(notes) as records_with_notes
FROM schedule_requests;

-- =====================================================
-- HOW TO RUN THESE COMMANDS ON RAILWAY:
-- =====================================================
-- 
-- Option 1: Railway Dashboard
-- 1. Go to your Railway project dashboard
-- 2. Click on your PostgreSQL service
-- 3. Go to the "Data" tab
-- 4. Open the "SQL Editor" 
-- 5. Paste and run the ALTER TABLE commands above
-- 
-- Option 2: External Database Tool (DBeaver, TablePlus, etc.)
-- 1. Get your database connection string from Railway
-- 2. Connect using your preferred database tool
-- 3. Run the ALTER TABLE commands
-- 
-- Option 3: Command Line (if you have psql installed)
-- 1. Get your DATABASE_URL from Railway environment variables
-- 2. Run: psql $DATABASE_URL
-- 3. Execute the ALTER TABLE commands
-- 
-- =====================================================
-- ROLLBACK COMMANDS (if needed)
-- =====================================================
-- 
-- If you need to undo these changes for any reason:
-- 
-- ALTER TABLE schedule_requests DROP COLUMN IF EXISTS contacted_at;
-- ALTER TABLE schedule_requests DROP COLUMN IF EXISTS notes;
-- 
-- WARNING: This will permanently delete any data in these columns!
-- 
-- =====================================================

-- Success message
SELECT 'Database schema migration completed successfully!' as status;