-- ============================================
-- แก้ไขตาราง pm25_predictions ให้เก็บประวัติการพยากรณ์ทั้งหมด
-- ============================================

-- ขั้นตอนที่ 1: ลบ UNIQUE constraint เดิม
ALTER TABLE pm25_predictions 
DROP CONSTRAINT IF EXISTS unique_prediction;

-- ขั้นตอนที่ 2: เพิ่ม column สำหรับระบุเวอร์ชันการพยากรณ์
ALTER TABLE pm25_predictions 
ADD COLUMN IF NOT EXISTS prediction_version INTEGER DEFAULT 1;

-- ขั้นตอนที่ 3: เพิ่ม column สำหรับระบุว่าเป็นการพยากรณ์ล่าสุดหรือไม่
ALTER TABLE pm25_predictions 
ADD COLUMN IF NOT EXISTS is_latest BOOLEAN DEFAULT TRUE;

-- ขั้นตอนที่ 4: สร้าง index ใหม่สำหรับ query ที่เร็วขึ้น
CREATE INDEX IF NOT EXISTS idx_predictions_latest 
ON pm25_predictions(target_date, location, is_latest) 
WHERE is_latest = TRUE;

CREATE INDEX IF NOT EXISTS idx_predictions_version 
ON pm25_predictions(target_date, location, prediction_version);

-- ขั้นตอนที่ 5: สร้าง function สำหรับอัปเดต is_latest อัตโนมัติ
CREATE OR REPLACE FUNCTION update_latest_prediction()
RETURNS TRIGGER AS $$
BEGIN
    -- ทำให้การพยากรณ์เก่าทั้งหมดของวันเดียวกันเป็น is_latest = FALSE
    UPDATE pm25_predictions
    SET is_latest = FALSE
    WHERE target_date = NEW.target_date
      AND location = NEW.location
      AND id != NEW.id;
    
    -- ทำให้การพยากรณ์ใหม่เป็น is_latest = TRUE
    NEW.is_latest := TRUE;
    
    -- คำนวณ prediction_version อัตโนมัติ
    NEW.prediction_version := (
        SELECT COALESCE(MAX(prediction_version), 0) + 1
        FROM pm25_predictions
        WHERE target_date = NEW.target_date
          AND location = NEW.location
          AND id != NEW.id
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ขั้นตอนที่ 6: สร้าง trigger
DROP TRIGGER IF EXISTS trigger_update_latest_prediction ON pm25_predictions;

CREATE TRIGGER trigger_update_latest_prediction
    BEFORE INSERT ON pm25_predictions
    FOR EACH ROW
    EXECUTE FUNCTION update_latest_prediction();

-- ============================================
-- Views สำหรับ Query ที่สะดวก
-- ============================================

-- View: การพยากรณ์ล่าสุดเท่านั้น
CREATE OR REPLACE VIEW v_latest_predictions AS
SELECT 
    id,
    prediction_date,
    target_date,
    predicted_value,
    actual_value,
    input_values,
    model_version,
    prediction_version,
    confidence_score,
    location,
    created_at
FROM pm25_predictions
WHERE is_latest = TRUE
ORDER BY target_date DESC;

-- View: ประวัติการพยากรณ์ทั้งหมด
CREATE OR REPLACE VIEW v_prediction_history AS
SELECT 
    id,
    prediction_date,
    target_date,
    predicted_value,
    actual_value,
    prediction_version,
    model_version,
    location,
    created_at,
    is_latest,
    CASE 
        WHEN is_latest THEN 'Latest'
        ELSE 'Historical'
    END as status
FROM pm25_predictions
ORDER BY target_date DESC, prediction_version DESC;

-- View: เปรียบเทียบการพยากรณ์หลายเวอร์ชัน
CREATE OR REPLACE VIEW v_prediction_comparison AS
SELECT 
    target_date,
    location,
    COUNT(*) as total_predictions,
    MIN(predicted_value) as min_prediction,
    MAX(predicted_value) as max_prediction,
    AVG(predicted_value) as avg_prediction,
    STDDEV(predicted_value) as std_prediction,
    MAX(CASE WHEN is_latest THEN predicted_value END) as latest_prediction,
    MAX(actual_value) as actual_value
FROM pm25_predictions
GROUP BY target_date, location
ORDER BY target_date DESC;

-- ============================================
-- Example Queries
-- ============================================

-- Query 1: ดูการพยากรณ์ล่าสุด
-- SELECT * FROM v_latest_predictions LIMIT 10;

-- Query 2: ดูประวัติการพยากรณ์ทั้งหมดของวันที่ 2026-02-24
-- SELECT * FROM v_prediction_history 
-- WHERE target_date = '2026-02-24' 
-- ORDER BY prediction_version;

-- Query 3: เปรียบเทียบการพยากรณ์หลายเวอร์ชัน
-- SELECT * FROM v_prediction_comparison 
-- WHERE target_date >= CURRENT_DATE - INTERVAL '7 days';

-- Query 4: ดูว่าการพยากรณ์แต่ละเวอร์ชันแม่นยำแค่ไหน
-- SELECT 
--     target_date,
--     prediction_version,
--     predicted_value,
--     actual_value,
--     ABS(predicted_value - actual_value) as error
-- FROM pm25_predictions
-- WHERE actual_value IS NOT NULL
-- ORDER BY target_date DESC, prediction_version;

-- ============================================
-- สรุป
-- ============================================

-- ตอนนี้ระบบจะ:
-- 1. เก็บการพยากรณ์ทุกครั้งที่ทำ (ไม่ overwrite)
-- 2. มี prediction_version บอกว่าเป็นการพยากรณ์ครั้งที่เท่าไหร่
-- 3. มี is_latest บอกว่าเป็นการพยากรณ์ล่าสุดหรือไม่
-- 4. สามารถเปรียบเทียบการพยากรณ์หลายเวอร์ชันได้
-- 5. Query ได้ง่ายผ่าน Views

COMMENT ON TABLE pm25_predictions IS 'เก็บประวัติการพยากรณ์ PM2.5 ทั้งหมด รองรับหลายเวอร์ชัน';
COMMENT ON COLUMN pm25_predictions.prediction_version IS 'เวอร์ชันของการพยากรณ์ (1, 2, 3, ...)';
COMMENT ON COLUMN pm25_predictions.is_latest IS 'เป็นการพยากรณ์ล่าสุดหรือไม่';
