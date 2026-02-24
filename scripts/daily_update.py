"""
Daily Update Script - รันอัตโนมัติทุกวัน
ดึงข้อมูล PM2.5 จาก WAQI API และบันทึกลง Supabase
"""

import os
import sys
import requests
from datetime import date, datetime, timedelta
from dotenv import load_dotenv

# เพิ่ม path เพื่อ import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db

# โหลด environment variables
load_dotenv()

# Configuration
WAQI_API_TOKEN = os.getenv('WAQI_API_TOKEN', '6e19dc4d73747ab27c397b590fdbd504f1f496fc')
LOCATION = os.getenv('LOCATION', 'Nakhon Phanom')
WAQI_STATION_ID = '@9696'  # Nakhon Phanom station ID

def fetch_waqi_data():
    """ดึงข้อมูล PM2.5 จาก WAQI API"""
    try:
        url = f'https://api.waqi.info/feed/{WAQI_STATION_ID}/?token={WAQI_API_TOKEN}'
        
        print(f"🌐 Fetching data from WAQI API...")
        print(f"   URL: {url}")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') != 'ok':
            print(f"❌ WAQI API error: {data.get('data', 'Unknown error')}")
            return None
        
        return data.get('data')
        
    except Exception as e:
        print(f"❌ Error fetching WAQI data: {e}")
        return None

def calculate_aqi_level(pm25_value):
    """คำนวณระดับ AQI"""
    if pm25_value <= 15.0:
        return ('ดีมาก', '#28b4d8')
    elif pm25_value <= 25.0:
        return ('ดี', '#2ecc71')
    elif pm25_value <= 37.5:
        return ('ปานกลาง', '#f1c40f')
    elif pm25_value <= 75.0:
        return ('เริ่มมีผลกระทบ', '#e67e22')
    else:
        return ('มีผลกระทบต่อสุขภาพ', '#e74c3c')

def save_actual_reading(db, waqi_data):
    """บันทึกค่า PM2.5 จริงลง Supabase"""
    try:
        # ดึงค่า PM2.5
        pm25_value = waqi_data.get('iaqi', {}).get('pm25', {}).get('v')
        
        if pm25_value is None:
            print("❌ No PM2.5 data available")
            return False
        
        # ดึงข้อมูลเพิ่มเติม
        iaqi = waqi_data.get('iaqi', {})
        temperature = iaqi.get('t', {}).get('v')
        humidity = iaqi.get('h', {}).get('v')
        wind_speed = iaqi.get('w', {}).get('v')
        
        # คำนวณ AQI level
        aqi_level, aqi_color = calculate_aqi_level(pm25_value)
        
        today = date.today()
        
        print(f"\n📝 Saving actual reading:")
        print(f"   Date: {today}")
        print(f"   PM2.5: {pm25_value} µg/m³")
        print(f"   AQI Level: {aqi_level}")
        print(f"   Temperature: {temperature}°C")
        print(f"   Humidity: {humidity}%")
        
        # บันทึกลง database
        result = db.save_actual_reading(
            reading_date=today,
            pm25_value=pm25_value,
            aqi_level=aqi_level,
            aqi_color=aqi_color,
            temperature=temperature,
            humidity=humidity,
            wind_speed=wind_speed,
            location=LOCATION,
            data_source='WAQI API',
            raw_data=waqi_data
        )
        
        if result:
            print(f"✅ Actual reading saved successfully!")
            
            # อัปเดตค่าจริงในตาราง predictions (ถ้ามีการพยากรณ์ไว้)
            db.update_actual_value(
                target_date=today,
                actual_value=pm25_value,
                location=LOCATION
            )
            print(f"✅ Updated actual value in predictions table")
            
            return True
        else:
            print(f"❌ Failed to save actual reading")
            return False
            
    except Exception as e:
        print(f"❌ Error saving actual reading: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_recent_pm25_values(db):
    """ดึงค่า PM2.5 ล่าสุด 3 วัน สำหรับพยากรณ์"""
    try:
        readings = db.get_actual_readings(limit=3, location=LOCATION)
        
        if len(readings) < 3:
            print(f"⚠️ Not enough data for prediction (need 3 days, have {len(readings)})")
            return None
        
        # เรียงจากเก่าไปใหม่
        readings = sorted(readings, key=lambda x: x['reading_date'])
        
        values = [r['pm25_value'] for r in readings]
        print(f"\n📊 Recent 3 days PM2.5 values:")
        for i, r in enumerate(readings, 1):
            print(f"   Day {i} ({r['reading_date']}): {r['pm25_value']} µg/m³")
        
        return values
        
    except Exception as e:
        print(f"❌ Error getting recent values: {e}")
        return None

def make_prediction(db, input_values):
    """ทำการพยากรณ์ PM2.5 วันพรุ่งนี้"""
    try:
        # เรียก prediction API
        api_url = os.getenv('API_URL', 'https://project-pm25-1.onrender.com')
        
        print(f"\n🔮 Making prediction for tomorrow...")
        print(f"   Input values: {input_values}")
        
        response = requests.post(
            f'{api_url}/predict',
            json={'inputs': input_values},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            predicted_value = result.get('prediction')
            
            print(f"✅ Prediction successful!")
            print(f"   Predicted PM2.5 for tomorrow: {predicted_value:.2f} µg/m³")
            
            # บันทึกการพยากรณ์ (API จะบันทึกอัตโนมัติ)
            return predicted_value
        else:
            print(f"❌ Prediction failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error making prediction: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_and_send_alert(db, pm25_value):
    """ตรวจสอบและส่ง alert ถ้าค่า PM2.5 สูง"""
    try:
        # เกณฑ์การแจ้งเตือน
        if pm25_value > 75.0:
            severity = 'critical'
            title = '🚨 PM2.5 สูงมาก!'
            message = f'ค่า PM2.5 = {pm25_value:.1f} µg/m³ อยู่ในระดับ "มีผลกระทบต่อสุขภาพ" กรุณาหลีกเลี่ยงกิจกรรมกลางแจ้ง'
            threshold = 75.0
        elif pm25_value > 37.5:
            severity = 'warning'
            title = '⚠️ PM2.5 สูงกว่าปกติ'
            message = f'ค่า PM2.5 = {pm25_value:.1f} µg/m³ อยู่ในระดับ "เริ่มมีผลกระทบ" ควรระวังสุขภาพ'
            threshold = 37.5
        else:
            print(f"✅ PM2.5 level is normal ({pm25_value:.1f} µg/m³)")
            return
        
        print(f"\n🔔 Sending alert:")
        print(f"   Severity: {severity}")
        print(f"   Title: {title}")
        
        # บันทึก alert log
        db.save_alert(
            alert_type='high_pm25',
            severity=severity,
            title=title,
            message=message,
            pm25_value=pm25_value,
            threshold_value=threshold,
            location=LOCATION
        )
        
        print(f"✅ Alert saved to database")
        
        # TODO: ส่ง LINE Notify (เพิ่มในอนาคต)
        # send_line_notify(message)
        
    except Exception as e:
        print(f"❌ Error sending alert: {e}")

def main():
    """Main function - รันทุกวัน"""
    print("\n" + "=" * 70)
    print("🤖 DAILY UPDATE SCRIPT - PM2.5 Forecasting System")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70 + "\n")
    
    try:
        # 1. เชื่อมต่อ database
        print("Step 1: Connecting to database...")
        db = get_db()
        if not db.test_connection():
            print("❌ Database connection failed. Exiting.")
            return
        print("✅ Database connected\n")
        
        # 2. ดึงข้อมูลจาก WAQI API
        print("Step 2: Fetching data from WAQI API...")
        waqi_data = fetch_waqi_data()
        if not waqi_data:
            print("❌ Failed to fetch WAQI data. Exiting.")
            return
        print("✅ WAQI data fetched\n")
        
        # 3. บันทึกค่าจริง
        print("Step 3: Saving actual reading to database...")
        if not save_actual_reading(db, waqi_data):
            print("❌ Failed to save actual reading. Exiting.")
            return
        
        pm25_value = waqi_data.get('iaqi', {}).get('pm25', {}).get('v')
        
        # 4. ตรวจสอบและส่ง alert
        print("\nStep 4: Checking alert conditions...")
        check_and_send_alert(db, pm25_value)
        
        # 5. ดึงข้อมูล 3 วันล่าสุดสำหรับพยากรณ์
        print("\nStep 5: Getting recent data for prediction...")
        input_values = get_recent_pm25_values(db)
        
        if input_values:
            # 6. ทำการพยากรณ์
            print("\nStep 6: Making prediction for tomorrow...")
            predicted_value = make_prediction(db, input_values)
            
            if predicted_value:
                # ตรวจสอบว่าการพยากรณ์สูงหรือไม่
                if predicted_value > 37.5:
                    print(f"\n⚠️ Tomorrow's prediction is high: {predicted_value:.2f} µg/m³")
        else:
            print("\n⚠️ Skipping prediction (not enough historical data)")
        
        print("\n" + "=" * 70)
        print("✅ Daily update completed successfully!")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error in main function: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
