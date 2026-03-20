# คู่มือการใช้งานไฟล์ .bat

## ไฟล์ที่มีให้ใช้งาน

### 1. `install.bat` - ติดตั้ง Dependencies
**วิธีใช้:** Double-click หรือรันใน Command Prompt
```
install.bat
```

**ทำอะไร:**
- ตรวจสอบว่ามี Python ติดตั้งหรือไม่
- สร้าง virtual environment (.venv)
- ติดตั้ง packages ทั้งหมดจาก requirements.txt

**เมื่อไหร่ต้องใช้:**
- ครั้งแรกที่ clone โปรเจค
- เมื่อมีการเพิ่ม dependencies ใหม่

---

### 2. `run_server.bat` - รัน Web Server
**วิธีใช้:** Double-click หรือรันใน Command Prompt
```
run_server.bat
```

**ทำอะไร:**
- เปิด Flask web server
- เข้าถึงได้ที่ http://localhost:5000

**เมื่อไหร่ต้องใช้:**
- ทุกครั้งที่ต้องการทดสอบเว็บในเครื่อง
- กด Ctrl+C เพื่อหยุด server

---

### 3. `run_daily_update.bat` - อัปเดตข้อมูล PM2.5
**วิธีใช้:** Double-click หรือรันใน Command Prompt
```
run_daily_update.bat
```

**ทำอะไร:**
- ดึงข้อมูล PM2.5 ล่าสุดจาก WAQI API
- บันทึกลง Supabase database

**เมื่อไหร่ต้องใช้:**
- เมื่อต้องการอัปเดตข้อมูลด้วยตนเอง
- ทดสอบ daily update script

---

### 4. `test_database.bat` - ทดสอบการเชื่อมต่อ Database
**วิธีใช้:** Double-click หรือรันใน Command Prompt
```
test_database.bat
```

**ทำอะไร:**
- ทดสอบการเชื่อมต่อกับ Supabase
- แสดงข้อมูลตัวอย่างจาก database

**เมื่อไหร่ต้องใช้:**
- ตรวจสอบว่า .env ตั้งค่าถูกต้อง
- Debug ปัญหาการเชื่อมต่อ database

---

### 5. `cleanup.bat` - ลบไฟล์ชั่วคราว
**วิธีใช้:** Double-click หรือรันใน Command Prompt
```
cleanup.bat
```

**ทำอะไร:**
- ลบ virtual environment (.venv)
- ลบ Python cache files (__pycache__)
- ลบไฟล์ชั่วคราวอื่นๆ

**เมื่อไหร่ต้องใช้:**
- เมื่อต้องการติดตั้งใหม่ทั้งหมด
- แก้ปัญหา dependencies conflict

---

### 6. `git_push.bat` - Push โค้ดขึ้น GitHub
**วิธีใช้:** Double-click หรือรันใน Command Prompt
```
git_push.bat
```

**ทำอะไร:**
- แสดง git status
- ให้ใส่ commit message
- Add, commit และ push ไปยัง GitHub

**เมื่อไหร่ต้องใช้:**
- เมื่อแก้ไขโค้ดเสร็จและต้องการ backup
- Deploy โค้ดใหม่ไปยัง Render

---

## ลำดับการใช้งานครั้งแรก

1. **ติดตั้ง:** รัน `install.bat`
2. **ตั้งค่า:** สร้างไฟล์ `.env` (copy จาก `.env.example`)
3. **ทดสอบ:** รัน `test_database.bat`
4. **รัน Server:** รัน `run_server.bat`
5. **เปิดเว็บ:** ไปที่ http://localhost:5000

---

## การแก้ปัญหา

### ปัญหา: "Python is not installed"
**แก้ไข:** ติดตั้ง Python 3.11 จาก https://www.python.org/

### ปัญหา: "Virtual environment not found"
**แก้ไข:** รัน `install.bat` ก่อน

### ปัญหา: ".env file not found"
**แก้ไข:** 
1. Copy `.env.example` เป็น `.env`
2. แก้ไขค่าใน `.env` ให้ถูกต้อง

### ปัญหา: Dependencies error
**แก้ไข:**
1. รัน `cleanup.bat`
2. รัน `install.bat` ใหม่

---

## หมายเหตุ

- ไฟล์ .bat ทั้งหมดต้องรันบน Windows เท่านั้น
- สำหรับ Mac/Linux ใช้ไฟล์ .sh แทน
- ตรวจสอบว่ามี Python 3.11+ ติดตั้งแล้ว
- ตรวจสอบว่าไฟล์ `.env` มีค่าครบถ้วน
