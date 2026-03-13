"""
ตรวจสอบข้อมูลใน Supabase
"""

from backend.database import get_db
from datetime import date

db = get_db()

print("\n" + "=" * 60)
print("📊 ตรวจสอบข้อมูลใน Supabase")
print("=" * 60 + "\n")

# 1. ตรวจสอบข้อมูลค่าจริง (pm25_actual_readings)
print("1️⃣ ตาราง pm25_actual_readings:")
print("-" * 60)
readings = db.get_actual_readings(limit=10, location="Nakhon Phanom")
if readings:
    for i, r in enumerate(readings, 1):
        print(f"\n   {i}. วันที่: {r['reading_date']}")
        print(f"      PM2.5: {r['pm25_value']} µg/m³")
        print(f"      AQI: {r['aqi_level']} ({r['aqi_color']})")
        print(f"      อุณหภูมิ: {r.get('temperature', 'N/A')}°C")
        print(f"      ความชื้น: {r.get('humidity', 'N/A')}%")
        print(f"      Created: {r['created_at']}")
else:
    print("   ❌ ไม่มีข้อมูล")

# 2. ตรวจสอบการพยากรณ์ (pm25_predictions)
print("\n\n2️⃣ ตาราง pm25_predictions:")
print("-" * 60)
predictions = db.get_predictions(limit=10, location="Nakhon Phanom")
if predictions:
    for i, p in enumerate(predictions, 1):
        print(f"\n   {i}. วันที่พยากรณ์: {p['target_date']}")
        print(f"      ค่าพยากรณ์: {p['predicted_value']} µg/m³")
        print(f"      ค่าจริง: {p.get('actual_value', 'ยังไม่มี')} µg/m³")
        if p.get('actual_value'):
            error = abs(p['predicted_value'] - p['actual_value'])
            print(f"      ความผิดพลาด: {error:.2f} µg/m³")
        print(f"      Model: {p['model_version']}")
        print(f"      Created: {p['created_at']}")
else:
    print("   ❌ ไม่มีข้อมูล")

# 3. ตรวจสอบ alert logs
print("\n\n3️⃣ ตาราง alert_logs:")
print("-" * 60)
try:
    result = db.client.table('alert_logs')\
        .select('*')\
        .eq('location', 'Nakhon Phanom')\
        .order('created_at', desc=True)\
        .limit(5)\
        .execute()
    
    alerts = result.data
    if alerts:
        for i, a in enumerate(alerts, 1):
            print(f"\n   {i}. {a['title']}")
            print(f"      Severity: {a['severity']}")
            print(f"      PM2.5: {a.get('pm25_value', 'N/A')} µg/m³")
            print(f"      Message: {a['message']}")
            print(f"      Created: {a['created_at']}")
    else:
        print("   ❌ ไม่มีข้อมูล")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 4. ตรวจสอบ accuracy log
print("\n\n4️⃣ ตาราง prediction_accuracy_log:")
print("-" * 60)
try:
    result = db.client.table('prediction_accuracy_log')\
        .select('*')\
        .order('calculated_at', desc=True)\
        .limit(5)\
        .execute()
    
    accuracy = result.data
    if accuracy:
        for i, a in enumerate(accuracy, 1):
            print(f"\n   {i}. Error: {a.get('error_value', 'N/A'):.2f} µg/m³")
            print(f"      Error %: {a.get('error_percentage', 'N/A'):.2f}%")
            print(f"      Accurate: {'✅' if a.get('is_accurate') else '❌'}")
            print(f"      Calculated: {a['calculated_at']}")
    else:
        print("   ❌ ไม่มีข้อมูล")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 5. สรุป
print("\n\n" + "=" * 60)
print("📈 สรุป")
print("=" * 60)
print(f"   จำนวนข้อมูลค่าจริง: {len(readings)} รายการ")
print(f"   จำนวนการพยากรณ์: {len(predictions)} รายการ")
print(f"   จำนวน alerts: {len(alerts) if 'alerts' in locals() else 0} รายการ")
print(f"   จำนวน accuracy logs: {len(accuracy) if 'accuracy' in locals() else 0} รายการ")

# ตรวจสอบข้อมูลวันนี้โดยเฉพาะ
today = date.today()
print(f"\n   ข้อมูลวันนี้ ({today}):")
today_reading = [r for r in readings if r['reading_date'] == str(today)]
if today_reading:
    print(f"   ✅ มีข้อมูลค่าจริง: {today_reading[0]['pm25_value']} µg/m³")
else:
    print(f"   ❌ ยังไม่มีข้อมูลค่าจริง")

print("\n" + "=" * 60 + "\n")
