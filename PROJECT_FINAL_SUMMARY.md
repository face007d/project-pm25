# 📊 สรุปโครงการ: ระบบพยากรณ์และเฝ้าระวังคุณภาพอากาศ PM2.5 นครพนม

## 🎯 ชื่อโครงการ
**"พญานาคเฝ้าฟ้า" - PM2.5 Air Quality Forecasting & Fire Monitoring System**

---

## 📝 ภาพรวมโครงการ

ระบบพยากรณ์คุณภาพอากาศ PM2.5 และเฝ้าระวังจุดไฟไหม้สำหรับจังหวัดนครพนม ประกอบด้วย:
1. **Dashboard เว็บไซต์** - แสดงข้อมูล PM2.5 แบบ real-time และพยากรณ์
2. **LINE Official Account** - รับรายงานจุดไฟไหม้จากประชาชน
3. **แผนที่แสดงจุดไฟไหม้** - แสดงตำแหน่งและรูปภาพจุดไฟไหม้บนแผนที่

---

## 🏗️ สถาปัตยกรรมระบบ

### Frontend
- **Framework**: HTML, CSS (Tailwind), JavaScript
- **UI Theme**: Cyber Command Center (Dark Mode + Neon Effects)
- **Charts**: ApexCharts
- **Map**: Leaflet.js + OpenStreetMap
- **Hosting**: Render (Static + Backend)

### Backend
- **Framework**: Flask (Python)
- **ML Model**: LSTM (TensorFlow/Keras) สำหรับพยากรณ์ PM2.5
- **API Integration**: 
  - WAQI API (World Air Quality Index)
  - LINE Messaging API
- **Hosting**: Render

### Database
- **Platform**: Supabase (PostgreSQL)
- **Tables**:
  - `predictions` - ข้อมูลการพยากรณ์
  - `actual_readings` - ค่าจริงจากสถานี
  - `fire_reports` - รายงานจุดไฟไหม้
  - `line_users` - ข้อมูลผู้ใช้ LINE
  - `user_sessions` - session การรายงาน

### Storage
- **Platform**: Supabase Storage
- **Bucket**: `fire_image` (เก็บรูปภาพจุดไฟไหม้)
- **Features**: 
  - Auto-resize รูปเป็น 768px
  - Compress เป็น JPEG quality 85
  - Public URL ไม่หมดอายุ

---

## ✨ ฟีเจอร์หลัก

### 1. 📊 Dashboard (Web)
- **ค่า PM2.5 ปัจจุบัน** - Real-time จาก WAQI API
- **พยากรณ์ 3 วัน** - ใช้ LSTM Model
- **กราฟแนวโน้ม** - แสดงข้อมูล 7 วันย้อนหลัง + พยากรณ์
- **ตารางข้อมูล** - ประวัติการพยากรณ์และค่าจริง
- **แผนที่จุดไฟไหม้** - แสดงตำแหน่งและรูปภาพ
- **ระดับคุณภาพอากาศ** - แสดงสีตามมาตรฐาน AQI
- **Live Data Simulation** - อัปเดตทุก 5 วินาที
- **Download CSV** - ดาวน์โหลดข้อมูลเป็นไฟล์

### 2. 🤖 LINE Official Account (@726lnjeu)
**คำสั่งที่ใช้ได้:**
- `ฝุ่น` / `pm25` - ตรวจสอบค่า PM2.5 ปัจจุบัน
- `สวัสดี` / `hello` - เมนูหลัก
- `help` - ดูคำสั่งทั้งหมด

**การรายงานจุดไฟไหม้:**
1. ส่งรูปภาพจุดไฟไหม้/ควัน
2. ส่ง Location (พิกัด GPS)
3. ระบบบันทึกและแสดงบนแผนที่อัตโนมัติ

### 3. 🗺️ แผนที่จุดไฟไหม้
- แสดงรูปภาพจริงเป็น marker
- คลิกดูรายละเอียด (พิกัด, เวลา, ผู้รายงาน, PM2.5)
- รองรับทั้งมือถือและคอมพิวเตอร์
- Auto-zoom ไปยังจุดที่มีไฟไหม้

---

## 🎨 UI/UX Design

### Cyber Command Center Theme
- **สีหลัก**: Dark Navy (#0A0E27) + Neon Cyan (#48DBFB)
- **เอฟเฟกต์**:
  - Glassmorphism cards พร้อมขอบ neon
  - Scanning animation บนการ์ด
  - Holographic color shift
  - Neon glow บนข้อความและไอคอน
  - Pulse animation สำหรับสถานะ live
  - Grid pattern background
  - Glitch effect สำหรับค่าวิกฤต

### Responsive Design
- ✅ Mobile-first approach
- ✅ Tablet optimized
- ✅ Desktop full-screen
- ✅ แผนที่ปรับขนาดตามหน้าจอ

---

## 🔧 เทคโนโลยีที่ใช้

### Machine Learning
- **Model**: LSTM (Long Short-Term Memory)
- **Input**: ค่า PM2.5 3 วันย้อนหลัง
- **Output**: พยากรณ์วันถัดไป
- **Preprocessing**: MinMaxScaler
- **Framework**: TensorFlow 2.x + Keras

### APIs & Services
1. **WAQI API** - ข้อมูล PM2.5 real-time
2. **LINE Messaging API** - รับ-ส่งข้อความ
3. **Supabase API** - Database + Storage
4. **Leaflet.js** - แผนที่โต้ตอบได้

### Automation
- **GitHub Actions** - Auto-update ข้อมูลทุกวัน 18:00 น.
- **Cron Job** - ดึงข้อมูล PM2.5 และพยากรณ์อัตโนมัติ

---

## 📁 โครงสร้างโปรเจค

```
pm25_web_project/
├── frontend/
│   ├── index.html              # Dashboard หลัก (Cyber Theme)
│   ├── dashboard_v2.html       # Dashboard รุ่นเก่า
│   └── command_center.html     # Template ทดสอบ
│
├── backend/
│   ├── server.py               # Flask API Server
│   ├── database.py             # Supabase Database Functions
│   ├── lstm_pm25_model (2).h5  # LSTM Model
│   └── scaler (2).pkl          # MinMaxScaler
│
├── database/
│   ├── schema.sql              # Database Schema
│   ├── phase2_fire_reports_schema.sql
│   ├── fix_rls_policies.sql    # Row Level Security
│   └── README.md
│
├── scripts/
│   ├── daily_update.py         # Auto-update script
│   └── fetch_daily_pm25.py     # Fetch PM2.5 data
│
├── .github/workflows/
│   └── daily-update.yml        # GitHub Actions
│
├── requirements.txt            # Python dependencies
├── Procfile                    # Render deployment
├── runtime.txt                 # Python version
└── .env                        # Environment variables
```

---

## 🚀 Deployment

### Production URL
- **Website**: https://project-pm25.onrender.com
- **LINE OA**: @726lnjeu (พญานาคเฝ้าฟ้า)

### Hosting
- **Platform**: Render (Free Tier)
- **Region**: Singapore
- **Auto-deploy**: Push to `main` branch

### Environment Variables
```
SUPABASE_URL=https://anjyzpskodrwxjsrbdds.supabase.co
SUPABASE_KEY=<anon_key>
SUPABASE_SERVICE_KEY=<service_role_key>
WAQI_API_TOKEN=<token>
LINE_CHANNEL_ACCESS_TOKEN=<token>
LINE_CHANNEL_SECRET=<secret>
FLASK_ENV=production
MODEL_VERSION=v1.0
LOCATION=Nakhon Phanom
```

---

## 📊 ข้อมูลและแหล่งที่มา

### ข้อมูล PM2.5
- **แหล่ง**: WAQI (World Air Quality Index)
- **สถานี**: Nakhon Phanom, Thailand (UID: 9696)
- **ความถี่**: Real-time (อัปเดตทุกชั่วโมง)

### ข้อมูลจุดไฟไหม้
- **แหล่ง**: รายงานจากประชาชนผ่าน LINE OA
- **ข้อมูล**: รูปภาพ, พิกัด GPS, เวลา, ผู้รายงาน

---

## 🎯 ผลลัพธ์และความสำเร็จ

### ✅ สิ่งที่ทำสำเร็จ
1. ✅ Dashboard แสดงข้อมูล PM2.5 real-time
2. ✅ LSTM Model พยากรณ์ PM2.5 ได้
3. ✅ LINE Bot รับรายงานจุดไฟไหม้
4. ✅ อัปโหลดรูปไปยัง Supabase Storage
5. ✅ แผนที่แสดงจุดไฟไหม้พร้อมรูปภาพ
6. ✅ UI Cyber Command Center สุดอลังการ
7. ✅ Responsive ทั้งมือถือและคอมพิวเตอร์
8. ✅ Auto-update ข้อมูลทุกวัน
9. ✅ Deploy บน Render สำเร็จ

### 🔧 ปัญหาที่แก้ไขได้
1. ✅ แผนที่ไม่โหลดจุดไฟไหม้ → แก้ด้วย service_role key
2. ✅ รูปภาพหมดอายุ → อัปโหลดไปยัง Supabase Storage
3. ✅ แผนที่ไม่เต็มหน้าจอ → ใช้ calc(100vh-400px)
4. ✅ Timezone ไม่ตรง → ใช้ Asia/Bangkok
5. ✅ Bucket not found → เพิ่ม SUPABASE_SERVICE_KEY

---

## 📈 สถิติโครงการ

- **จำนวนไฟล์**: 30+ ไฟล์
- **บรรทัดโค้ด**: ~3,000+ บรรทัด
- **API Endpoints**: 10+ endpoints
- **Database Tables**: 5 ตาราง
- **Commits**: 20+ commits
- **Development Time**: 1 วัน (intensive)

---

## 🔮 แนวทางพัฒนาต่อ (Future Enhancements)

### Phase 3 - Advanced Features
1. **Notification System**
   - แจ้งเตือนเมื่อ PM2.5 เกินมาตรฐาน
   - แจ้งเตือนเมื่อมีจุดไฟไหม้ใกล้ตัว

2. **Analytics Dashboard**
   - สถิติรายเดือน/รายปี
   - เปรียบเทียบกับปีที่แล้ว
   - Heatmap แสดงพื้นที่เสี่ยง

3. **AI Enhancements**
   - ปรับปรุง LSTM Model ให้แม่นยำขึ้น
   - พยากรณ์ 7 วันล่วงหน้า
   - ทำนายแนวโน้มไฟป่า

4. **Community Features**
   - ระบบ upvote/downvote รายงาน
   - Comment บนจุดไฟไหม้
   - Leaderboard ผู้รายงานยอดนิยม

5. **Mobile App**
   - React Native / Flutter
   - Push Notifications
   - Offline Mode

---

## 👥 ทีมพัฒนา

- **Developer**: คุณ (ผู้พัฒนาหลัก)
- **AI Assistant**: Kiro (ช่วยเขียนโค้ดและแก้ปัญหา)
- **Design**: Cyber Command Center Theme
- **Testing**: Manual Testing + User Feedback

---

## 📞 ติดต่อและสนับสนุน

- **LINE OA**: @726lnjeu
- **Website**: https://project-pm25.onrender.com
- **GitHub**: https://github.com/face007d/project-pm25
- **Supabase Project**: anjyzpskodrwxjsrbdds

---

## 📜 License & Credits

### Open Source Libraries
- Flask (BSD License)
- TensorFlow (Apache 2.0)
- Leaflet.js (BSD 2-Clause)
- ApexCharts (MIT)
- Tailwind CSS (MIT)

### Data Sources
- WAQI (World Air Quality Index)
- OpenStreetMap Contributors
- LINE Corporation

### Special Thanks
- Supabase (Database & Storage)
- Render (Hosting)
- WAQI Team (Air Quality Data)

---

## 🎉 สรุป

โครงการ "พญานาคเฝ้าฟ้า" เป็นระบบเฝ้าระวังคุณภาพอากาศและจุดไฟไหม้ที่ครบวงจร ผสมผสานเทคโนโลยี Machine Learning, Real-time Data, และ Community Reporting เข้าด้วยกัน พร้อม UI สุดอลังการแบบ Cyber Command Center ที่ใช้งานง่ายทั้งบนมือถือและคอมพิวเตอร์

**ระบบพร้อมใช้งานจริงแล้ว!** 🚀✨

---

*สร้างเมื่อ: 14 มีนาคม 2026*  
*เวอร์ชัน: 2.0 (Cyber Theme)*  
*สถานะ: Production Ready ✅*
