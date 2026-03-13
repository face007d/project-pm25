-- ============================================
-- Phase 2: Fire Reports & LINE Integration Schema
-- ระบบรับแจ้งจุดไฟไหม้ผ่าน LINE OA
-- ============================================

-- ============================================
-- Table 1: fire_reports (รายงานจุดไฟไหม้)
-- ============================================
CREATE TABLE IF NOT EXISTS fire_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- ข้อมูลผู้แจ้ง
    line_user_id TEXT NOT NULL,
    user_display_name TEXT,
    
    -- ข้อมูลตำแหน่ง
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    location_address TEXT,
    location_name TEXT,
    
    -- ข้อมูลรูปภาพ
    image_url TEXT NOT NULL,
    image_message_id TEXT,
    
    -- ข้อมูลเพิ่มเติม
    report_date DATE NOT NULL DEFAULT CURRENT_DATE,
    report_time TIME NOT NULL DEFAULT CURRENT_TIME,
    description TEXT,
    
    -- สถานะ
    status TEXT DEFAULT 'pending',  -- pending, verified, resolved, false_alarm
    severity TEXT DEFAULT 'medium', -- low, medium, high, critical
    
    -- ข้อมูลการตรวจสอบ
    verified_by TEXT,
    verified_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    
    -- Metadata
    pm25_value FLOAT,  -- ค่า PM2.5 ณ เวลาที่แจ้ง
    weather_data JSONB,
    notes TEXT,
    
    -- Constraints
    CONSTRAINT valid_latitude CHECK (latitude >= -90 AND latitude <= 90),
    CONSTRAINT valid_longitude CHECK (longitude >= -180 AND longitude <= 180),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'verified', 'resolved', 'false_alarm')),
    CONSTRAINT valid_severity CHECK (severity IN ('low', 'medium', 'high', 'critical'))
);

-- Indexes
CREATE INDEX idx_fire_reports_created_at ON fire_reports(created_at DESC);
CREATE INDEX idx_fire_reports_location ON fire_reports(latitude, longitude);
CREATE INDEX idx_fire_reports_status ON fire_reports(status);
CREATE INDEX idx_fire_reports_user ON fire_reports(line_user_id);
CREATE INDEX idx_fire_reports_date ON fire_reports(report_date DESC);

-- Spatial Index (สำหรับค้นหาจุดใกล้เคียง)
CREATE INDEX idx_fire_reports_geom ON fire_reports USING gist (
    ll_to_earth(latitude, longitude)
);

-- ============================================
-- Table 2: line_users (ผู้ใช้ LINE)
-- ============================================
CREATE TABLE IF NOT EXISTS line_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- ข้อมูล LINE
    line_user_id TEXT UNIQUE NOT NULL,
    display_name TEXT,
    picture_url TEXT,
    status_message TEXT,
    
    -- การตั้งค่า
    notification_enabled BOOLEAN DEFAULT TRUE,
    notification_time TIME DEFAULT '08:00:00',
    alert_threshold FLOAT DEFAULT 37.5,  -- แจ้งเตือนเมื่อ PM2.5 > ค่านี้
    
    -- สถิติ
    total_reports INTEGER DEFAULT 0,
    last_report_at TIMESTAMPTZ,
    last_active_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Metadata
    language TEXT DEFAULT 'th',
    location_preference TEXT,
    metadata JSONB
);

-- Indexes
CREATE INDEX idx_line_users_user_id ON line_users(line_user_id);
CREATE INDEX idx_line_users_notification ON line_users(notification_enabled) 
    WHERE notification_enabled = TRUE;

-- ============================================
-- Table 3: line_user_sessions (Session การส่งข้อมูล)
-- ============================================
CREATE TABLE IF NOT EXISTS line_user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '30 minutes',
    
    line_user_id TEXT NOT NULL,
    
    -- สถานะการส่งข้อมูล
    has_image BOOLEAN DEFAULT FALSE,
    has_location BOOLEAN DEFAULT FALSE,
    
    -- ข้อมูลชั่วคราว
    image_url TEXT,
    image_message_id TEXT,
    latitude FLOAT,
    longitude FLOAT,
    
    -- สถานะ
    is_complete BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_sessions_user_id ON line_user_sessions(line_user_id);
CREATE INDEX idx_sessions_expires ON line_user_sessions(expires_at);

-- Auto-delete expired sessions
CREATE INDEX idx_sessions_cleanup ON line_user_sessions(expires_at) 
    WHERE is_complete = FALSE;

-- ============================================
-- Table 4: notification_logs (ประวัติการแจ้งเตือน)
-- ============================================
CREATE TABLE IF NOT EXISTS notification_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    notification_type TEXT NOT NULL, -- daily_report, high_pm25, fire_alert
    
    -- ผู้รับ
    line_user_id TEXT,
    is_broadcast BOOLEAN DEFAULT FALSE,
    total_recipients INTEGER,
    
    -- เนื้อหา
    message_text TEXT NOT NULL,
    pm25_value FLOAT,
    forecast_value FLOAT,
    
    -- สถานะ
    status TEXT DEFAULT 'sent', -- sent, failed, pending
    error_message TEXT,
    
    -- Metadata
    metadata JSONB
);

-- Indexes
CREATE INDEX idx_notification_logs_created ON notification_logs(created_at DESC);
CREATE INDEX idx_notification_logs_type ON notification_logs(notification_type);
CREATE INDEX idx_notification_logs_user ON notification_logs(line_user_id);

-- ============================================
-- Functions & Triggers
-- ============================================

-- Function: อัปเดต updated_at อัตโนมัติ
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers
CREATE TRIGGER update_fire_reports_updated_at
    BEFORE UPDATE ON fire_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_line_users_updated_at
    BEFORE UPDATE ON line_users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function: อัปเดตสถิติผู้ใช้เมื่อมีรายงานใหม่
CREATE OR REPLACE FUNCTION update_user_report_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE line_users
    SET 
        total_reports = total_reports + 1,
        last_report_at = NEW.created_at
    WHERE line_user_id = NEW.line_user_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger
CREATE TRIGGER trigger_update_user_stats
    AFTER INSERT ON fire_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_user_report_stats();

-- Function: ลบ sessions ที่หมดอายุ
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS void AS $$
BEGIN
    DELETE FROM line_user_sessions
    WHERE expires_at < NOW()
      AND is_complete = FALSE;
END;
$$ LANGUAGE plpgsql;

-- Function: คำนวณระยะทางระหว่างจุด (km)
CREATE OR REPLACE FUNCTION calculate_distance(
    lat1 FLOAT,
    lon1 FLOAT,
    lat2 FLOAT,
    lon2 FLOAT
)
RETURNS FLOAT AS $$
BEGIN
    RETURN earth_distance(
        ll_to_earth(lat1, lon1),
        ll_to_earth(lat2, lon2)
    ) / 1000.0; -- แปลงเป็น km
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Views สำหรับ Query ที่ใช้บ่อย
-- ============================================

-- View: รายงานที่รอตรวจสอบ
CREATE OR REPLACE VIEW v_pending_reports AS
SELECT 
    fr.*,
    lu.display_name as reporter_name,
    lu.total_reports as reporter_total_reports
FROM fire_reports fr
LEFT JOIN line_users lu ON fr.line_user_id = lu.line_user_id
WHERE fr.status = 'pending'
ORDER BY fr.created_at DESC;

-- View: รายงานวันนี้
CREATE OR REPLACE VIEW v_today_reports AS
SELECT 
    fr.*,
    lu.display_name as reporter_name
FROM fire_reports fr
LEFT JOIN line_users lu ON fr.line_user_id = lu.line_user_id
WHERE fr.report_date = CURRENT_DATE
ORDER BY fr.created_at DESC;

-- View: สถิติรายงานตามสถานะ
CREATE OR REPLACE VIEW v_report_statistics AS
SELECT 
    report_date,
    COUNT(*) as total_reports,
    COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
    COUNT(*) FILTER (WHERE status = 'verified') as verified_count,
    COUNT(*) FILTER (WHERE status = 'resolved') as resolved_count,
    COUNT(*) FILTER (WHERE status = 'false_alarm') as false_alarm_count,
    COUNT(DISTINCT line_user_id) as unique_reporters
FROM fire_reports
GROUP BY report_date
ORDER BY report_date DESC;

-- View: ผู้ใช้ที่เปิดการแจ้งเตือน
CREATE OR REPLACE VIEW v_notification_subscribers AS
SELECT 
    line_user_id,
    display_name,
    notification_time,
    alert_threshold,
    last_active_at
FROM line_users
WHERE notification_enabled = TRUE
ORDER BY notification_time;

-- ============================================
-- Row Level Security (RLS)
-- ============================================

-- Enable RLS
ALTER TABLE fire_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE line_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_logs ENABLE ROW LEVEL SECURITY;

-- Policy: อนุญาตให้ทุกคนอ่านรายงานไฟไหม้
CREATE POLICY "Allow public read fire reports" 
    ON fire_reports FOR SELECT 
    USING (true);

-- Policy: เฉพาะ authenticated users เท่านั้นที่เขียนได้
CREATE POLICY "Allow authenticated insert fire reports" 
    ON fire_reports FOR INSERT 
    WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated update fire reports" 
    ON fire_reports FOR UPDATE 
    USING (auth.role() = 'authenticated');

-- ============================================
-- Sample Data (Optional - for testing)
-- ============================================

-- Insert sample fire report
-- INSERT INTO fire_reports (
--     line_user_id,
--     user_display_name,
--     latitude,
--     longitude,
--     location_name,
--     image_url,
--     description,
--     severity
-- ) VALUES (
--     'U1234567890',
--     'ทดสอบ',
--     17.4065,
--     104.7686,
--     'นครพนม',
--     'https://example.com/fire.jpg',
--     'พบจุดไฟไหม้ใกล้บ้าน',
--     'medium'
-- );

-- ============================================
-- Useful Queries
-- ============================================

-- Query 1: ดูรายงานล่าสุด 10 รายการ
-- SELECT * FROM fire_reports ORDER BY created_at DESC LIMIT 10;

-- Query 2: ดูรายงานที่รอตรวจสอบ
-- SELECT * FROM v_pending_reports;

-- Query 3: ดูรายงานวันนี้
-- SELECT * FROM v_today_reports;

-- Query 4: หาจุดไฟไหม้ใกล้เคียง (รัศมี 5 km)
-- SELECT 
--     *,
--     calculate_distance(17.4065, 104.7686, latitude, longitude) as distance_km
-- FROM fire_reports
-- WHERE calculate_distance(17.4065, 104.7686, latitude, longitude) < 5
-- ORDER BY distance_km;

-- Query 5: สถิติรายงานรายวัน
-- SELECT * FROM v_report_statistics WHERE report_date >= CURRENT_DATE - INTERVAL '7 days';

-- Query 6: ผู้ใช้ที่แจ้งเหตุบ่อยที่สุด
-- SELECT 
--     line_user_id,
--     display_name,
--     total_reports,
--     last_report_at
-- FROM line_users
-- WHERE total_reports > 0
-- ORDER BY total_reports DESC
-- LIMIT 10;

-- ============================================
-- Maintenance
-- ============================================

-- ลบ sessions ที่หมดอายุ (รันเป็นระยะ)
-- SELECT cleanup_expired_sessions();

-- ลบรายงานเก่ามากกว่า 1 ปี (ถ้าต้องการ)
-- DELETE FROM fire_reports 
-- WHERE created_at < NOW() - INTERVAL '1 year' 
--   AND status IN ('resolved', 'false_alarm');

-- ============================================
-- Comments
-- ============================================

COMMENT ON TABLE fire_reports IS 'เก็บรายงานจุดไฟไหม้ที่ชาวบ้านแจ้งผ่าน LINE OA';
COMMENT ON TABLE line_users IS 'ข้อมูลผู้ใช้ LINE และการตั้งค่าการแจ้งเตือน';
COMMENT ON TABLE line_user_sessions IS 'Session ชั่วคราวสำหรับเก็บสถานะการส่งรูป+พิกัด';
COMMENT ON TABLE notification_logs IS 'ประวัติการส่งการแจ้งเตือนทั้งหมด';

-- ============================================
-- End of Schema
-- ============================================
