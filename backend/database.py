"""
Supabase Database Connection Module
เชื่อมต่อและจัดการข้อมูลกับ Supabase
"""

import os
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv

# โหลด environment variables
load_dotenv()

class SupabaseDB:
    """Class สำหรับจัดการ Supabase database"""
    
    def __init__(self):
        """Initialize Supabase client"""
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not self.url or not self.key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment variables")
        
        self.client: Client = create_client(self.url, self.key)
        print(f"✅ Connected to Supabase: {self.url}")
    
    # ==========================================
    # PM2.5 Predictions
    # ==========================================
    
    def save_prediction(
        self,
        prediction_date: date,
        target_date: date,
        predicted_value: float,
        input_values: Dict[str, float],
        model_version: str = "v1.0",
        location: str = "Nakhon Phanom",
        confidence_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        บันทึกการพยากรณ์ PM2.5
        
        Args:
            prediction_date: วันที่ทำการพยากรณ์
            target_date: วันที่พยากรณ์ไว้ (พรุ่งนี้)
            predicted_value: ค่าที่พยากรณ์
            input_values: ข้อมูล 3 วันที่ใช้พยากรณ์ {"day1": 22.4, "day2": 39.7, "day3": 25.0}
            model_version: เวอร์ชันของ model
            location: สถานที่
            confidence_score: ความมั่นใจ (0-1)
        
        Returns:
            Dict ของข้อมูลที่บันทึก
        """
        try:
            data = {
                "prediction_date": str(prediction_date),
                "target_date": str(target_date),
                "predicted_value": predicted_value,
                "input_values": input_values,
                "model_version": model_version,
                "location": location,
                "data_source": "LSTM Model",
            }
            
            if confidence_score is not None:
                data["confidence_score"] = confidence_score
            
            result = self.client.table('pm25_predictions').insert(data).execute()
            print(f"✅ Saved prediction: {predicted_value} for {target_date}")
            return result.data[0] if result.data else {}
        
        except Exception as e:
            print(f"❌ Error saving prediction: {e}")
            return {}
    
    def get_predictions(
        self,
        limit: int = 10,
        location: str = "Nakhon Phanom"
    ) -> List[Dict[str, Any]]:
        """
        ดึงข้อมูลการพยากรณ์
        
        Args:
            limit: จำนวนข้อมูลที่ต้องการ
            location: สถานที่
        
        Returns:
            List ของการพยากรณ์
        """
        try:
            result = self.client.table('pm25_predictions')\
                .select('*')\
                .eq('location', location)\
                .order('target_date', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data
        
        except Exception as e:
            print(f"❌ Error getting predictions: {e}")
            return []
    
    def update_actual_value(
        self,
        target_date: date,
        actual_value: float,
        location: str = "Nakhon Phanom"
    ) -> bool:
        """
        อัปเดตค่าจริงของการพยากรณ์
        
        Args:
            target_date: วันที่พยากรณ์ไว้
            actual_value: ค่าจริงที่เกิดขึ้น
            location: สถานที่
        
        Returns:
            True ถ้าสำเร็จ
        """
        try:
            result = self.client.table('pm25_predictions')\
                .update({"actual_value": actual_value})\
                .eq('target_date', str(target_date))\
                .eq('location', location)\
                .execute()
            
            print(f"✅ Updated actual value: {actual_value} for {target_date}")
            return True
        
        except Exception as e:
            print(f"❌ Error updating actual value: {e}")
            return False
    
    # ==========================================
    # PM2.5 Actual Readings
    # ==========================================
    
    def save_actual_reading(
        self,
        reading_date: date,
        pm25_value: float,
        aqi_level: str,
        aqi_color: str,
        location: str = "Nakhon Phanom",
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        wind_speed: Optional[float] = None,
        data_source: str = "WAQI API",
        raw_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        บันทึกค่า PM2.5 จริง
        
        Args:
            reading_date: วันที่วัด
            pm25_value: ค่า PM2.5
            aqi_level: ระดับคุณภาพอากาศ
            aqi_color: สีของระดับ
            location: สถานที่
            temperature: อุณหภูมิ
            humidity: ความชื้น
            wind_speed: ความเร็วลม
            data_source: แหล่งข้อมูล
            raw_data: ข้อมูลดิบทั้งหมด
        
        Returns:
            Dict ของข้อมูลที่บันทึก
        """
        try:
            data = {
                "reading_date": str(reading_date),
                "reading_time": datetime.now().isoformat(),
                "pm25_value": pm25_value,
                "aqi_level": aqi_level,
                "aqi_color": aqi_color,
                "location": location,
                "data_source": data_source,
            }
            
            if temperature is not None:
                data["temperature"] = temperature
            if humidity is not None:
                data["humidity"] = humidity
            if wind_speed is not None:
                data["wind_speed"] = wind_speed
            if raw_data is not None:
                data["raw_data"] = raw_data
            
            # ใช้ upsert เพื่อ update ถ้ามีข้อมูลวันนั้นแล้ว
            result = self.client.table('pm25_actual_readings')\
                .upsert(data, on_conflict='reading_date,location')\
                .execute()
            
            print(f"✅ Saved actual reading: {pm25_value} for {reading_date}")
            return result.data[0] if result.data else {}
        
        except Exception as e:
            print(f"❌ Error saving actual reading: {e}")
            return {}
    
    def get_actual_readings(
        self,
        limit: int = 10,
        location: str = "Nakhon Phanom"
    ) -> List[Dict[str, Any]]:
        """
        ดึงข้อมูลค่าจริง
        
        Args:
            limit: จำนวนข้อมูล
            location: สถานที่
        
        Returns:
            List ของค่าจริง
        """
        try:
            result = self.client.table('pm25_actual_readings')\
                .select('*')\
                .eq('location', location)\
                .order('reading_date', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data
        
        except Exception as e:
            print(f"❌ Error getting actual readings: {e}")
            return []
    
    # ==========================================
    # Accuracy & Analytics
    # ==========================================
    
    def get_accuracy_stats(
        self,
        days: int = 30,
        location: str = "Nakhon Phanom"
    ) -> Dict[str, Any]:
        """
        ดึงสถิติความแม่นยำ
        
        Args:
            days: จำนวนวันย้อนหลัง
            location: สถานที่
        
        Returns:
            Dict ของสถิติ
        """
        try:
            # ใช้ view ที่สร้างไว้
            result = self.client.rpc(
                'get_accuracy_stats',
                {'days_back': days, 'loc': location}
            ).execute()
            
            return result.data[0] if result.data else {}
        
        except Exception as e:
            print(f"❌ Error getting accuracy stats: {e}")
            # Fallback: query ธรรมดา
            return self._get_accuracy_stats_fallback(days, location)
    
    def _get_accuracy_stats_fallback(
        self,
        days: int,
        location: str
    ) -> Dict[str, Any]:
        """Fallback method สำหรับดึงสถิติ"""
        try:
            result = self.client.table('prediction_accuracy_log')\
                .select('error_value, error_percentage, is_accurate')\
                .execute()
            
            if not result.data:
                return {}
            
            errors = [r['error_value'] for r in result.data if r.get('error_value')]
            accurate = [r for r in result.data if r.get('is_accurate')]
            
            return {
                'total_predictions': len(result.data),
                'avg_error': sum(errors) / len(errors) if errors else 0,
                'accuracy_rate': len(accurate) / len(result.data) * 100 if result.data else 0
            }
        
        except Exception as e:
            print(f"❌ Error in fallback stats: {e}")
            return {}
    
    def get_recent_predictions_with_actual(
        self,
        days: int = 7,
        location: str = "Nakhon Phanom"
    ) -> List[Dict[str, Any]]:
        """
        ดึงข้อมูลพยากรณ์พร้อมค่าจริง
        
        Args:
            days: จำนวนวันย้อนหลัง
            location: สถานที่
        
        Returns:
            List ของข้อมูล
        """
        try:
            # ใช้ view
            result = self.client.table('v_predictions_with_actual')\
                .select('*')\
                .eq('location', location)\
                .limit(days)\
                .execute()
            
            return result.data
        
        except Exception as e:
            print(f"❌ Error getting predictions with actual: {e}")
            return []
    
    # ==========================================
    # Alert Logs
    # ==========================================
    
    def save_alert(
        self,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        pm25_value: Optional[float] = None,
        threshold_value: Optional[float] = None,
        location: str = "Nakhon Phanom"
    ) -> Dict[str, Any]:
        """
        บันทึก alert log
        
        Args:
            alert_type: ประเภท alert
            severity: ระดับความรุนแรง (info, warning, critical)
            title: หัวข้อ
            message: ข้อความ
            pm25_value: ค่า PM2.5
            threshold_value: ค่าเกณฑ์
            location: สถานที่
        
        Returns:
            Dict ของ alert ที่บันทึก
        """
        try:
            data = {
                "alert_type": alert_type,
                "severity": severity,
                "title": title,
                "message": message,
                "location": location,
            }
            
            if pm25_value is not None:
                data["pm25_value"] = pm25_value
            if threshold_value is not None:
                data["threshold_value"] = threshold_value
            
            result = self.client.table('alert_logs').insert(data).execute()
            print(f"✅ Saved alert: {title}")
            return result.data[0] if result.data else {}
        
        except Exception as e:
            print(f"❌ Error saving alert: {e}")
            return {}
    
    # ==========================================
    # Utility Functions
    # ==========================================
    
    def calculate_aqi_level(self, pm25_value: float) -> tuple[str, str]:
        """
        คำนวณระดับ AQI จากค่า PM2.5
        
        Args:
            pm25_value: ค่า PM2.5
        
        Returns:
            Tuple (level, color)
        """
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
    
    def test_connection(self) -> bool:
        """ทดสอบการเชื่อมต่อ"""
        try:
            result = self.client.table('pm25_predictions').select('id').limit(1).execute()
            print("✅ Database connection test: SUCCESS")
            return True
        except Exception as e:
            print(f"❌ Database connection test: FAILED - {e}")
            return False


# Singleton instance
_db_instance = None

def get_db() -> SupabaseDB:
    """Get database instance (singleton)"""
    global _db_instance
    if _db_instance is None:
        _db_instance = SupabaseDB()
    return _db_instance


# ==========================================
# Example Usage
# ==========================================

if __name__ == "__main__":
    # ทดสอบการเชื่อมต่อ
    db = get_db()
    db.test_connection()
    
    # ตัวอย่างการบันทึกการพยากรณ์
    from datetime import date, timedelta
    
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    # บันทึกการพยากรณ์
    prediction = db.save_prediction(
        prediction_date=today,
        target_date=tomorrow,
        predicted_value=35.2,
        input_values={"day1": 22.4, "day2": 39.7, "day3": 25.0},
        model_version="v1.0",
        confidence_score=0.85
    )
    print(f"Prediction saved: {prediction}")
    
    # บันทึกค่าจริง
    level, color = db.calculate_aqi_level(33.5)
    reading = db.save_actual_reading(
        reading_date=today,
        pm25_value=33.5,
        aqi_level=level,
        aqi_color=color,
        temperature=28.5,
        humidity=65.0
    )
    print(f"Reading saved: {reading}")
    
    # ดึงข้อมูล
    predictions = db.get_predictions(limit=5)
    print(f"Recent predictions: {len(predictions)} items")
    
    # ดูสถิติ
    stats = db.get_accuracy_stats(days=30)
    print(f"Accuracy stats: {stats}")
