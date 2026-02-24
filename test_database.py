"""
Test script สำหรับทดสอบการเก็บข้อมูลลง Supabase
"""

from datetime import date, timedelta
from backend.database import get_db

def test_database_connection():
    """ทดสอบการเชื่อมต่อ"""
    print("=" * 60)
    print("🧪 Test 1: Database Connection")
    print("=" * 60)
    
    try:
        db = get_db()
        success = db.test_connection()
        if success:
            print("✅ Database connection: SUCCESS\n")
            return db
        else:
            print("❌ Database connection: FAILED\n")
            return None
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return None

def test_save_prediction(db):
    """ทดสอบบันทึกการพยากรณ์"""
    print("=" * 60)
    print("🧪 Test 2: Save Prediction")
    print("=" * 60)
    
    try:
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        # ข้อมูลทดสอบ
        test_data = {
            "prediction_date": today,
            "target_date": tomorrow,
            "predicted_value": 35.2,
            "input_values": {
                "day1": 22.4,
                "day2": 39.7,
                "day3": 25.0
            },
            "model_version": "v1.0",
            "location": "Nakhon Phanom",
            "confidence_score": 0.85
        }
        
        print(f"📝 Saving prediction:")
        print(f"   Prediction Date: {test_data['prediction_date']}")
        print(f"   Target Date: {test_data['target_date']}")
        print(f"   Predicted Value: {test_data['predicted_value']} µg/m³")
        print(f"   Input Values: {test_data['input_values']}")
        
        result = db.save_prediction(**test_data)
        
        if result:
            print(f"✅ Prediction saved successfully!")
            print(f"   ID: {result.get('id', 'N/A')}")
            print(f"   Created at: {result.get('created_at', 'N/A')}\n")
            return result
        else:
            print("❌ Failed to save prediction\n")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return None

def test_save_actual_reading(db):
    """ทดสอบบันทึกค่าจริง"""
    print("=" * 60)
    print("🧪 Test 3: Save Actual Reading")
    print("=" * 60)
    
    try:
        today = date.today()
        pm25_value = 33.5
        
        # คำนวณ AQI level
        aqi_level, aqi_color = db.calculate_aqi_level(pm25_value)
        
        test_data = {
            "reading_date": today,
            "pm25_value": pm25_value,
            "aqi_level": aqi_level,
            "aqi_color": aqi_color,
            "temperature": 28.5,
            "humidity": 65.0,
            "wind_speed": 5.2,
            "location": "Nakhon Phanom",
            "data_source": "Test Script"
        }
        
        print(f"📝 Saving actual reading:")
        print(f"   Reading Date: {test_data['reading_date']}")
        print(f"   PM2.5 Value: {test_data['pm25_value']} µg/m³")
        print(f"   AQI Level: {test_data['aqi_level']}")
        print(f"   AQI Color: {test_data['aqi_color']}")
        print(f"   Temperature: {test_data['temperature']}°C")
        print(f"   Humidity: {test_data['humidity']}%")
        
        result = db.save_actual_reading(**test_data)
        
        if result:
            print(f"✅ Actual reading saved successfully!")
            print(f"   ID: {result.get('id', 'N/A')}")
            print(f"   Created at: {result.get('created_at', 'N/A')}\n")
            return result
        else:
            print("❌ Failed to save actual reading\n")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return None

def test_update_actual_value(db):
    """ทดสอบอัปเดตค่าจริงในตาราง predictions"""
    print("=" * 60)
    print("🧪 Test 4: Update Actual Value in Predictions")
    print("=" * 60)
    
    try:
        tomorrow = date.today() + timedelta(days=1)
        actual_value = 33.5
        
        print(f"📝 Updating actual value:")
        print(f"   Target Date: {tomorrow}")
        print(f"   Actual Value: {actual_value} µg/m³")
        
        success = db.update_actual_value(
            target_date=tomorrow,
            actual_value=actual_value,
            location="Nakhon Phanom"
        )
        
        if success:
            print(f"✅ Actual value updated successfully!\n")
            print(f"   Note: Trigger จะคำนวณ accuracy อัตโนมัติ\n")
        else:
            print("❌ Failed to update actual value\n")
            
        return success
            
    except Exception as e:
        print(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_get_predictions(db):
    """ทดสอบดึงข้อมูลการพยากรณ์"""
    print("=" * 60)
    print("🧪 Test 5: Get Recent Predictions")
    print("=" * 60)
    
    try:
        predictions = db.get_predictions(limit=5, location="Nakhon Phanom")
        
        print(f"📊 Retrieved {len(predictions)} predictions:")
        for i, pred in enumerate(predictions, 1):
            print(f"\n   {i}. Target Date: {pred.get('target_date')}")
            print(f"      Predicted: {pred.get('predicted_value')} µg/m³")
            print(f"      Actual: {pred.get('actual_value', 'N/A')} µg/m³")
            print(f"      Model: {pred.get('model_version')}")
        
        print(f"\n✅ Successfully retrieved predictions\n")
        return predictions
            
    except Exception as e:
        print(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return []

def test_get_readings(db):
    """ทดสอบดึงข้อมูลค่าจริง"""
    print("=" * 60)
    print("🧪 Test 6: Get Recent Readings")
    print("=" * 60)
    
    try:
        readings = db.get_actual_readings(limit=5, location="Nakhon Phanom")
        
        print(f"📊 Retrieved {len(readings)} readings:")
        for i, reading in enumerate(readings, 1):
            print(f"\n   {i}. Date: {reading.get('reading_date')}")
            print(f"      PM2.5: {reading.get('pm25_value')} µg/m³")
            print(f"      AQI: {reading.get('aqi_level')}")
            print(f"      Temp: {reading.get('temperature', 'N/A')}°C")
        
        print(f"\n✅ Successfully retrieved readings\n")
        return readings
            
    except Exception as e:
        print(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return []

def test_save_alert(db):
    """ทดสอบบันทึก alert"""
    print("=" * 60)
    print("🧪 Test 7: Save Alert Log")
    print("=" * 60)
    
    try:
        test_data = {
            "alert_type": "high_pm25",
            "severity": "warning",
            "title": "⚠️ PM2.5 สูงกว่าปกติ",
            "message": "ค่า PM2.5 = 45.0 µg/m³ อยู่ในระดับ 'เริ่มมีผลกระทบ'",
            "pm25_value": 45.0,
            "threshold_value": 37.5,
            "location": "Nakhon Phanom"
        }
        
        print(f"📝 Saving alert:")
        print(f"   Type: {test_data['alert_type']}")
        print(f"   Severity: {test_data['severity']}")
        print(f"   Title: {test_data['title']}")
        print(f"   Message: {test_data['message']}")
        
        result = db.save_alert(**test_data)
        
        if result:
            print(f"✅ Alert saved successfully!")
            print(f"   ID: {result.get('id', 'N/A')}\n")
            return result
        else:
            print("❌ Failed to save alert\n")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return None

def test_get_accuracy_stats(db):
    """ทดสอบดึงสถิติความแม่นยำ"""
    print("=" * 60)
    print("🧪 Test 8: Get Accuracy Statistics")
    print("=" * 60)
    
    try:
        stats = db.get_accuracy_stats(days=30, location="Nakhon Phanom")
        
        print(f"📊 Accuracy Statistics (Last 30 days):")
        if stats:
            print(f"   Total Predictions: {stats.get('total_predictions', 0)}")
            print(f"   Average Error: {stats.get('avg_error', 0):.2f} µg/m³")
            print(f"   Accuracy Rate: {stats.get('accuracy_rate', 0):.2f}%")
        else:
            print(f"   No statistics available yet")
        
        print(f"\n✅ Successfully retrieved statistics\n")
        return stats
            
    except Exception as e:
        print(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return {}

def main():
    """รัน test ทั้งหมด"""
    print("\n")
    print("🚀 " + "=" * 56 + " 🚀")
    print("   SUPABASE DATABASE TEST - PM2.5 Forecasting Project")
    print("🚀 " + "=" * 56 + " 🚀")
    print("\n")
    
    # Test 1: Connection
    db = test_database_connection()
    if not db:
        print("❌ Cannot proceed without database connection")
        return
    
    # Test 2: Save Prediction
    prediction = test_save_prediction(db)
    
    # Test 3: Save Actual Reading
    reading = test_save_actual_reading(db)
    
    # Test 4: Update Actual Value
    test_update_actual_value(db)
    
    # Test 5: Get Predictions
    test_get_predictions(db)
    
    # Test 6: Get Readings
    test_get_readings(db)
    
    # Test 7: Save Alert
    test_save_alert(db)
    
    # Test 8: Get Accuracy Stats
    test_get_accuracy_stats(db)
    
    print("=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    print("\n💡 Tips:")
    print("   - ตรวจสอบข้อมูลใน Supabase Dashboard")
    print("   - ดูตาราง: pm25_predictions, pm25_actual_readings")
    print("   - ดู Views: v_predictions_with_actual, v_daily_accuracy_stats")
    print("\n")

if __name__ == "__main__":
    main()
