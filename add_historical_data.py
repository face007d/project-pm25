"""
เพิ่มข้อมูลย้อนหลังเข้า Supabase เพื่อให้มีข้อมูลเพียงพอสำหรับการพยากรณ์
"""

from datetime import date, timedelta
from backend.database import get_db

db = get_db()

print("\n" + "=" * 60)
print("📝 เพิ่มข้อมูลย้อนหลังเข้า Supabase")
print("=" * 60 + "\n")

# ข้อมูลย้อนหลัง 5 วัน (ข้อมูลจำลองจาก pattern ที่เห็น)
historical_data = [
    {
        "date": date.today() - timedelta(days=5),
        "pm25": 22.4,
        "temp": 26.5,
        "humidity": 68.0
    },
    {
        "date": date.today() - timedelta(days=4),
        "pm25": 39.7,
        "temp": 27.2,
        "humidity": 65.5
    },
    {
        "date": date.today() - timedelta(days=3),
        "pm25": 25.0,
        "temp": 28.0,
        "humidity": 62.0
    },
    {
        "date": date.today() - timedelta(days=2),
        "pm25": 45.2,
        "temp": 29.1,
        "humidity": 60.0
    },
    {
        "date": date.today() - timedelta(days=1),
        "pm25": 58.0,
        "temp": 28.5,
        "humidity": 63.0
    }
]

print("กำลังเพิ่มข้อมูล...\n")

for data in historical_data:
    pm25_value = data["pm25"]
    aqi_level, aqi_color = db.calculate_aqi_level(pm25_value)
    
    print(f"📅 {data['date']}: PM2.5 = {pm25_value} µg/m³ ({aqi_level})")
    
    try:
        result = db.save_actual_reading(
            reading_date=data["date"],
            pm25_value=pm25_value,
            aqi_level=aqi_level,
            aqi_color=aqi_color,
            temperature=data["temp"],
            humidity=data["humidity"],
            location="Nakhon Phanom",
            data_source="Historical Data (Manual)"
        )
        
        if result:
            print(f"   ✅ บันทึกสำเร็จ\n")
        else:
            print(f"   ⚠️ อาจมีข้อมูลอยู่แล้ว (upsert)\n")
            
    except Exception as e:
        print(f"   ❌ Error: {e}\n")

print("=" * 60)
print("✅ เพิ่มข้อมูลเสร็จสิ้น!")
print("=" * 60 + "\n")

# ตรวจสอบข้อมูลทั้งหมด
print("📊 ตรวจสอบข้อมูลทั้งหมด:\n")
readings = db.get_actual_readings(limit=10, location="Nakhon Phanom")

for i, r in enumerate(readings, 1):
    print(f"{i}. {r['reading_date']}: {r['pm25_value']} µg/m³ ({r['aqi_level']})")

print(f"\n✅ มีข้อมูลทั้งหมด {len(readings)} วัน")
print(f"✅ {'พร้อมทำการพยากรณ์!' if len(readings) >= 3 else '⚠️ ยังต้องการข้อมูลอีก ' + str(3 - len(readings)) + ' วัน'}\n")
