-- Fix RLS Policies for LINE Bot to write data
-- Run this in Supabase SQL Editor

-- Allow service_role to insert/update line_users
CREATE POLICY "Allow service_role full access to line_users"
ON line_users
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Allow service_role to insert/update fire_reports
CREATE POLICY "Allow service_role full access to fire_reports"
ON fire_reports
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Allow service_role to insert/update line_user_sessions
CREATE POLICY "Allow service_role full access to line_user_sessions"
ON line_user_sessions
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Allow service_role to insert notification_logs
CREATE POLICY "Allow service_role full access to notification_logs"
ON notification_logs
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Allow public read access to fire_reports (for map display)
CREATE POLICY "Allow public read access to fire_reports"
ON fire_reports
FOR SELECT
TO anon, authenticated
USING (true);
