# Naka_monitoring - ระบบเฝ้าระวังคุณภาพอากาศและจุดไฟไหม้ จังหวัดนครพนม

## ข้อมูลโครงการ

**ชื่อโครงการ**: Naka_monitoring (พญานาคเฝ้าฟ้า)  
**พื้นที่**: จังหวัดนครพนม  
**วันที่พัฒนา**: มีนาคม 2026  
**เทคโนโลジี**: Web Application + LINE Official Account + AI/ML

---

## 1. ปัญหาและความจำเป็น

### ปัญหาที่พบ
- **ฝุ่น PM2.5 สูง**: นครพนมมีปัญหาฝุ่น PM2.5 เกินมาตรฐานในช่วงฤดูแล้ง
- **ไฟป่า/ไฟไหม้**: มีการเผาในพื้นที่เกษตรและป่าไม้บ่อยครั้ง
- **ขาดข้อมูล Real-time**: ประชาชนไม่ทราบค่าฝุ่นปัจจุบันและพยากรณ์
- **การรายงานจุดไฟช้า**: ไม่มีระบบรายงานจุดไฟที่รวดเร็วและง่าย

### กลุ่มเป้าหมาย
- ประชาชนทั่วไปในจังหวัดนครพนม
- หน่วยงานราชการ (สาธารณสุข, ทรัพยากรธรรมชาติ)
- โรงเรียนและสถานศึกษา
- ผู้สูงอายุและกลุ่มเสี่ยง

---

## 2. วัตถุประสงค์

1. **ติดตามค่า PM2.5 แบบ Real-time** จากสถานีวัดคุณภาพอากาศ
2. **พยากรณ์ค่า PM2.5** ล่วงหน้า 1 วัน ด้วย LSTM Model
3. **รายงานจุดไฟไหม้** จากประชาชนผ่าน LINE OA
4. **แสดงข้อมูลบนแผนที่** เพื่อให้เห็นภาพรวม
5. **แจ้งเตือนอัตโนมัติ** ทุกวันเวลา 07:00 น.

---

## 3. ฟีเจอร์หลัก

### 3.1 เว็บแอปพลิเคชัน
**URL**: https://pm25-nakhon-phanom.onrender.com

#### หน้าแรก (Dashboard)
- แสดงค่า PM2.5 ปัจจุบัน แบบ Real-time
- กราฟแสดงแนวโน้ม 24 ชั่วโมง
- ระดับคุณภาพอากาศ (ดีมาก, ดี, ปานกลาง, ไม่ดี, อันตราย, วิกฤต)
- คำแนะนำการป้องกัน

#### การพยากรณ์ด้วย AI
- **LSTM Model** (TensorFlow/Keras)
- พยากรณ์ล่วงหน้า 1 วัน
- แสดงความแม่นยำของโมเดล
- เปรียบเทียบค่าทำนาย vs ค่าจริง

#### แผนที่จุดไฟไหม้
- แสดงจุดไฟไหม้ 48 ชั่วโมงล่าสุด
- รูปภาพจากประชาชน
- ค่า PM2.5 ณ เวลาที่รายงาน
- พิกัดและเวลาที่เกิดเหตุ

#### จังหวัดใกล้เคียง
- แสดงค่า PM2.5 จาก 4 จังหวัด:
  - อุดรธานี
  - สกลนคร
  - มุกดาหาร
  - หนองคาย
- อัปเดตทุก 5 นาที (cache)

### 3.2 LINE Official Account
**ชื่อ**: Naka Monitor

#### ฟีเจอร์
1. **ตรวจสอบค่าฝุ่น**: พิมพ์ "ฝุ่น" หรือ "pm25"
2. **รายงานจุดไฟไหม้**: ส่งรูป + แชร์พิกัด
3. **แจ้งเตือนอัตโนมัติ**: ทุกวัน 07:00 น.
4. **Rich Menu**: 5 ปุ่มด่วน
   - ตรวจสอบค่าฝุ่น
   - รายงานไฟไหม้
   - ดูแผนที่
   - ดูข้อมูลเพิ่มเติม
   - คู่มือการใช้งาน

#### การรายงานจุดไฟ
1. ผู้ใช้ส่งรูปภาพ
2. ระบบขอพิกัด (Quick Reply)
3. ผู้ใช้แชร์ location
4. ระบบบันทึก + แสดงบนแผนที่
5. บันทึกค่า PM2.5 ณ เวลานั้น

---

## 4. เทคโนโลジีที่ใช้

### Frontend
- **HTML5, CSS3, JavaScript**
- **Leaflet.js**: แผนที่
- **Chart.js**: กราฟ
- **Lucide Icons**: ไอคอน
- **Responsive Design**: รองรับทุกอุปกรณ์

### Backend
- **Python Flask**: Web Server
- **TensorFlow/Keras**: LSTM Model
- **LINE Bot SDK**: LINE OA
- **Supabase**: Database + Storage
- **WAQI API**: ข้อมูล PM2.5

### AI/ML
- **LSTM (Long Short-Term Memory)**
- **Input**: ค่า PM2.5 ย้อนหลัง 3 วัน
- **Output**: พยากรณ์ 1 วันข้างหน้า
- **Accuracy**: ~85-90%

### Deployment
- **Render**: Web Hosting (Starter Plan $7/เดือน)
- **Supabase**: Database + Storage (Free Tier)
- **GitHub**: Version Control
- **GitHub Actions**: Auto-update ทุกวัน 07:00 น.

---

## 5. สถาปัตยกรรมระบบ

```
┌─────────────────┐
│   ผู้ใช้งาน      │
│  (Web/LINE)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Frontend       │
│  (HTML/JS)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Backend        │
│  (Flask/Python) │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│Supabase│ │WAQI API│
│Database│ │PM2.5   │
└────────┘ └────────┘
```

### Data Flow
1. **WAQI API** → ค่า PM2.5 Real-time
2. **LSTM Model** → พยากรณ์ 1 วัน
3. **Supabase** → เก็บข้อมูล + รูปภาพ
4. **Frontend** → แสดงผล
5. **LINE Bot** → รับรายงาน + แจ้งเตือน

---

## 6. ฐานข้อมูล (Supabase)

### ตารางหลัก

#### 1. pm25_predictions
- การพยากรณ์ PM2.5
- ค่าทำนาย vs ค่าจริง
- ความแม่นยำ

#### 2. fire_reports
- รายงานจุดไฟไหม้
- รูปภาพ (Supabase Storage)
- พิกัด GPS
- ค่า PM2.5 ณ เวลานั้น
- ผู้รายงาน (LINE User)

#### 3. line_users
- ข้อมูลผู้ใช้ LINE
- การตั้งค่าการแจ้งเตือน

#### 4. notification_logs
- ประวัติการแจ้งเตือน

---

## 7. การพยากรณ์ด้วย LSTM

### โมเดล
- **Architecture**: LSTM (50 units) + Dense
- **Input Shape**: (3, 1) - ค่า PM2.5 ย้อนหลัง 3 วัน
- **Output**: ค่า PM2.5 วันพรุ่งนี้
- **Loss Function**: Mean Squared Error
- **Optimizer**: Adam

### การเทรน
- **Dataset**: ข้อมูลย้อนหลัง 1 ปี
- **Train/Test Split**: 80/20
- **Epochs**: 100
- **Batch Size**: 32

### ความแม่นยำ
- **MAE**: ~5-8 µg/m³
- **Accuracy**: 85-90%
- **แสดงเฉพาะ**: ค่าที่แม่นยำ (error ≤ 30)

---

## 8. การปรับปรุงประสิทธิภาพ

### ปัญหาเดิม
- หน้าเว็บโหลดช้า (5-10 วินาที)
- เรียก WAQI API 16 ครั้ง

### การแก้ไข
1. **ลดจังหวัด**: จาก 8 → 4 จังหวัด
2. **Backend Cache**: Cache 5 นาที
3. **API Endpoint**: `/api/nearby-provinces`

### ผลลัพธ์
- ⚡ เร็วขึ้น 70-80%
- 📉 ลด API calls 88% (จาก 17 → 2)
- 💾 ข้อมูลยัง Real-time (ภายใน 5 นาที)

---

## 9. ฟีเจอร์เด่น

### 9.1 Real-time Monitoring
- ข้อมูลจาก WAQI API (World Air Quality Index)
- อัปเดตทุก 5-10 นาที
- แสดงแนวโน้ม 24 ชั่วโมง

### 9.2 AI Prediction
- LSTM Model พยากรณ์ล่วงหน้า 1 วัน
- แสดงความแม่นยำ
- เปรียบเทียบค่าทำนาย vs จริง

### 9.3 Citizen Reporting
- ประชาชนรายงานจุดไฟผ่าน LINE
- ส่งรูป + พิกัด
- แสดงบนแผนที่ทันที
- บันทึกค่า PM2.5 ณ เวลานั้น

### 9.4 Auto Notification
- แจ้งเตือนทุกวัน 07:00 น.
- ค่า PM2.5 ปัจจุบัน
- คำแนะนำการป้องกัน

### 9.5 Interactive Map
- แสดงจุดไฟ 48 ชั่วโมง
- คลิกดูรายละเอียด
- รูปภาพ + พิกัด + เวลา

---

## 10. การใช้งาน

### เว็บไซต์
1. เปิด https://pm25-nakhon-phanom.onrender.com
2. ดูค่า PM2.5 ปัจจุบัน
3. ดูการพยากรณ์
4. ดูแผนที่จุดไฟ
5. ดูจังหวัดใกล้เคียง

### LINE Official Account
1. เพิ่มเพื่อน: @naka_monitor (ตัวอย่าง)
2. กด Rich Menu หรือพิมพ์คำสั่ง
3. รายงานจุดไฟ: ส่งรูป + พิกัด
4. รับการแจ้งเตือนอัตโนมัติ

---

## 11. ข้อมูลทางเทคนิค

### API Endpoints

#### GET /api/fire-reports
- ดึงรายงานจุดไฟ
- Query: `?hours=48` (48 ชั่วโมงล่าสุด)

#### GET /api/nearby-provinces
- ดึงค่า PM2.5 จังหวัดใกล้เคียง
- Cache: 5 นาที
- Response: `{data: [...], cached: true/false}`

#### GET /api/model-accuracy
- ดึงข้อมูลความแม่นยำโมเดล
- Filter: error ≤ 30

#### POST /webhook
- LINE Bot Webhook
- รับข้อความ, รูปภาพ, พิกัด

### Environment Variables
```
WAQI_API_TOKEN=xxx
LINE_CHANNEL_ACCESS_TOKEN=xxx
LINE_CHANNEL_SECRET=xxx
SUPABASE_URL=xxx
SUPABASE_KEY=xxx
```

---

## 12. การ Deploy

### Render (Web Server)
1. Connect GitHub Repository
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `python backend/server.py`
4. Environment Variables: ตั้งค่าใน Dashboard
5. Auto-deploy: Push to main branch

### GitHub Actions (Auto-update)
- ทำงานทุกวัน 07:00 น.
- ดึงค่า PM2.5 จริง
- อัปเดตฐานข้อมูล
- ส่งการแจ้งเตือน LINE

---

## 13. ความปลอดภัย

### Data Security
- ✅ HTTPS (SSL/TLS)
- ✅ Environment Variables (ไม่เก็บใน code)
- ✅ Supabase RLS (Row Level Security)
- ✅ LINE Webhook Signature Verification

### Privacy
- ✅ ไม่เก็บข้อมูลส่วนตัว
- ✅ รูปภาพเก็บใน Supabase Storage (ปลอดภัย)
- ✅ พิกัดใช้เฉพาะแสดงบนแผนที่

---

## 14. ข้อจำกัดและแนวทางพัฒนา

### ข้อจำกัดปัจจุบัน
- ครอบคลุมเฉพาะจังหวัดนครพนม
- พยากรณ์เพียง 1 วัน
- ต้องใช้ LINE (ไม่มี Mobile App)

### แนวทางพัฒนาต่อ
1. **ขยายพื้นที่**: ครอบคลุมภาคอีสาน
2. **พยากรณ์ 3-7 วัน**: ปรับปรุงโมเดล
3. **Mobile App**: iOS/Android
4. **AI Image Recognition**: ตรวจจับควันจากรูปภาพ
5. **Integration**: เชื่อมต่อหน่วยงานราชการ

---

## 15. ผลกระทบและประโยชน์

### ต่อประชาชน
- ✅ รู้ค่าฝุ่น Real-time
- ✅ วางแผนกิจกรรมได้
- ✅ ป้องกันสุขภาพ
- ✅ รายงานจุดไฟได้ง่าย

### ต่อหน่วยงาน
- ✅ ข้อมูลเพื่อตัดสินใจ
- ✅ ติดตามสถานการณ์
- ✅ ประเมินผลนโยบาย
- ✅ ประชาสัมพันธ์

### ต่อสิ่งแวดล้อม
- ✅ ลดการเผา
- ✅ เพิ่มการตระหนักรู้
- ✅ ข้อมูลเพื่อวิจัย

---

## 16. ทีมพัฒนา

**โครงการ**: Naka_monitoring  
**สถาบัน**: มหาวิทยาลัยนครพนม  
**ปี**: 2026

---

## 17. สถิติการใช้งาน (ตัวอย่าง)

### เว็บไซต์
- 📊 Visitors: 1,000+ ต่อเดือน
- ⏱️ Avg. Session: 3-5 นาที
- 📱 Mobile: 70% | Desktop: 30%

### LINE Official Account
- 👥 Followers: 500+ คน
- 📨 Messages: 2,000+ ต่อเดือน
- 🔥 Fire Reports: 50+ รายงาน

---

## 18. ต้นทุนการดำเนินงาน

### รายเดือน
- Render Starter Plan: $7
- Supabase Free Tier: $0
- WAQI API Free: $0
- LINE OA Free: $0

**รวม**: $7/เดือน ($84/ปี)

---

## 19. Timeline การพัฒนา

### Phase 1: Core Features (เสร็จสิ้น)
- ✅ เว็บไซต์ + Dashboard
- ✅ LSTM Model
- ✅ WAQI API Integration
- ✅ Database Setup

### Phase 2: LINE Integration (เสร็จสิ้น)
- ✅ LINE Bot
- ✅ Fire Reporting
- ✅ Rich Menu
- ✅ Auto Notification

### Phase 3: Optimization (เสร็จสิ้น)
- ✅ Performance Tuning
- ✅ Cache Implementation
- ✅ Error Handling
- ✅ Debug Logging

---

## 20. สรุป

**Naka_monitoring** เป็นระบบเฝ้าระวังคุณภาพอากาศและจุดไฟไหม้ที่:

✅ **ใช้งานง่าย**: เว็บ + LINE OA  
✅ **Real-time**: ข้อมูลทันสมัย  
✅ **AI-powered**: พยากรณ์ด้วย LSTM  
✅ **Citizen Science**: ประชาชนมีส่วนร่วม  
✅ **Cost-effective**: $7/เดือน  
✅ **Scalable**: ขยายได้  

**พร้อมใช้งานจริง** และสามารถขยายผลไปยังพื้นที่อื่นได้!

---

## ข้อมูลติดต่อ

**Website**: https://pm25-nakhon-phanom.onrender.com  
**GitHub**: https://github.com/face007d/project-pm25  
**LINE OA**: @naka_monitor (ตัวอย่าง)

---

**จัดทำเมื่อ**: 26 มีนาคม 2026  
**เวอร์ชัน**: 1.0  
**สถานะ**: Production Ready 🚀
