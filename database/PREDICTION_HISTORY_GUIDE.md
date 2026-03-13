# คู่มือการใช้งานระบบเก็บประวัติการพยากรณ์

## 📋 ภาพรวม

หลังจากรัน `fix_predictions_history.sql` แล้ว ระบบจะเก็บ**ประวัติการพยากรณ์ทั้งหมด** ไม่ใช่แค่ล่าสุด

---

## 🔄 การเปลี่ยนแปลง

### ก่อนแก้ไข ❌
```
วันที่ 2026-02-24:
  - การพยากรณ์ครั้งที่ 1: 35.2 µg/m³ (เก็บไว้)
  - การพยากรณ์ครั้งที่ 2: 40.5 µg/m³ (overwrite ครั้งที่ 1)
  - การพยากรณ์ครั้งที่ 3: 38.0 µg/m³ (overwrite ครั้งที่ 2)
  
ผลลัพธ์: มีแค่ 38.0 µg/m³ (ข้อมูลเก่าหาย)
```

### หลังแก้ไข ✅
```
วันที่ 2026-02-24:
  - การพยากรณ์ครั้งที่ 1: 35.2 µg/m³ (version 1, is_latest=false)
  - การพยากรณ์ครั้งที่ 2: 40.5 µg/m³ (version 2, is_latest=false)
  - การพยากรณ์ครั้งที่ 3: 38.0 µg/m³ (version 3, is_latest=true)
  
ผลลัพธ์: เก็บทั้งหมด 3 รายการ
```

---

## 🛠️ วิธีติดตั้ง

### ขั้นตอนที่ 1: รัน SQL Script

1. เข้า Supabase Dashboard
2. ไปที่ SQL Editor
3. Copy ทั้งหมดจาก `fix_predictions_history.sql`
4. Paste และกด Run

### ขั้นตอนที่ 2: ตรวจสอบ

```sql
-- ตรวจสอบว่า columns ใหม่ถูกสร้างแล้ว
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'pm25_predictions';

-- ควรเห็น:
-- prediction_version (integer)
-- is_latest (boolean)
```

---

## 📊 การใช้งาน

### 1. ดูการพยากรณ์ล่าสุด

```sql
SELECT * FROM v_latest_predictions 
ORDER BY target_date DESC 
LIMIT 10;
```

**ผลลัพธ์**:
```
target_date  | predicted_value | prediction_version | is_latest
-------------|-----------------|-------------------|----------
2026-03-10   | 45.2           | 3                 | true
2026-03-09   | 38.5           | 2                 | true
2026-03-08   | 42.1           | 1                 | true
```

### 2. ดูประวัติการพยากรณ์ทั้งหมด

```sql
SELECT * FROM v_prediction_history 
WHERE target_date = '2026-03-10'
ORDER BY prediction_version;
```

**ผลลัพธ์**:
```
prediction_date | predicted_value | prediction_version | status
----------------|-----------------|-------------------|----------
2026-03-09      | 42.0           | 1                 | Historical
2026-03-09      | 43.5           | 2                 | Historical
2026-03-10      | 45.2           | 3                 | Latest
```

### 3. เปรียบเทียบการพยากรณ์หลายเวอร์ชัน

```sql
SELECT * FROM v_prediction_comparison 
WHERE target_date = '2026-03-10';
```

**ผลลัพธ์**:
```
target_date | total_predictions | min | max  | avg  | latest | actual
------------|-------------------|-----|------|------|--------|-------
2026-03-10  | 3                 | 42.0| 45.2 | 43.6 | 45.2   | 44.8
```

### 4. วิเคราะห์ความแม่นยำแต่ละเวอร์ชัน

```sql
SELECT 
    target_date,
    prediction_version,
    predicted_value,
    actual_value,
    ABS(predicted_value - actual_value) as error,
    CASE 
        WHEN ABS(predicted_value - actual_value) < 10 THEN 'Accurate'
        ELSE 'Inaccurate'
    END as accuracy
FROM pm25_predictions
WHERE actual_value IS NOT NULL
  AND target_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY target_date DESC, prediction_version;
```

---

## 🔧 การใช้งานใน Python

### อัปเดต `backend/database.py`

ไม่ต้องแก้ไขอะไร! Code เดิมยังใช้ได้ เพราะ:
- `save_prediction()` จะเพิ่มข้อมูลใหม่เสมอ (ไม่ overwrite)
- Trigger จะจัดการ `prediction_version` และ `is_latest` อัตโนมัติ

### ตัวอย่างการใช้งาน

```python
from backend.database import get_db
from datetime import date, timedelta

db = get_db()

# บันทึกการพยากรณ์ครั้งที่ 1
db.save_prediction(
    prediction_date=date.today(),
    target_date=date.today() + timedelta(days=1),
    predicted_value=35.2,
    input_values={"day1": 22.4, "day2": 39.7, "day3": 25.0},
    model_version="v1.0"
)

# บันทึกการพยากรณ์ครั้งที่ 2 (วันเดียวกัน)
db.save_prediction(
    prediction_date=date.today(),
    target_date=date.today() + timedelta(days=1),
    predicted_value=40.5,  # ค่าต่างจากครั้งที่ 1
    input_values={"day1": 25.0, "day2": 42.0, "day3": 38.0},
    model_version="v1.0"
)

# ผลลัพธ์: มี 2 รายการใน database
# - รายการที่ 1: prediction_version=1, is_latest=false
# - รายการที่ 2: prediction_version=2, is_latest=true
```

### ดึงข้อมูลการพยากรณ์ล่าสุด

```python
# ใช้ view สำหรับ query ที่เร็วขึ้น
result = db.client.table('v_latest_predictions')\
    .select('*')\
    .eq('location', 'Nakhon Phanom')\
    .order('target_date', desc=True)\
    .limit(10)\
    .execute()

predictions = result.data
```

### ดึงประวัติการพยากรณ์ทั้งหมด

```python
result = db.client.table('v_prediction_history')\
    .select('*')\
    .eq('target_date', '2026-03-10')\
    .order('prediction_version')\
    .execute()

history = result.data
```

---

## 📈 Use Cases

### 1. วิเคราะห์ว่า Model ปรับปรุงขึ้นหรือไม่

```sql
-- เปรียบเทียบ error ของการพยากรณ์เวอร์ชันแรกกับเวอร์ชันล่าสุด
SELECT 
    target_date,
    MAX(CASE WHEN prediction_version = 1 THEN ABS(predicted_value - actual_value) END) as first_error,
    MAX(CASE WHEN is_latest THEN ABS(predicted_value - actual_value) END) as latest_error
FROM pm25_predictions
WHERE actual_value IS NOT NULL
GROUP BY target_date
HAVING COUNT(*) > 1;
```

### 2. ดูว่าการพยากรณ์ซ้ำกี่ครั้งต่อวัน

```sql
SELECT 
    target_date,
    COUNT(*) as prediction_count,
    STRING_AGG(predicted_value::TEXT, ', ' ORDER BY prediction_version) as all_predictions
FROM pm25_predictions
GROUP BY target_date
HAVING COUNT(*) > 1
ORDER BY target_date DESC;
```

### 3. หา Model Version ที่แม่นยำที่สุด

```sql
SELECT 
    model_version,
    COUNT(*) as total_predictions,
    AVG(ABS(predicted_value - actual_value)) as avg_error,
    COUNT(*) FILTER (WHERE ABS(predicted_value - actual_value) < 10) as accurate_count
FROM pm25_predictions
WHERE actual_value IS NOT NULL
GROUP BY model_version
ORDER BY avg_error;
```

---

## ⚠️ ข้อควรระวัง

### 1. ข้อมูลจะเพิ่มขึ้นเรื่อยๆ

ถ้าพยากรณ์บ่อยมาก (เช่น ทุกชั่วโมง) ข้อมูลจะเยอะมาก

**วิธีแก้**: ลบข้อมูลเก่าที่ไม่ใช้แล้ว

```sql
-- ลบการพยากรณ์ที่ไม่ใช่ล่าสุดและเก่ากว่า 30 วัน
DELETE FROM pm25_predictions
WHERE is_latest = FALSE
  AND created_at < CURRENT_DATE - INTERVAL '30 days';
```

### 2. Query อาจช้าลง

ถ้ามีข้อมูลเยอะมาก

**วิธีแก้**: ใช้ Views ที่สร้างไว้ (มี index อยู่แล้ว)

```sql
-- ดี ✅ (ใช้ view)
SELECT * FROM v_latest_predictions;

-- ไม่ดี ❌ (query ตรงๆ)
SELECT * FROM pm25_predictions WHERE is_latest = TRUE;
```

---

## 🎯 สรุป

หลังจากรัน SQL script แล้ว:

✅ เก็บประวัติการพยากรณ์ทั้งหมด  
✅ มี prediction_version บอกว่าเป็นครั้งที่เท่าไหร่  
✅ มี is_latest บอกว่าเป็นล่าสุดหรือไม่  
✅ สามารถเปรียบเทียบการพยากรณ์หลายเวอร์ชันได้  
✅ Code Python ไม่ต้องแก้ไข  
✅ มี Views สำหรับ query ที่สะดวก  

**ระบบพร้อมเก็บประวัติการพยากรณ์แล้ว!** 🚀
