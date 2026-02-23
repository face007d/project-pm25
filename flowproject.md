# 🌊 PM2.5 Air Quality Forecasting Project - Flow Documentation
## โครงการพยากรณ์คุณภาพอากาศ PM2.5 จังหวัดนครพนม

---

## 📋 ภาพรวมโครงการ (Project Overview)

โครงการนี้เป็นระบบพยากรณ์ค่า PM2.5 สำหรับจังหวัดนครพนม โดยใช้ LSTM Neural Network Model พร้อมระบบ Dashboard แบบ Real-time และการจัดเก็บข้อมูลใน Supabase Database

### เทคโนโลยีที่ใช้
- **Backend**: Flask (Python)
- **ML Model**: LSTM (TensorFlow/Keras 2.12)
- **Database**: Supabase (PostgreSQL)
- **Frontend**: HTML/CSS/JavaScript (Thai-themed UI with Naga design)
- **Deployment**: Render.com
- **Data Source**: WAQI API

### ลิงก์สำคัญ
- **GitHub Repository**: https://github.com/face007d/project-pm25
- **Production URL**: https://project-pm25-1.onrender.com

---

## ✅ สิ่งที่ทำเสร็จแล้ว (Completed Tasks)

### 1. การตั้งค่าโครงการเบื้องต้น (Initial Setup)
- ✅ สร้าง `.gitignore` สำหรับ Python project
- ✅ แก้ไข `requirements.txt` ให้ถูกต้อง (เดิมมี Python code แทนที่จะเป็น dependencies)
- ✅ Push โครงการขึ้น GitHub
- ✅ สร้าง README.md พร้อมคำอธิบายโครงการ

### 2. การ Deploy บน Render.com
- ✅ สร้าง `runtime.txt` กำหนด Python version 3.11.9
- ✅ สร้าง `.python-version` สำหรับ version control
- ✅ สร้าง `Procfile` สำหรับ Gunicorn: `gunicorn backend.server:app`
- ✅ แก้ไขปัญหา dependency conflicts:
  - TensorFlow 2.15 → 2.12.0
  - numpy 1.24.3 → 1.23.5 (เพื่อ compatibility กับ TensorFlow 2.12)
  - เพิ่ม keras==2.12.0, h5py==3.8.0, protobuf==3.20.3
- ✅ Deploy สำเร็จที่ https://project-pm25-1.onrender.com

### 3. แก้ไขปัญหา Model Loading
- ✅ สร้าง `CustomInputLayer` class เพื่อแปลง `batch_shape` → `batch_input_shape`
- ✅ สร้าง `DTypePolicy` custom class สำหรับ compatibility
- ✅ ใช้ `keras.utils.custom_object_scope()` ในการโหลด model
- ✅ เพิ่ม error handling และ logging ที่ครบถ้วน
- ✅ Model โหลดสำเร็จบน Render

### 4. Frontend Integration
- ✅ แก้ไข Flask app ให้ serve frontend HTML
- ✅ เพิ่ม route `/` สำหรับ index.html
- ✅ เพิ่ม route `/api` สำหรับ API status
- ✅ Frontend แสดงผลได้ที่ https://project-pm25-1.onrender.com
- ✅ UI ใช้ Thai-themed design พร้อมลาย Naga (พญานาค)

### 5. Database Schema Design
- ✅ ออกแบบ database schema ครบถ้วน 5 ตาราง:
  1. **pm25_predictions** - เก็บการพยากรณ์และค่าจริง
  2. **pm25_actual_readings** - เก็บค่า PM2.5 จริงที่วัดได้
  3. **prediction_accuracy_log** - ติดตามความแม่นยำของ model
  4. **model_versions** - version control สำหรับ ML models
  5. **alert_logs** - ประวัติการแจ้งเตือน

### 6. Supabase Integration
- ✅ สร้าง `database/schema.sql` พร้อม:
  - Tables, Indexes, Constraints
  - Triggers สำหรับ auto-update timestamps
  - Functions สำหรับคำนวณ AQI level และ accuracy
  - Views สำหรับ common queries
  - Row Level Security (RLS) policies
- ✅ สร้าง `database/README.md` พร้อมคำแนะนำการใช้งาน
- ✅ สร้าง `.env.example` template
- ✅ สร้าง `backend/database.py` module พร้อม:
  - SupabaseDB class (Singleton pattern)
  - Methods: save_prediction, get_predictions, update_actual_value
  - Methods: save_actual_reading, get_actual_readings
  - Methods: get_accuracy_stats, save_alert
  - Utility: calculate_aqi_level, test_connection
- ✅ อัปเดต `backend/server.py` เพื่อใช้ database module
- ✅ เพิ่ม API endpoints ใหม่:
  - `GET /api/predictions` - ดึงการพยากรณ์ล่าสุด
  - `GET /api/readings` - ดึงค่าจริง
  - `GET /api/stats` - ดึงสถิติความแม่นยำ
  - `POST /api/save-reading` - บันทึกค่าจริง
- ✅ แก้ไข `POST /predict` ให้บันทึกการพยากรณ์ลง database อัตโนมัติ
- ✅ เพิ่ม dependencies: `supabase==2.3.4`, `python-dotenv==1.0.0`
- ✅ User ยืนยันว่ารัน SQL สร้าง tables สำเร็จแล้ว

---

## 🔄 สิ่งที่กำลังดำเนินการ (In Progress)

### 1. การตั้งค่า Environment Variables
- ⏳ ต้องตั้งค่า environment variables ใน Render dashboard:
  ```
  SUPABASE_URL=https://your-project.supabase.co
  SUPABASE_SERVICE_KEY=your-service-role-key
  MODEL_VERSION=v1.0
  LOCATION=Nakhon Phanom
  ```

### 2. ทดสอบการเชื่อมต่อ Database บน Production
- ⏳ ทดสอบว่า database connection ทำงานได้บน Render
- ⏳ ตรวจสอบว่า predictions ถูกบันทึกลง Supabase

---

## 📝 สิ่งที่ต้องทำต่อ (TODO / Future Enhancements)

### Priority 1: Core Functionality

#### 1.1 Automated Data Collection (Cron Job)
**เป้าหมาย**: ดึงข้อมูล PM2.5 จาก WAQI API อัตโนมัติทุกวัน

**สิ่งที่ต้องทำ**:
- [ ] สร้าง script `scripts/fetch_daily_pm25.py` สำหรับดึงข้อมูลจาก WAQI API
- [ ] บันทึกข้อมูลลง `pm25_actual_readings` table
- [ ] อัปเดต `actual_value` ใน `pm25_predictions` table
- [ ] ตั้งค่า Cron Job บน Render หรือใช้ GitHub Actions
- [ ] กำหนดเวลารัน: ทุกวันเวลา 00:00 น. (เที่ยงคืน)

**ตัวอย่าง Code Structure**:
```python
# scripts/fetch_daily_pm25.py
import requests
from datetime import date
from backend.database import get_db

def fetch_waqi_data():
    # ดึงข้อมูลจาก WAQI API
    # บันทึกลง database
    pass

if __name__ == "__main__":
    fetch_waqi_data()
```

#### 1.2 Frontend Integration with Database
**เป้าหมาย**: แสดงข้อมูลจาก database แทนการเรียก WAQI API โดยตรง

**สิ่งที่ต้องทำ**:
- [ ] แก้ไข `frontend/index.html` ให้เรียก API endpoints ใหม่
- [ ] แสดงกราฟเปรียบเทียบค่าพยากรณ์ vs ค่าจริง
- [ ] แสดงสถิติความแม่นยำของ model
- [ ] เพิ่มตาราง historical data 7-30 วัน
- [ ] เพิ่ม loading states และ error handling

**API Endpoints ที่ใช้**:
```javascript
// ดึงการพยากรณ์ล่าสุด
fetch('/api/predictions?limit=7')

// ดึงค่าจริง
fetch('/api/readings?limit=7')

// ดึงสถิติ
fetch('/api/stats?days=30')
```

#### 1.3 Alert System (LINE Notify)
**เป้าหมาย**: แจ้งเตือนเมื่อค่า PM2.5 สูงเกินเกณฑ์

**สิ่งที่ต้องทำ**:
- [ ] สมัคร LINE Notify API Token
- [ ] สร้าง `backend/line_notify.py` module
- [ ] เพิ่ม function `send_alert()` ใน database.py
- [ ] ตั้งเกณฑ์การแจ้งเตือน:
  - PM2.5 > 37.5 (ปานกลาง) → Warning
  - PM2.5 > 75.0 (มีผลกระทบ) → Critical
- [ ] บันทึก alert logs ลง database
- [ ] ทดสอบการส่ง notification

**ตัวอย่าง Code**:
```python
# backend/line_notify.py
def send_line_alert(message, token):
    url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {token}'}
    data = {'message': message}
    requests.post(url, headers=headers, data=data)
```

---

### Priority 2: Analytics & Monitoring

#### 2.1 Model Performance Dashboard
**เป้าหมาย**: ติดตามประสิทธิภาพของ model

**สิ่งที่ต้องทำ**:
- [ ] สร้างหน้า `/dashboard/analytics`
- [ ] แสดงกราฟ MAE, RMSE, MAPE ตามเวลา
- [ ] แสดง accuracy rate (%)
- [ ] แสดงการกระจายของ errors (histogram)
- [ ] เปรียบเทียบ performance ระหว่าง model versions

#### 2.2 Data Quality Monitoring
**เป้าหมาย**: ตรวจสอบคุณภาพข้อมูล

**สิ่งที่ต้องทำ**:
- [ ] ตรวจสอบ missing data
- [ ] ตรวจสอบ outliers (ค่าผิดปกติ)
- [ ] แจ้งเตือนเมื่อไม่มีข้อมูลอัปเดต
- [ ] สร้าง data quality report

---

### Priority 3: Model Improvements

#### 3.1 Model Retraining Pipeline
**เป้าหมาย**: ปรับปรุง model ด้วยข้อมูลใหม่

**สิ่งที่ต้องทำ**:
- [ ] สร้าง script `scripts/retrain_model.py`
- [ ] ดึงข้อมูลจาก database สำหรับ training
- [ ] Train model ใหม่
- [ ] เปรียบเทียบ performance กับ model เก่า
- [ ] บันทึก model version ใหม่ลง `model_versions` table
- [ ] Deploy model ใหม่ถ้า performance ดีขึ้น

#### 3.2 Feature Engineering
**เป้าหมาย**: เพิ่ม features เพื่อปรับปรุงความแม่นยำ

**Features ที่อาจเพิ่ม**:
- [ ] ข้อมูลสภาพอากาศ (อุณหภูมิ, ความชื้น, ลม)
- [ ] ข้อมูลฤดูกาล (หน้าแล้ง, หน้าฝน)
- [ ] ข้อมูลวันหยุด/วันทำงาน
- [ ] ข้อมูลจากพื้นที่ใกล้เคียง

#### 3.3 Multi-day Forecasting
**เป้าหมาย**: พยากรณ์ล่วงหน้ามากกว่า 1 วัน

**สิ่งที่ต้องทำ**:
- [ ] ปรับ model architecture สำหรับ multi-step prediction
- [ ] พยากรณ์ 3-7 วันล่วงหน้า
- [ ] แสดงผลบน frontend
- [ ] ประเมิน accuracy สำหรับแต่ละวัน

---

### Priority 4: User Experience

#### 4.1 Mobile Responsive Design
**เป้าหมาย**: ปรับปรุง UI สำหรับมือถือ

**สิ่งที่ต้องทำ**:
- [ ] ทดสอบบนหน้าจอขนาดต่างๆ
- [ ] ปรับ CSS สำหรับ mobile
- [ ] เพิ่ม touch gestures
- [ ] ปรับปรุง loading speed

#### 4.2 Multi-language Support
**เป้าหมาย**: รองรับหลายภาษา

**สิ่งที่ต้องทำ**:
- [ ] เพิ่มปุ่มสลับภาษา (ไทย/English)
- [ ] แปล UI text
- [ ] แปล alert messages
- [ ] แปล documentation

#### 4.3 User Settings
**เป้าหมาย**: ให้ผู้ใช้ปรับแต่งได้

**สิ่งที่ต้องทำ**:
- [ ] เลือกหน่วยวัด (µg/m³ หรือ AQI)
- [ ] ตั้งค่า alert threshold
- [ ] เลือก notification channel
- [ ] เลือกสี theme

---

### Priority 5: API & Integration

#### 5.1 Public API
**เป้าหมาย**: เปิด API ให้หน่วยงานอื่นใช้

**สิ่งที่ต้องทำ**:
- [ ] สร้าง API documentation (Swagger/OpenAPI)
- [ ] เพิ่ม API authentication (API keys)
- [ ] เพิ่ม rate limiting
- [ ] สร้าง API usage dashboard

**API Endpoints**:
```
GET /api/v1/current - ค่า PM2.5 ปัจจุบัน
GET /api/v1/forecast - การพยากรณ์
GET /api/v1/history - ข้อมูลย้อนหลัง
GET /api/v1/stats - สถิติ
```

#### 5.2 Integration with Government Systems
**เป้าหมาย**: เชื่อมต่อกับระบบราชการ

**สิ่งที่ต้องทำ**:
- [ ] ส่งข้อมูลไปยัง PCD (กรมควบคุมมลพิษ)
- [ ] ส่งข้อมูลไปยัง CMUCCDC (ศูนย์ข้อมูลเชียงใหม่)
- [ ] รับข้อมูลจากสถานีตรวจวัดของรัฐ

---

### Priority 6: DevOps & Infrastructure

#### 6.1 Monitoring & Logging
**เป้าหมาย**: ติดตามสถานะระบบ

**สิ่งที่ต้องทำ**:
- [ ] ตั้งค่า application logging (Sentry หรือ LogRocket)
- [ ] ตั้งค่า uptime monitoring (UptimeRobot)
- [ ] ตั้งค่า performance monitoring (New Relic)
- [ ] สร้าง health check endpoint

#### 6.2 Backup & Recovery
**เป้าหมาย**: ป้องกันการสูญหายของข้อมูล

**สิ่งที่ต้องทำ**:
- [ ] ตั้งค่า automatic database backup (Supabase)
- [ ] สร้าง backup script สำหรับ model files
- [ ] ทดสอบ recovery procedure
- [ ] สร้าง disaster recovery plan

#### 6.3 CI/CD Pipeline
**เป้าหมาย**: Automate deployment

**สิ่งที่ต้องทำ**:
- [ ] ตั้งค่า GitHub Actions
- [ ] Auto-deploy เมื่อ push ไป main branch
- [ ] Run tests ก่อน deploy
- [ ] Auto-rollback ถ้า deploy ล้มเหลว

---

### Priority 7: Documentation & Testing

#### 7.1 Documentation
**เป้าหมาย**: เอกสารครบถ้วน

**สิ่งที่ต้องทำ**:
- [ ] เขียน API documentation
- [ ] เขียน deployment guide
- [ ] เขียน user manual
- [ ] เขียน developer guide
- [ ] สร้าง video tutorials

#### 7.2 Testing
**เป้าหมาย**: ทดสอบระบบอย่างครบถ้วน

**สิ่งที่ต้องทำ**:
- [ ] เขียน unit tests (pytest)
- [ ] เขียน integration tests
- [ ] เขียน API tests
- [ ] ทดสอบ load testing
- [ ] ทดสอบ security

---

## 🗂️ โครงสร้างไฟล์ (File Structure)

```
project-pm25/
├── backend/
│   ├── server.py              # Flask application (✅ มี database integration)
│   ├── database.py            # Supabase connection module (✅ เสร็จ)
│   ├── lstm_pm25_model (2).h5 # LSTM model file
│   └── scaler (2).pkl         # Data scaler
├── database/
│   ├── schema.sql             # Database schema (✅ เสร็จ)
│   └── README.md              # Database documentation (✅ เสร็จ)
├── frontend/
│   └── index.html             # Dashboard UI (⏳ ต้องแก้ไขให้ใช้ database)
├── scripts/                   # (📝 ต้องสร้าง)
│   ├── fetch_daily_pm25.py    # Cron job script
│   └── retrain_model.py       # Model retraining script
├── .env                       # Environment variables (⏳ ต้องตั้งค่า)
├── .env.example               # Template (✅ เสร็จ)
├── .gitignore                 # Git ignore (✅ เสร็จ)
├── .python-version            # Python version (✅ เสร็จ)
├── Procfile                   # Render deployment (✅ เสร็จ)
├── requirements.txt           # Python dependencies (✅ เสร็จ)
├── runtime.txt                # Python runtime (✅ เสร็จ)
├── README.md                  # Project documentation (✅ เสร็จ)
└── flowproject.md             # This file (✅ เสร็จ)
```

---

## 📊 Database Schema Summary

### Tables
1. **pm25_predictions** - การพยากรณ์ PM2.5
2. **pm25_actual_readings** - ค่า PM2.5 จริง
3. **prediction_accuracy_log** - ความแม่นยำ
4. **model_versions** - เวอร์ชัน model
5. **alert_logs** - ประวัติการแจ้งเตือน

### Key Features
- Auto-calculate accuracy เมื่อมีค่าจริง (Trigger)
- Views สำหรับ common queries
- Functions สำหรับคำนวณ AQI level
- Row Level Security (RLS)

---

## 🔑 Environment Variables ที่ต้องตั้งค่า

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# WAQI API
WAQI_API_TOKEN=6e19dc4d73747ab27c397b590fdbd504f1f496fc

# Application
FLASK_ENV=production
MODEL_VERSION=v1.0
LOCATION=Nakhon Phanom

# LINE Notify (สำหรับอนาคต)
LINE_NOTIFY_TOKEN=your-line-token
```

---

## 🎯 เป้าหมายระยะสั้น (Next 1-2 Weeks)

1. ✅ ตั้งค่า environment variables บน Render
2. ✅ ทดสอบ database connection บน production
3. 📝 สร้าง cron job สำหรับดึงข้อมูลอัตโนมัติ
4. 📝 แก้ไข frontend ให้ใช้ database API
5. 📝 ทดสอบระบบทั้งหมด end-to-end

---

## 🎯 เป้าหมายระยะยาว (Next 1-3 Months)

1. 📝 เพิ่ม LINE Notify alert system
2. 📝 สร้าง analytics dashboard
3. 📝 ปรับปรุง model ด้วยข้อมูลใหม่
4. 📝 เพิ่ม multi-day forecasting
5. 📝 เปิด Public API

---

## 📞 ติดต่อ & Support

- **GitHub**: https://github.com/face007d/project-pm25
- **Production**: https://project-pm25-1.onrender.com

---

## 📝 บันทึกการเปลี่ยนแปลง (Changelog)

### 2026-02-23
- ✅ สร้าง database schema ครบถ้วน
- ✅ สร้าง database.py module
- ✅ เพิ่ม API endpoints สำหรับ database
- ✅ อัปเดต requirements.txt
- ✅ สร้าง flowproject.md

### 2026-02-22
- ✅ แก้ไขปัญหา model loading compatibility
- ✅ Deploy สำเร็จบน Render
- ✅ Frontend integration เสร็จ
- ✅ ออกแบบ database schema

### 2026-02-21
- ✅ Push project ขึ้น GitHub
- ✅ สร้าง .gitignore และ requirements.txt
- ✅ ตั้งค่า Render deployment

---

**หมายเหตุ**: เอกสารนี้จะอัปเดตเป็นระยะตามความคืบหน้าของโครงการ

---

*สร้างโดย: Kiro AI Assistant*  
*วันที่: 23 กุมภาพันธ์ 2026*
