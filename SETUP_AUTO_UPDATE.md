# 🤖 การตั้งค่าระบบอัตโนมัติ (Auto Update)

## ภาพรวม

ระบบจะดึงข้อมูล PM2.5 จาก WAQI API และบันทึกลง Supabase อัตโนมัติทุกวัน เวลา 00:00 UTC (07:00 น. เวลาไทย)

---

## 📋 สิ่งที่ระบบทำอัตโนมัติ

1. ✅ ดึงข้อมูล PM2.5 จาก WAQI API
2. ✅ บันทึกค่าจริงลง `pm25_actual_readings` table
3. ✅ อัปเดต `actual_value` ใน `pm25_predictions` table
4. ✅ คำนวณ accuracy อัตโนมัติ (ผ่าน database trigger)
5. ✅ ทำการพยากรณ์วันพรุ่งนี้
6. ✅ ส่ง alert ถ้าค่า PM2.5 สูงเกินเกณฑ์

---

## 🔧 วิธีตั้งค่า

### ขั้นตอนที่ 1: ตั้งค่า GitHub Secrets

ไปที่ GitHub Repository → Settings → Secrets and variables → Actions → New repository secret

เพิ่ม secrets ต่อไปนี้:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here
WAQI_API_TOKEN=6e19dc4d73747ab27c397b590fdbd504f1f496fc
```

**วิธีหา Supabase Keys:**
1. เข้า https://supabase.com/dashboard
2. เลือก project ของคุณ
3. ไปที่ Settings → API
4. คัดลอก:
   - `Project URL` → ใส่ใน `SUPABASE_URL`
   - `service_role` key → ใส่ใน `SUPABASE_SERVICE_KEY`

### ขั้นตอนที่ 2: Push Code ขึ้น GitHub

```bash
git add .
git commit -m "Add daily auto-update system"
git push origin main
```

### ขั้นตอนที่ 3: Enable GitHub Actions

1. ไปที่ GitHub Repository → Actions tab
2. ถ้ามีข้อความ "Workflows aren't being run on this repository" ให้กด "I understand my workflows, go ahead and enable them"
3. คุณจะเห็น workflow "Daily PM2.5 Data Update"

### ขั้นตอนที่ 4: ทดสอบรัน Manual

1. ไปที่ Actions tab
2. เลือก "Daily PM2.5 Data Update"
3. กด "Run workflow" → "Run workflow"
4. รอสักครู่แล้วดูผลลัพธ์

---

## ⏰ กำหนดการรัน

### GitHub Actions (แนะนำ)
- รันอัตโนมัติทุกวัน เวลา 00:00 UTC (07:00 น. เวลาไทย)
- ฟรี! ไม่มีค่าใช้จ่าย
- รัน manual ได้ตลอดเวลา

### ทางเลือกอื่น

#### 1. Render Cron Jobs (ต้องจ่ายเงิน)
```yaml
# render.yaml
services:
  - type: cron
    name: daily-update
    env: python
    schedule: "0 0 * * *"
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python scripts/daily_update.py"
```

#### 2. รันบนเครื่องตัวเอง (Windows Task Scheduler)
```powershell
# สร้าง task ที่รันทุกวัน
schtasks /create /tn "PM25DailyUpdate" /tr "python D:\pm25_web_project\scripts\daily_update.py" /sc daily /st 07:00
```

#### 3. รันบน Linux Server (Crontab)
```bash
# เพิ่มใน crontab
0 7 * * * cd /path/to/project && python scripts/daily_update.py >> /var/log/pm25_update.log 2>&1
```

---

## 🧪 ทดสอบ Script ด้วยตัวเอง

```bash
# ตรวจสอบว่า environment variables ถูกต้อง
python scripts/daily_update.py
```

คุณจะเห็น output แบบนี้:

```
======================================================================
🤖 DAILY UPDATE SCRIPT - PM2.5 Forecasting System
📅 Date: 2026-02-23 12:00:00
======================================================================

Step 1: Connecting to database...
✅ Database connected

Step 2: Fetching data from WAQI API...
✅ WAQI data fetched

Step 3: Saving actual reading to database...
📝 Saving actual reading:
   Date: 2026-02-23
   PM2.5: 33.5 µg/m³
   AQI Level: ปานกลาง
✅ Actual reading saved successfully!

Step 4: Checking alert conditions...
✅ PM2.5 level is normal (33.5 µg/m³)

Step 5: Getting recent data for prediction...
📊 Recent 3 days PM2.5 values:
   Day 1 (2026-02-21): 22.4 µg/m³
   Day 2 (2026-02-22): 39.7 µg/m³
   Day 3 (2026-02-23): 33.5 µg/m³

Step 6: Making prediction for tomorrow...
✅ Prediction successful!
   Predicted PM2.5 for tomorrow: 35.2 µg/m³

======================================================================
✅ Daily update completed successfully!
======================================================================
```

---

## 📊 ตรวจสอบว่าระบบทำงาน

### 1. ดูใน Supabase Dashboard
- เข้า https://supabase.com/dashboard
- เลือก project → Table Editor
- ดูตาราง `pm25_actual_readings` ควรมีข้อมูลใหม่ทุกวัน
- ดูตาราง `pm25_predictions` ควรมีการพยากรณ์ใหม่ทุกวัน

### 2. ดูใน GitHub Actions
- ไปที่ Actions tab
- ดู workflow runs ล่าสุด
- ถ้าเป็นสีเขียว ✅ = สำเร็จ
- ถ้าเป็นสีแดง ❌ = ล้มเหลว (กดดู logs)

### 3. ดูใน Frontend
- เข้า https://project-pm25-1.onrender.com
- ควรเห็นข้อมูลอัปเดตทุกวัน

---

## 🔔 การแจ้งเตือน (Alert)

ระบบจะบันทึก alert log เมื่อ:
- PM2.5 > 37.5 µg/m³ (ระดับ warning)
- PM2.5 > 75.0 µg/m³ (ระดับ critical)

### เพิ่ม LINE Notify (ในอนาคต)

1. สมัคร LINE Notify Token: https://notify-bot.line.me/
2. เพิ่ม secret `LINE_NOTIFY_TOKEN` ใน GitHub
3. แก้ไข `scripts/daily_update.py` เพิ่มฟังก์ชัน `send_line_notify()`

---

## 🐛 Troubleshooting

### ปัญหา: GitHub Actions ไม่รัน

**วิธีแก้:**
1. ตรวจสอบว่า Actions เปิดใช้งานแล้ว (Settings → Actions → General)
2. ตรวจสอบว่า secrets ตั้งค่าถูกต้อง
3. ลองรัน manual ดู

### ปัญหา: Database connection failed

**วิธีแก้:**
1. ตรวจสอบ `SUPABASE_URL` และ `SUPABASE_SERVICE_KEY`
2. ตรวจสอบว่า Supabase project ยังทำงานอยู่
3. ตรวจสอบว่า tables ถูกสร้างแล้ว

### ปัญหา: WAQI API error

**วิธีแก้:**
1. ตรวจสอบ `WAQI_API_TOKEN`
2. ทดสอบ API: https://api.waqi.info/feed/@9696/?token=YOUR_TOKEN
3. ตรวจสอบว่า station ID ถูกต้อง

### ปัญหา: Not enough data for prediction

**วิธีแก้:**
- ต้องมีข้อมูลอย่างน้อย 3 วันก่อนถึงจะพยากรณ์ได้
- รัน script 3 วันติดต่อกัน หรือเพิ่มข้อมูลเก่าเข้าไปใน database

---

## 📝 Logs

### ดู GitHub Actions Logs
1. ไปที่ Actions tab
2. เลือก workflow run
3. กดดู job "update-data"
4. ดู output ของแต่ละ step

### ดู Render Logs (ถ้าใช้ Render Cron)
1. ไปที่ Render Dashboard
2. เลือก cron job service
3. ดู Logs tab

---

## 🎯 Next Steps

หลังจากตั้งค่าเสร็จแล้ว:

1. ✅ รอ 3-7 วันให้มีข้อมูลเพียงพอ
2. ✅ ตรวจสอบความแม่นยำของ model
3. ✅ เพิ่ม LINE Notify สำหรับ alert
4. ✅ ปรับปรุง frontend ให้แสดงข้อมูลจาก database
5. ✅ เพิ่ม analytics dashboard

---

## 📞 Support

ถ้ามีปัญหา:
1. ดู logs ใน GitHub Actions
2. ตรวจสอบ Supabase Dashboard
3. ทดสอบรัน script ด้วยตัวเอง: `python scripts/daily_update.py`

---

**หมายเหตุ**: ระบบจะเริ่มทำงานอัตโนมัติหลังจาก push code และตั้งค่า secrets เรียบร้อยแล้ว
