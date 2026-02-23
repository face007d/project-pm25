-- ============================================
-- PM2.5 Air Quality Forecasting Database Schema
-- สำหรับ Supabase PostgreSQL
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- Table 1: pm25_predictions
-- เก็บข้อมูลการพยากรณ์ PM2.5
-- ============================================
CREATE TABLE IF NOT EXISTS pm25_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- วันที่ข้อมูล
    prediction_date DATE NOT NULL,  -- วันที่ทำการพยากรณ์
    target_date DATE NOT NULL,      -- วันที่พยากรณ์ไว้ (พรุ่งนี้)
    
    -- ค่า PM2.5
    predicted_value FLOAT NOT NULL,  -- ค่าที่พยากรณ์
    actual_value FLOAT,              -- ค่าจริงที่เกิดขึ้น (อัปเดทภายหลัง)
    
    -- ข้อมูลเพิ่มเติม
    input_values JSONB NOT NULL,     -- ข้อมูล 3 วันที่ใช้พยากรณ์ {"day1": 22.4, "day2": 39.7, "day3": 25.0}
    model_version TEXT NOT NULL,     -- เวอร์ชันของ model
    location TEXT DEFAULT 'Nakhon Phanom',
    data_source TEXT DEFAULT 'LSTM Model',
    
    -- Metadata
    confidence_score FLOAT,          -- ความมั่นใจของการพยากรณ์ (0-1)
    notes TEXT,
    
    -- Constraints
    CONSTRAINT unique_prediction UNIQUE(prediction_date, target_date, location),
    CONSTRAINT valid_pm25_predicted CHECK (predicted_value >= 0),
    CONSTRAINT valid_pm25_actual CHECK (actual_value IS NULL OR actual_value >= 0)
);

-- Indexes สำหรับ query ที่เร็วขึ้น
CREATE INDEX idx_predictions_target_date ON pm25_predictions(target_date);
CREATE INDEX idx_predictions_created_at ON pm25_predictions(created_at DESC);
CREATE INDEX idx_predictions_location ON pm25_predictions(location);
CREATE INDEX idx_predictions_pending_actual ON pm25_predictions(target_date) WHERE actual_value IS NULL;

-- ============================================
-- Table 2: pm25_actual_readings
-- เก็บข้อมูลค่า PM2.5 จริงที่วัดได้
-- ============================================
CREATE TABLE IF NOT EXISTS pm25_actual_readings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- วันที่และค่า
    reading_date DATE NOT NULL,
    reading_time TIMESTAMPTZ,
    pm25_value FLOAT NOT NULL,
    
    -- ระดับคุณภาพอากาศ
    aqi_level TEXT,  -- 'ดีมาก', 'ดี', 'ปานกลาง', 'เริ่มมีผลกระทบ', 'มีผลกระทบต่อสุขภาพ'
    aqi_color TEXT,  -- '#28b4d8', '#2ecc71', '#f1c40f', '#e67e22', '#e74c3c'
    
    -- ข้อมูลสภาพอากาศเพิ่มเติม
    temperature FLOAT,
    humidity FLOAT,
    wind_speed FLOAT,
    wind_direction TEXT,
    pressure FLOAT,
    
    -- ที่มาของข้อมูล
    location TEXT DEFAULT 'Nakhon Phanom',
    data_source TEXT DEFAULT 'WAQI API',
    station_id TEXT,
    
    -- Metadata
    raw_data JSONB,  -- เก็บข้อมูลดิบทั้งหมดจาก API
    notes TEXT,
    
    -- Constraints
    CONSTRAINT unique_reading UNIQUE(reading_date, location),
    CONSTRAINT valid_pm25_reading CHECK (pm25_value >= 0)
);

-- Indexes
CREATE INDEX idx_actual_reading_date ON pm25_actual_readings(reading_date DESC);
CREATE INDEX idx_actual_location ON pm25_actual_readings(location);
CREATE INDEX idx_actual_created_at ON pm25_actual_readings(created_at DESC);

-- ============================================
-- Table 3: prediction_accuracy_log
-- เก็บข้อมูลความแม่นยำของการพยากรณ์
-- ============================================
CREATE TABLE IF NOT EXISTS prediction_accuracy_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prediction_id UUID REFERENCES pm25_predictions(id) ON DELETE CASCADE,
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- ค่าความผิดพลาด
    error_value FLOAT NOT NULL,           -- |predicted - actual|
    error_percentage FLOAT,               -- (error/actual) * 100
    squared_error FLOAT,                  -- (predicted - actual)^2
    
    -- Metrics
    mae FLOAT,   -- Mean Absolute Error
    rmse FLOAT,  -- Root Mean Square Error
    mape FLOAT,  -- Mean Absolute Percentage Error
    
    -- Classification
    is_accurate BOOLEAN,  -- ถือว่าแม่นยำหรือไม่ (error < threshold)
    accuracy_threshold FLOAT DEFAULT 10.0,
    
    -- Metadata
    notes TEXT
);

-- Indexes
CREATE INDEX idx_accuracy_prediction_id ON prediction_accuracy_log(prediction_id);
CREATE INDEX idx_accuracy_calculated_at ON prediction_accuracy_log(calculated_at DESC);
CREATE INDEX idx_accuracy_is_accurate ON prediction_accuracy_log(is_accurate);

-- ============================================
-- Table 4: model_versions
-- เก็บข้อมูลเวอร์ชันของ Model
-- ============================================
CREATE TABLE IF NOT EXISTS model_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    version TEXT UNIQUE NOT NULL,
    model_name TEXT NOT NULL,
    model_type TEXT DEFAULT 'LSTM',
    
    -- Performance metrics
    training_mae FLOAT,
    training_rmse FLOAT,
    validation_mae FLOAT,
    validation_rmse FLOAT,
    
    -- Model info
    architecture JSONB,  -- {"layers": [...], "params": {...}}
    training_data_size INTEGER,
    training_date DATE,
    
    -- Status
    is_active BOOLEAN DEFAULT FALSE,
    is_production BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    description TEXT,
    notes TEXT
);

CREATE INDEX idx_model_versions_active ON model_versions(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_model_versions_production ON model_versions(is_production) WHERE is_production = TRUE;

-- ============================================
-- Table 5: alert_logs
-- เก็บประวัติการแจ้งเตือน
-- ============================================
CREATE TABLE IF NOT EXISTS alert_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    alert_type TEXT NOT NULL,  -- 'high_pm25', 'model_accuracy_low', 'data_missing'
    severity TEXT NOT NULL,    -- 'info', 'warning', 'critical'
    
    -- Alert details
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    pm25_value FLOAT,
    threshold_value FLOAT,
    
    -- Notification
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_channel TEXT,  -- 'line', 'email', 'sms'
    notification_status TEXT,
    
    -- Related data
    prediction_id UUID REFERENCES pm25_predictions(id),
    location TEXT DEFAULT 'Nakhon Phanom',
    
    -- Metadata
    metadata JSONB
);

CREATE INDEX idx_alert_created_at ON alert_logs(created_at DESC);
CREATE INDEX idx_alert_type ON alert_logs(alert_type);
CREATE INDEX idx_alert_severity ON alert_logs(severity);

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

-- Trigger สำหรับ pm25_predictions
CREATE TRIGGER update_pm25_predictions_updated_at
    BEFORE UPDATE ON pm25_predictions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger สำหรับ pm25_actual_readings
CREATE TRIGGER update_pm25_actual_readings_updated_at
    BEFORE UPDATE ON pm25_actual_readings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function: คำนวณ AQI Level จาก PM2.5 value
CREATE OR REPLACE FUNCTION calculate_aqi_level(pm25_value FLOAT)
RETURNS TABLE(level TEXT, color TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE 
            WHEN pm25_value <= 15.0 THEN 'ดีมาก'
            WHEN pm25_value <= 25.0 THEN 'ดี'
            WHEN pm25_value <= 37.5 THEN 'ปานกลาง'
            WHEN pm25_value <= 75.0 THEN 'เริ่มมีผลกระทบ'
            ELSE 'มีผลกระทบต่อสุขภาพ'
        END,
        CASE 
            WHEN pm25_value <= 15.0 THEN '#28b4d8'
            WHEN pm25_value <= 25.0 THEN '#2ecc71'
            WHEN pm25_value <= 37.5 THEN '#f1c40f'
            WHEN pm25_value <= 75.0 THEN '#e67e22'
            ELSE '#e74c3c'
        END;
END;
$$ LANGUAGE plpgsql;

-- Function: คำนวณความแม่นยำเมื่อมีค่าจริง
CREATE OR REPLACE FUNCTION calculate_prediction_accuracy()
RETURNS TRIGGER AS $$
DECLARE
    error_val FLOAT;
    error_pct FLOAT;
    sq_error FLOAT;
BEGIN
    -- คำนวณเมื่อมีการอัปเดต actual_value
    IF NEW.actual_value IS NOT NULL AND OLD.actual_value IS NULL THEN
        error_val := ABS(NEW.predicted_value - NEW.actual_value);
        error_pct := (error_val / NULLIF(NEW.actual_value, 0)) * 100;
        sq_error := POWER(NEW.predicted_value - NEW.actual_value, 2);
        
        -- บันทึกลง prediction_accuracy_log
        INSERT INTO prediction_accuracy_log (
            prediction_id,
            error_value,
            error_percentage,
            squared_error,
            is_accurate
        ) VALUES (
            NEW.id,
            error_val,
            error_pct,
            sq_error,
            error_val < 10.0  -- ถือว่าแม่นยำถ้า error < 10
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: คำนวณความแม่นยำอัตโนมัติ
CREATE TRIGGER trigger_calculate_accuracy
    AFTER UPDATE ON pm25_predictions
    FOR EACH ROW
    WHEN (NEW.actual_value IS NOT NULL AND OLD.actual_value IS NULL)
    EXECUTE FUNCTION calculate_prediction_accuracy();

-- ============================================
-- Views สำหรับ Query ที่ใช้บ่อย
-- ============================================

-- View: ข้อมูลพยากรณ์พร้อมค่าจริง
CREATE OR REPLACE VIEW v_predictions_with_actual AS
SELECT 
    p.id,
    p.prediction_date,
    p.target_date,
    p.predicted_value,
    p.actual_value,
    p.model_version,
    p.location,
    a.error_value,
    a.error_percentage,
    a.is_accurate,
    CASE 
        WHEN p.actual_value IS NULL THEN 'pending'
        WHEN a.is_accurate THEN 'accurate'
        ELSE 'inaccurate'
    END as status
FROM pm25_predictions p
LEFT JOIN prediction_accuracy_log a ON p.id = a.prediction_id
ORDER BY p.target_date DESC;

-- View: สถิติความแม่นยำรายวัน
CREATE OR REPLACE VIEW v_daily_accuracy_stats AS
SELECT 
    DATE(p.target_date) as date,
    COUNT(*) as total_predictions,
    COUNT(p.actual_value) as predictions_with_actual,
    AVG(a.error_value) as avg_error,
    AVG(a.error_percentage) as avg_error_percentage,
    COUNT(*) FILTER (WHERE a.is_accurate = TRUE) as accurate_count,
    ROUND(
        (COUNT(*) FILTER (WHERE a.is_accurate = TRUE)::FLOAT / 
         NULLIF(COUNT(p.actual_value), 0) * 100)::NUMERIC, 
        2
    ) as accuracy_rate
FROM pm25_predictions p
LEFT JOIN prediction_accuracy_log a ON p.id = a.prediction_id
WHERE p.actual_value IS NOT NULL
GROUP BY DATE(p.target_date)
ORDER BY date DESC;

-- View: ข้อมูลล่าสุด 7 วัน
CREATE OR REPLACE VIEW v_recent_7days AS
SELECT 
    r.reading_date,
    r.pm25_value as actual_value,
    r.aqi_level,
    r.aqi_color,
    p.predicted_value,
    p.prediction_date,
    CASE 
        WHEN p.predicted_value IS NOT NULL 
        THEN ABS(p.predicted_value - r.pm25_value)
        ELSE NULL
    END as error
FROM pm25_actual_readings r
LEFT JOIN pm25_predictions p 
    ON r.reading_date = p.target_date 
    AND r.location = p.location
WHERE r.reading_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY r.reading_date DESC;

-- ============================================
-- Sample Data (Optional - for testing)
-- ============================================

-- Insert sample model version
INSERT INTO model_versions (version, model_name, is_active, is_production, description)
VALUES ('v1.0', 'LSTM PM2.5 Forecaster', TRUE, TRUE, 'Initial production model')
ON CONFLICT (version) DO NOTHING;

-- ============================================
-- Row Level Security (RLS) - Optional
-- ============================================

-- Enable RLS
ALTER TABLE pm25_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE pm25_actual_readings ENABLE ROW LEVEL SECURITY;
ALTER TABLE prediction_accuracy_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_logs ENABLE ROW LEVEL SECURITY;

-- Policy: อนุญาตให้ทุกคนอ่านได้
CREATE POLICY "Allow public read access" ON pm25_predictions FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON pm25_actual_readings FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON prediction_accuracy_log FOR SELECT USING (true);

-- Policy: เฉพาะ authenticated users เท่านั้นที่เขียนได้
CREATE POLICY "Allow authenticated insert" ON pm25_predictions FOR INSERT WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Allow authenticated update" ON pm25_predictions FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated insert" ON pm25_actual_readings FOR INSERT WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Allow authenticated update" ON pm25_actual_readings FOR UPDATE USING (auth.role() = 'authenticated');

-- ============================================
-- Useful Queries (คัดลอกไปใช้ได้เลย)
-- ============================================

-- Query 1: ดูข้อมูลพยากรณ์ล่าสุด 10 รายการ
-- SELECT * FROM v_predictions_with_actual LIMIT 10;

-- Query 2: ดูสถิติความแม่นยำ 30 วันล่าสุด
-- SELECT * FROM v_daily_accuracy_stats WHERE date >= CURRENT_DATE - INTERVAL '30 days';

-- Query 3: ดูข้อมูล 7 วันล่าสุด
-- SELECT * FROM v_recent_7days;

-- Query 4: หาค่าเฉลี่ย MAE ของ model
-- SELECT AVG(error_value) as avg_mae FROM prediction_accuracy_log;

-- Query 5: หาวันที่พยากรณ์ผิดพลาดมากที่สุด
-- SELECT * FROM v_predictions_with_actual 
-- WHERE actual_value IS NOT NULL 
-- ORDER BY error_value DESC LIMIT 10;

-- Query 6: นับจำนวนการพยากรณ์ที่แม่นยำ
-- SELECT 
--     COUNT(*) FILTER (WHERE is_accurate = TRUE) as accurate,
--     COUNT(*) FILTER (WHERE is_accurate = FALSE) as inaccurate,
--     ROUND(
--         (COUNT(*) FILTER (WHERE is_accurate = TRUE)::FLOAT / COUNT(*) * 100)::NUMERIC, 
--         2
--     ) as accuracy_percentage
-- FROM prediction_accuracy_log;

-- ============================================
-- End of Schema
-- ============================================
