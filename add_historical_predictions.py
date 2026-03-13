"""
เพิ่มข้อมูลการพยากรณ์ย้อนหลังเข้า Supabase
โดยใช้ข้อมูลจาก pm25_actual_readings ที่มีอยู่แล้ว
"""

from datetime import date, timedelta
from backend.database import get_db
import requests

db = get_db()

print("\n" + "=" * 70)
print("📝 เพิ่มข้อมูลการพยากรณ์ย้อนหลัง")
print("=" * 70 + "\n")

# ดึงข้อมูลค่าจริงทั้งหมด
print("Step 1: ดึงข้อมูลค่าจริงจาก Database...")
readings = db.get_actual_readings(limit=100, location="Nakhon Phanom")
print(f"✅ พบข้อมูล {len(readings)} รายการ\n")

if len(readings) < 3:
    print("❌ ต้องมีข้อมูลอย่างน้อย 3 วัน ถึงจะพยากรณ์ได้")
    exit(1)

# เรียงข้อมูลจากเก่าไปใหม่
readings = sorted(readings, key=lambda x: x['reading_date'])

print("Step 2: สร้างการพยากรณ์ย้อนหลัง...\n")

success_count = 0
skip_count = 0
error_count = 0

# วนลูปสร้างการพยากรณ์
for i in range(2, len(readings)):
    # ใช้ข้อมูล 3 วันย้อนหลังเพื่อพยากรณ์วันถัดไป
    day1 = readings[i-2]
    day2 = readings[i-1]
    day3 = readings[i]
    
    # วันที่พยากรณ์ = วันที่ของ day3
    prediction_date = date.fromisoformat(day3['reading_date'])
    
    # วันที่พยากรณ์ไว้ = วันถัดจาก day3
    if i + 1 < len(readings):
        target_date = date.fromisoformat(readings[i+1]['reading_date'])
        actual_value = readings[i+1]['pm25_value']
    else:
        # ถ้าไม่มีวันถัดไป ให้พยากรณ์วันพรุ่งนี้
        target_date = prediction_date + timedelta(days=1)
        actual_value = None
    
    # ข้อมูล input 3 วัน
    input_values = {
        "day1": day1['pm25_value'],
        "day2": day2['pm25_value'],
        "day3": day3['pm25_value']
    }
    
    print(f"📅 {prediction_date} → พยากรณ์วันที่ {target_date}")
    print(f"   Input: [{input_values['day1']}, {input_values['day2']}, {input_values['day3']}]")
    
    try:
        # เรียก Prediction API
        api_url = 'http://localhost:5000'  # หรือ https://project-pm25-1.onrender.com
        
        response = requests.post(
            f'{api_url}/predict',
            json={'inputs': [input_values['day1'], input_values['day2'], input_values['day3']]},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            predicted_value = result.get('prediction')
            
            print(f"   ✅ พยากรณ์: {predicted_value:.2f} µg/m³")
            
            if actual_value:
                error = abs(predicted_value - actual_value)
                print(f"   ✅ ค่าจริง: {actual_value} µg/m³ (Error: {error:.2f})")
                
                # อัปเดตค่าจริง
                db.update_actual_value(
                    target_date=target_date,
                    actual_value=actual_value,
                    location="Nakhon Phanom"
                )
            else:
                print(f"   ⏳ รอค่าจริง")
            
            success_count += 1
            print()
            
        else:
            print(f"   ❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            error_count += 1
            print()
            
    except requests.exceptions.ConnectionError:
        print(f"   ⚠️ ไม่สามารถเชื่อมต่อ API ได้ (Server ไม่ทำงาน)")
        print(f"   💡 ใช้การพยากรณ์แบบง่าย (ค่าเฉลี่ย 3 วัน)")
        
        # ใช้วิธีง่ายๆ: ค่าเฉลี่ยของ 3 วัน
        predicted_value = (input_values['day1'] + input_values['day2'] + input_values['day3']) / 3
        
        print(f"   ✅ พยากรณ์ (Simple Average): {predicted_value:.2f} µg/m³")
        
        # บันทึกลง database โดยตรง
        try:
            db.save_prediction(
                prediction_date=prediction_date,
                target_date=target_date,
                predicted_value=predicted_value,
                input_values=input_values,
                model_version="v1.0-simple",
                location="Nakhon Phanom"
            )
            
            if actual_value:
                error = abs(predicted_value - actual_value)
                print(f"   ✅ ค่าจริง: {actual_value} µg/m³ (Error: {error:.2f})")
                
                db.update_actual_value(
                    target_date=target_date,
                    actual_value=actual_value,
                    location="Nakhon Phanom"
                )
            
            success_count += 1
            print()
            
        except Exception as e:
            print(f"   ❌ Error saving: {e}")
            error_count += 1
            print()
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        error_count += 1
        print()

print("=" * 70)
print("📊 สรุปผลการทำงาน")
print("=" * 70)
print(f"✅ สำเร็จ: {success_count} รายการ")
print(f"⏭️  ข้าม: {skip_count} รายการ")
print(f"❌ ผิดพลาด: {error_count} รายการ")
print()

# ตรวจสอบข้อมูลทั้งหมด
print("=" * 70)
print("📊 ตรวจสอบข้อมูลทั้งหมดใน Database")
print("=" * 70 + "\n")

predictions = db.get_predictions(limit=20, location="Nakhon Phanom")
print(f"จำนวนการพยากรณ์ทั้งหมด: {len(predictions)} รายการ\n")

for i, pred in enumerate(predictions, 1):
    actual = pred.get('actual_value')
    if actual:
        error = abs(pred['predicted_value'] - actual)
        status = f"✅ Error: {error:.2f}"
    else:
        status = "⏳ รอค่าจริง"
    
    print(f"{i}. {pred['target_date']}: พยากรณ์ {pred['predicted_value']:.2f} | จริง {actual or 'N/A'} | {status}")

print("\n" + "=" * 70)
print("✅ เสร็จสิ้น!")
print("=" * 70 + "\n")
