# 🔍 ตรวจสอบปัญหาจุดไฟไหม้ไม่แสดงบนแผนที่

## ปัญหาที่พบ
- จุดที่ user แชร์ location มาไม่ขึ้นไฟบนแผนที่

## สาเหตุที่เป็นไปได้

### 1. ยังไม่ได้เพิ่ม SUPABASE_SERVICE_KEY ใน Render ⚠️
**ตรวจสอบ:**
- ไปที่ https://dashboard.render.com/
- เลือก service **project-pm25**
- ไปที่แท็บ **Environment**
- ตรวจสอบว่ามี `SUPABASE_SERVICE_KEY` หรือไม่

**ถ้ายังไม่มี ให้เพิ่ม:**
```
Key: SUPABASE_SERVICE_KEY
Value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFuanl6cHNrb2Ryd3hqc3JiZGRzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTc0MzY1MywiZXhwIjoyMDg3MzE5NjUzfQ.Vuv7O4dlJUmeLx28l44kiWK3xTnCT7IassjHGPyij4k
```

### 2. รูปภาพเก่าใช้ LINE URL ที่หมดอายุแล้ว
**วิธีแก้:**
- ส่งรูปใหม่ผ่าน LINE Bot อีกครั้ง
- รูปใหม่จะถูกอัพโหลดไปยัง Supabase Storage (ถ้าเพิ่ม SERVICE_KEY แล้ว)
- รูปจะไม่หมดอายุอีกต่อไป

### 3. ข้อมูลในฐานข้อมูลไม่มี latitude/longitude
**ตรวจสอบ:**
```sql
SELECT id, latitude, longitude, image_url, created_at 
FROM fire_reports 
ORDER BY created_at DESC 
LIMIT 5;
```

## ขั้นตอนการแก้ไข

### ขั้นตอนที่ 1: เพิ่ม Environment Variable ใน Render
1. ไปที่ Render Dashboard
2. เพิ่ม `SUPABASE_SERVICE_KEY` (ดูค่าด้านบน)
3. Save Changes
4. รอ redeploy (2-3 นาที)

### ขั้นตอนที่ 2: ทดสอบส่งรูปใหม่
1. เปิด LINE Bot
2. ส่งรูปภาพจุดไฟไหม้
3. ส่ง Location
4. ตรวจสอบว่าได้รับข้อความ "✅ บันทึกสำเร็จ!"

### ขั้นตอนที่ 3: ตรวจสอบบนแผนที่
1. เปิด https://project-pm25.onrender.com
2. ดูว่ามีจุดไฟไหม้ปรากฏหรือไม่
3. คลิกที่จุดเพื่อดูรายละเอียด

## วิธีตรวจสอบว่าแก้ไขสำเร็จ

### ✅ สัญญาณที่ดี:
- เห็นรูปภาพเป็น marker บนแผนที่ (ไม่ใช่แค่จุดแดง)
- คลิกที่รูปแล้วเห็น popup พร้อมรายละเอียด
- รูปภาพโหลดได้ (ไม่ error)
- URL ของรูปเป็น `https://anjyzpskodrwxjsrbdds.supabase.co/storage/...`

### ❌ สัญญาณที่ยังมีปัญหา:
- ไม่เห็นจุดไฟไหม้เลย
- เห็นแค่จุดแดงกลมๆ (ไม่มีรูป)
- รูปภาพโหลดไม่ได้ (แสดง 🔥 แทน)
- URL ของรูปเป็น `https://api-data.line.me/...` (LINE URL)

## Debug Commands

### ตรวจสอบ API Response:
```bash
curl https://project-pm25.onrender.com/api/fire-reports
```

### ตรวจสอบ Render Logs:
1. ไปที่ Render Dashboard
2. เลือก service project-pm25
3. ดู Logs
4. หา log ที่มี "📦 Available buckets"
5. ถ้าเห็น `[]` แสดงว่ายังไม่มี SERVICE_KEY
6. ถ้าเห็น `['fire_image']` แสดงว่าใช้งานได้แล้ว

## สรุป
ปัญหาหลักคือ **ยังไม่ได้เพิ่ม SUPABASE_SERVICE_KEY ใน Render**

เมื่อเพิ่มแล้ว:
- รูปจะถูกอัพโหลดไปยัง Supabase Storage
- รูปจะไม่หมดอายุ
- แผนที่จะแสดงรูปภาพจริงแทนจุดแดง
