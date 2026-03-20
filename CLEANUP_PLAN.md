# 🧹 แผนการลบ Mock Data และปรับปรุงระบบ

## 📋 สิ่งที่จะทำ

### ✅ Part 1: ลบ Mock Data + ใช้ WAQI API ครบ

**1. ลบ Mock Data ทั้งหมด:**
- ❌ `STATIONS` - สถานีหลายแห่ง (โรงพยาบาล, ท่าอุเทน, ฯลฯ)
- ❌ `TABLE_ROWS` - ตารางอำเภอต่างๆ
- ❌ `FIRE_REPORTS` - จุดไฟไหม้จำลอง
- ❌ `currentTemp`, `currentHumid`, `currentWind` - ค่าสภาพอากาศจำลอง
- ❌ `HOURLY_FORECAST` - พยากรณ์รายชั่วโมง

**2. ดึงข้อมูลจริงจาก WAQI API:**
```javascript
// ข้อมูลที่จะดึงจาก WAQI API:
{
  pm25: data.iaqi.pm25.v,      // PM2.5
  temp: data.iaqi.t.v,          // อุณหภูมิ
  humidity: data.iaqi.h.v,      // ความชื้น
  wind: data.iaqi.w.v,          // ความเร็วลม
  pressure: data.iaqi.p.v,      // ความกดอากาศ
  dew: data.iaqi.dew.v          // จุดน้ำค้าง
}
```

**3. ปรับ UI:**
- ซ่อนส่วนที่แสดงหลายสถานี
- ซ่อนตารางอำเภอต่างๆ
- เน้นแสดงข้อมูลสถานีเมืองนครพนม
- เพิ่มคำอธิบาย "ข้อมูลจากสถานีตรวจวัด 1 แห่ง"

---

### ✅ Part 2: Auto-Delete Fire Reports หลัง 48 ชั่วโมง

## 🔥 ระบบลบรายงานไฟไหม้อัตโนมัติ

### วิธีที่ 1: Filter ใน Frontend (แนะนำ - ง่ายที่สุด)

**ทำงาน:** กรองข้อมูลก่อนแสดงบนแผนที่

```javascript
async function loadFireReports() {
  const response = await fetch(`${BACKEND_URL}/api/fire-reports`);
  const data = await response.json();
  
  // กรองเฉพาะรายงานที่อายุไม่เกิน 48 ชั่วโมง
  const now = new Date();
  const HOURS_48 = 48 * 60 * 60 * 1000; // 48 hours in milliseconds
  
  const recentReports = data.data.filter(report => {
    const reportTime = new Date(report.created_at);
    const age = now - reportTime;
    return age <= HOURS_48;
  });
  
  // แสดงเฉพาะรายงานล่าสุด
  recentReports.forEach(report => {
    // แสดงบนแผนที่...
  });
}
```

**ข้อดี:**
- ✅ ง่ายที่สุด แก้แค่ Frontend
- ✅ ไม่ต้องแก้ Backend
- ✅ ข้อมูลยังอยู่ใน Database (สำหรับสถิติ)

**ข้อเสีย:**
- ❌ ยังดึงข้อมูลเก่ามาจาก API (เปลือง bandwidth นิดหน่อย)

---

### วิธีที่ 2: Filter ใน Backend API (แนะนำ - มีประสิทธิภาพ)

**ทำงาน:** Backend ส่งเฉพาะรายงานล่าสุด

**แก้ไข `backend/server.py`:**
```python
@app.route('/api/fire-reports', methods=['GET'])
def get_fire_reports_api():
    """API: ดึงรายงานจุดไฟไหม้ (เฉพาะ 48 ชั่วโมงล่าสุด)"""
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        limit = request.args.get('limit', 50, type=int)
        hours = request.args.get('hours', 48, type=int)  # เพิ่มพารามิเตอร์
        
        # คำนวณเวลา 48 ชั่วโมงที่แล้ว
        from datetime import datetime, timedelta
        cutoff_time = datetime.now(THAILAND_TZ) - timedelta(hours=hours)
        
        reports = db.get_fire_reports_recent(
            limit=limit, 
            since=cutoff_time
        )
        
        return jsonify({
            'data': reports,
            'count': len(reports),
            'hours': hours
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**แก้ไข `backend/database.py`:**
```python
def get_fire_reports_recent(
    self,
    limit: int = 50,
    since: datetime = None
) -> List[Dict[str, Any]]:
    """
    ดึงรายงานจุดไฟไหม้ล่าสุด
    
    Args:
        limit: จำนวนรายการ
        since: ดึงเฉพาะรายงานหลังเวลานี้
    """
    try:
        query = self.client.table('fire_reports').select('*')
        
        if since:
            query = query.gte('created_at', since.isoformat())
        
        result = query.order('created_at', desc=True).limit(limit).execute()
        return result.data
    
    except Exception as e:
        print(f"❌ Error getting recent fire reports: {e}")
        return []
```

**ข้อดี:**
- ✅ ประหยัด bandwidth
- ✅ Frontend ไม่ต้องกรอง
- ✅ สามารถปรับเวลาได้ (24h, 48h, 72h)

**ข้อเสีย:**
- ❌ ต้องแก้ทั้ง Backend และ Frontend

---

### วิธีที่ 3: Auto-Delete จาก Database (ไม่แนะนำ)

**ทำงาน:** ลบข้อมูลจริงๆ ออกจาก Database

**ใช้ Supabase Function + Cron:**
```sql
-- สร้าง Function ลบรายงานเก่า
CREATE OR REPLACE FUNCTION delete_old_fire_reports()
RETURNS void AS $$
BEGIN
  DELETE FROM fire_reports
  WHERE created_at < NOW() - INTERVAL '48 hours';
END;
$$ LANGUAGE plpgsql;

-- ตั้ง Cron ให้รันทุกวัน
-- (ต้องใช้ pg_cron extension)
SELECT cron.schedule(
  'delete-old-reports',
  '0 0 * * *',  -- ทุกวันเที่ยงคืน
  'SELECT delete_old_fire_reports();'
);
```

**ข้อดี:**
- ✅ Database เล็กลง
- ✅ ไม่ต้องกรองทุกครั้ง

**ข้อเสีย:**
- ❌ สูญเสียข้อมูลประวัติ (ไม่สามารถดูสถิติย้อนหลังได้)
- ❌ ซับซ้อน ต้องตั้ง Cron
- ❌ Supabase Free Tier อาจไม่รองรับ pg_cron

---

## 🎯 คำแนะนำของผม

### สำหรับ Part 1 (ลบ Mock Data):
✅ **ทำเลย** - แก้ไข Frontend ให้ใช้ WAQI API ครบ

### สำหรับ Part 2 (Auto-Delete Fire Reports):
✅ **ใช้วิธีที่ 2** - Filter ใน Backend API

**เหตุผล:**
1. ไม่สูญเสียข้อมูลประวัติ (เก็บไว้ทำสถิติได้)
2. ประหยัด bandwidth
3. ปรับเวลาได้ง่าย (24h, 48h, 72h)
4. ไม่ซับซ้อน

---

## 📝 ขั้นตอนการทำ

### Step 1: แก้ Frontend (ลบ Mock Data)
```bash
# แก้ไฟล์ frontend/index.html
- ลบ STATIONS, TABLE_ROWS, FIRE_REPORTS
- ลบ currentTemp, currentHumid, currentWind
- ดึงข้อมูลจาก WAQI API แทน
- ซ่อน UI ที่ไม่ใช้
```

### Step 2: แก้ Backend (Filter 48h)
```bash
# แก้ไฟล์ backend/database.py
- เพิ่ม function get_fire_reports_recent()

# แก้ไฟล์ backend/server.py
- แก้ /api/fire-reports ให้รองรับ hours parameter
```

### Step 3: Test
```bash
# ทดสอบ API
curl "http://localhost:5000/api/fire-reports?hours=48"

# ทดสอบ Frontend
# เปิด http://localhost:5000
```

### Step 4: Deploy
```bash
git add .
git commit -m "Remove mock data, use real WAQI data, add 48h filter"
git push origin main
```

---

## 🎨 UI ที่จะปรับ

**ซ่อน:**
- ❌ ตารางอำเภอต่างๆ (TABLE_ROWS)
- ❌ รายการสถานีหลายแห่ง (STATIONS)
- ❌ Mock fire reports

**เน้น:**
- ✅ ข้อมูล PM2.5 จากสถานีเมืองนครพนม
- ✅ ข้อมูลสภาพอากาศจาก WAQI
- ✅ จุดไฟไหม้จริงจาก LINE Bot (48h ล่าสุด)

**เพิ่ม:**
- ✅ คำอธิบาย "ข้อมูลจากสถานีตรวจวัดคุณภาพอากาศ อ.เมืองนครพนม"
- ✅ Badge "แสดงรายงาน 48 ชั่วโมงล่าสุด"

---

## ⏱️ เวลาที่ใช้

- Part 1 (ลบ Mock Data): ~30 นาที
- Part 2 (Auto-Delete 48h): ~20 นาที
- Test + Deploy: ~10 นาที

**รวม: ~1 ชั่วโมง**

---

**พร้อมเริ่มแล้วครับ!** 🚀
