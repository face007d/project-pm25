# Database Setup Guide

## 🚀 Quick Start

### 1. สร้าง Supabase Project
1. ไปที่ https://supabase.com
2. สร้าง project ใหม่
3. รอให้ database พร้อมใช้งาน (ประมาณ 2 นาที)

### 2. รัน SQL Schema
1. เปิด Supabase Dashboard
2. ไปที่ **SQL Editor**
3. คัดลอกโค้ดจากไฟล์ `schema.sql`
4. Paste และกด **Run**
5. รอให้เสร็จ (ประมาณ 10-20 วินาที)

### 3. ดึง API Keys
1. ไปที่ **Settings** → **API**
2. คัดลอก:
   - `Project URL`
   - `anon public` key
   - `service_role` key (สำหรับ backend)

### 4. ตั้งค่า Environment Variables
สร้างไฟล์ `.env` ในโฟลเดอร์ root:

```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 📊 Database Tables

### 1. `pm25_predictions`
เก็บข้อมูลการพยากรณ์ PM2.5

**Columns:**
- `id` - UUID primary key
- `prediction_date` - วันที่ทำการพยากรณ์
- `target_date` - วันที่พยากรณ์ไว้
- `predicted_value` - ค่าที่พยากรณ์
- `actual_value` - ค่าจริง (อัปเดตภายหลัง)
- `input_values` - ข้อมูล 3 วันที่ใช้พยากรณ์ (JSONB)
- `model_version` - เวอร์ชันของ model

### 2. `pm25_actual_readings`
เก็บค่า PM2.5 จริงที่วัดได้

**Columns:**
- `id` - UUID primary key
- `reading_date` - วันที่วัด
- `pm25_value` - ค่า PM2.5
- `aqi_level` - ระดับคุณภาพอากาศ
- `temperature`, `humidity`, `wind_speed` - ข้อมูลสภาพอากาศ

### 3. `prediction_accuracy_log`
เก็บข้อมูลความแม่นยำ

**Columns:**
- `prediction_id` - FK to pm25_predictions
- `error_value` - ค่าความผิดพลาด
- `error_percentage` - เปอร์เซ็นต์ความผิดพลาด
- `is_accurate` - แม่นยำหรือไม่

### 4. `model_versions`
เก็บข้อมูล model versions

### 5. `alert_logs`
เก็บประวัติการแจ้งเตือน

---

## 🔍 Useful Queries

### ดูข้อมูลพยากรณ์ล่าสุด
```sql
SELECT * FROM v_predictions_with_actual LIMIT 10;
```

### ดูสถิติความแม่นยำ
```sql
SELECT * FROM v_daily_accuracy_stats 
WHERE date >= CURRENT_DATE - INTERVAL '30 days';
```

### หาค่าเฉลี่ย MAE
```sql
SELECT AVG(error_value) as avg_mae 
FROM prediction_accuracy_log;
```

### ดูข้อมูล 7 วันล่าสุด
```sql
SELECT * FROM v_recent_7days;
```

---

## 🔐 Security (RLS)

Row Level Security (RLS) ถูกเปิดใช้งานแล้ว:
- **Public** สามารถ **อ่าน** ข้อมูลได้ทั้งหมด
- **Authenticated users** เท่านั้นที่ **เขียน** ได้

---

## 🛠️ Maintenance

### Backup Database
```bash
# ใน Supabase Dashboard → Database → Backups
# หรือใช้ pg_dump
```

### Monitor Performance
```sql
-- ดู table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 📝 Notes

- Indexes ถูกสร้างไว้แล้วสำหรับ queries ที่ใช้บ่อย
- Triggers จะคำนวณความแม่นยำอัตโนมัติเมื่อมีค่าจริง
- Views พร้อมใช้งานสำหรับ analytics
- RLS ป้องกันการเขียนข้อมูลโดยไม่ได้รับอนุญาต
