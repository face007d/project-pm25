# Phase 2 - Step 3: LINE Webhook Setup Guide
# คู่มือการตั้งค่า LINE Official Account

## ✅ สิ่งที่ทำเสร็จแล้ว

1. ✅ Database Schema (4 ตาราง: fire_reports, line_users, line_user_sessions, notification_logs)
2. ✅ Backend Code (LINE Webhook + Database Methods)
3. ✅ Dependencies (line-bot-sdk==3.9.0)

---

## 📋 ขั้นตอนการตั้งค่า LINE Official Account

### Step 1: สร้าง LINE Messaging API Channel

1. ไปที่ [LINE Developers Console](https://developers.line.biz/console/)
2. เลือก Provider ของคุณ (หรือสร้างใหม่)
3. คลิก **Create a new channel** → เลือก **Messaging API**
4. กรอกข้อมูล:
   - Channel name: `พญานาคเฝ้าฟ้า` (หรือชื่อที่ต้องการ)
   - Channel description: `ระบบแจ้งเหตุไฟไหม้และตรวจสอบค่าฝุ่น PM2.5 นครพนม`
   - Category: `Public Sector` หรือ `Environment`
   - Subcategory: เลือกตามความเหมาะสม
5. คลิก **Create**

---

### Step 2: ตั้งค่า Webhook URL

1. ในหน้า Channel Settings → ไปที่แท็บ **Messaging API**
2. หาส่วน **Webhook settings**
3. คลิก **Edit** แล้วใส่ URL:
   ```
   https://project-pm25-1.onrender.com/webhook
   ```
4. คลิก **Update**
5. เปิด **Use webhook**: เปลี่ยนเป็น **Enabled**
6. ทดสอบ webhook: คลิก **Verify** (ควรได้ Success)

---

### Step 3: ดึง Channel Access Token และ Channel Secret

#### 3.1 Channel Access Token
1. ในหน้า **Messaging API** → หาส่วน **Channel access token**
2. คลิก **Issue** (ถ้ายังไม่มี)
3. คัดลอก Token ที่ได้ (ยาวมาก ขึ้นต้นด้วย `eyJ...`)

#### 3.2 Channel Secret
1. ในหน้า **Basic settings** → หาส่วน **Channel secret**
2. คลิก **Show** แล้วคัดลอก

---

### Step 4: เพิ่ม Credentials ใน Render.com

1. ไปที่ [Render Dashboard](https://dashboard.render.com/)
2. เลือก Service: `project-pm25-1`
3. ไปที่ **Environment** → คลิก **Add Environment Variable**
4. เพิ่ม 2 ตัวแปรนี้:

```bash
LINE_CHANNEL_ACCESS_TOKEN=<วาง Channel Access Token ที่คัดลอกมา>
LINE_CHANNEL_SECRET=<วาง Channel Secret ที่คัดลอกมา>
```

5. คลิก **Save Changes**
6. Render จะ redeploy อัตโนมัติ (รอประมาณ 2-3 นาที)

---

### Step 5: ตั้งค่า LINE OA เพิ่มเติม

#### 5.1 ปิด Auto-reply messages
1. ในหน้า **Messaging API** → หาส่วน **LINE Official Account features**
2. คลิก **Edit** ที่ **Auto-reply messages**
3. เปลี่ยนเป็น **Disabled**

#### 5.2 ปิด Greeting messages (ถ้าไม่ต้องการ)
1. คลิก **Edit** ที่ **Greeting messages**
2. เปลี่ยนเป็น **Disabled** (หรือตั้งค่าข้อความต้อนรับเอง)

#### 5.3 เปิด Allow bot to join group chats (ถ้าต้องการ)
1. ในหน้า **Messaging API** → หาส่วน **Bot settings**
2. เปิด **Allow bot to join group chats** (ถ้าต้องการให้บอทเข้ากลุ่มได้)

---

### Step 6: ทดสอบระบบ

#### 6.1 เพิ่มเพื่อน LINE OA
1. ในหน้า **Messaging API** → หาส่วน **Bot information**
2. สแกน QR Code หรือคลิก **Add friend** link
3. หรือค้นหา LINE ID: `@726lnjeu`

#### 6.2 ทดสอบคำสั่งพื้นฐาน
ส่งข้อความไปที่บอท:
- `สวัสดี` → ควรได้ข้อความต้อนรับ
- `ฝุ่น` → ควรได้ข้อมูลค่า PM2.5 ล่าสุด
- `ช่วยเหลือ` → ควรได้รายการคำสั่ง

#### 6.3 ทดสอบการแจ้งเหตุไฟไหม้
1. ส่งรูปภาพใดก็ได้ → ควรได้ข้อความ "✅ ได้รับรูปภาพแล้ว กรุณาส่งพิกัด"
2. กดปุ่ม `+` → เลือก **Location** → แชร์ตำแหน่ง
3. ควรได้ข้อความ "✅ ขอบคุณสำหรับข้อมูล! ระบบได้รับแจ้งเหตุ..."

#### 6.4 ตรวจสอบข้อมูลใน Supabase
1. เปิด Supabase Dashboard → Table Editor
2. เปิดตาราง `fire_reports` → ควรเห็นข้อมูลที่เพิ่งแจ้ง
3. เปิดตาราง `line_users` → ควรเห็นข้อมูลผู้ใช้
4. เปิดตาราง `line_user_sessions` → ควรเห็น session (is_complete = true)

---

## 🔍 การตรวจสอบ Logs

### ดู Logs ใน Render
1. ไปที่ Render Dashboard → Service: `project-pm25-1`
2. คลิกแท็บ **Logs**
3. ดูข้อความ:
   - `✅ LINE Bot initialized successfully` → LINE Bot พร้อมใช้งาน
   - `✅ Saved fire report from U...` → บันทึกรายงานสำเร็จ

### ดู Webhook Logs ใน LINE Developers
1. ไปที่ LINE Developers Console → Channel
2. แท็บ **Messaging API** → ส่วน **Webhook settings**
3. คลิก **Webhook URL** → ดู Request/Response logs

---

## 🐛 Troubleshooting

### ปัญหา: Webhook Verify ไม่ผ่าน
**สาเหตุ:** Render ยังไม่ deploy เสร็จ หรือ credentials ผิด
**แก้ไข:**
1. ตรวจสอบว่า Render deploy เสร็จแล้ว (ดูที่ Logs)
2. ตรวจสอบ Environment Variables ว่าใส่ถูกต้อง
3. ลองเปิด URL: `https://project-pm25-1.onrender.com/api` → ดู `line_bot` status

### ปัญหา: บอทไม่ตอบกลับ
**สาเหตุ:** Auto-reply ยังเปิดอยู่ หรือ webhook ไม่ทำงาน
**แก้ไข:**
1. ปิด Auto-reply messages ใน LINE OA Manager
2. ตรวจสอบ Logs ใน Render ว่ามี error หรือไม่
3. ตรวจสอบ Webhook URL ว่าถูกต้อง

### ปัญหา: ข้อมูลไม่เข้า Supabase
**สาเหตุ:** Database credentials ผิด หรือ RLS policies
**แก้ไข:**
1. ตรวจสอบ `SUPABASE_URL` และ `SUPABASE_SERVICE_KEY` ใน Render
2. ตรวจสอบ RLS policies ใน Supabase (ควรใช้ service_role key)

---

## 📊 API Endpoints ใหม่ (Phase 2)

### 1. LINE Webhook
```
POST /webhook
```
- รับข้อความจาก LINE OA
- ต้องมี `X-Line-Signature` header

### 2. ดึงรายงานไฟไหม้
```
GET /api/fire-reports?limit=50&status=pending
```
Response:
```json
{
  "data": [
    {
      "id": "uuid",
      "line_user_id": "U...",
      "user_display_name": "ชื่อผู้ใช้",
      "latitude": 17.4065,
      "longitude": 104.7686,
      "image_url": "https://...",
      "status": "pending",
      "created_at": "2026-03-13T..."
    }
  ],
  "count": 1
}
```

### 3. ดึงรายงานวันนี้
```
GET /api/fire-reports/today
```

---

## 🎯 ขั้นตอนถัดไป

✅ Step 1: สร้าง LINE OA  
✅ Step 2: สร้าง Database Schema  
✅ Step 3: สร้าง LINE Webhook (Backend) ← **เสร็จแล้ว!**  
⏭️ Step 4: เพิ่ม OpenStreetMap (Frontend)  
⏭️ Step 5: สร้างระบบ Push Notification  
⏭️ Step 6: ทดสอบและ Deploy  

---

## 📝 Notes

- LINE Message API มี [rate limit](https://developers.line.biz/en/reference/messaging-api/#rate-limits)
- รูปภาพที่ส่งมาจะหมดอายุใน 30 วัน (ควรอัปโหลดไป cloud storage)
- Session จะหมดอายุใน 30 นาที (ตั้งค่าใน database schema)
- ใช้ `SUPABASE_SERVICE_KEY` เพื่อข้าม RLS policies

---

**เอกสารนี้สร้างเมื่อ:** 2026-03-13  
**สถานะ:** Step 3 Complete ✅
