from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import numpy as np
import joblib
import os
import warnings
import hmac
import hashlib
import base64
from datetime import date, timedelta, datetime
warnings.filterwarnings('ignore')

# ปิด TensorFlow logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import tensorflow as tf
from tensorflow import keras

# LINE Bot SDK
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage, LocationMessage,
    TextSendMessage, ImageSendMessage
)

# Import database module
try:
    from backend.database import get_db
    db = get_db()
    DB_AVAILABLE = True
    print("✅ Database module loaded successfully")
except Exception as e:
    print(f"⚠️ Database module not available: {e}")
    DB_AVAILABLE = False

# Initialize LINE Bot
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

if LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET:
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(LINE_CHANNEL_SECRET)
    LINE_BOT_AVAILABLE = True
    print("✅ LINE Bot initialized successfully")
else:
    line_bot_api = None
    handler = None
    LINE_BOT_AVAILABLE = False
    print("⚠️ LINE Bot not configured (missing credentials)")

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# หา path ของไฟล์ปัจจุบัน
base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, 'lstm_pm25_model (2).h5')
scaler_path = os.path.join(base_dir, 'scaler (2).pkl')

model = None
scaler = None

# โหลด Model และ Scaler
try:
    if os.path.exists(model_path) and os.path.exists(scaler_path):
        # สร้าง custom objects สำหรับ compatibility
        from tensorflow.keras.layers import InputLayer
        from tensorflow.keras.mixed_precision import Policy
        
        # Custom InputLayer ที่รองรับ batch_shape
        class CustomInputLayer(InputLayer):
            def __init__(self, batch_shape=None, **kwargs):
                if batch_shape is not None:
                    kwargs['batch_input_shape'] = batch_shape
                super().__init__(**kwargs)
        
        # Custom DTypePolicy สำหรับ Keras เก่า
        class DTypePolicy:
            def __init__(self, name='float32'):
                self.name = name
                self._name = name
                
            @property
            def compute_dtype(self):
                return self.name
            
            @property
            def variable_dtype(self):
                return self.name
        
        custom_objects = {
            'InputLayer': CustomInputLayer,
            'DTypePolicy': DTypePolicy,
        }
        
        # โหลด model
        with keras.utils.custom_object_scope(custom_objects):
            model = keras.models.load_model(
                model_path,
                compile=False
            )
        
        scaler = joblib.load(scaler_path)
        print("✅ Model and Scaler loaded successfully!")
        print(f"Model path: {model_path}")
    else:
        print("❌ Error: Missing model or scaler files!")
        print(f"Looking for model at: {model_path}")
        print(f"Looking for scaler at: {scaler_path}")
        print(f"Current directory: {os.getcwd()}")
        if os.path.exists(base_dir):
            print(f"Files in base_dir: {os.listdir(base_dir)}")
except Exception as e:
    print(f"❌ Error loading model: {str(e)}")
    import traceback
    traceback.print_exc()
    print("Server will start but predictions will not work")

@app.route('/')
def home():
    # Serve frontend HTML
    try:
        return app.send_static_file('index.html')
    except:
        return jsonify({
            'status': 'Ready' if model and scaler else 'Model Missing',
            'message': 'PM2.5 Nakhon Phanom API',
            'database': 'Connected' if DB_AVAILABLE else 'Not Connected'
        })

@app.route('/api')
def api_status():
    status = "Ready" if model and scaler else "Model Missing"
    return jsonify({
        'status': status,
        'message': 'PM2.5 Nakhon Phanom API',
        'database': 'Connected' if DB_AVAILABLE else 'Not Connected',
        'line_bot': 'Connected' if LINE_BOT_AVAILABLE else 'Not Configured',
        'endpoints': {
            '/predict': 'POST - Predict PM2.5 value',
            '/api/predictions': 'GET - Get recent predictions',
            '/api/readings': 'GET - Get actual readings',
            '/api/stats': 'GET - Get accuracy statistics',
            '/api/save-reading': 'POST - Save actual reading',
            '/webhook': 'POST - LINE Webhook (Phase 2)',
            '/api/fire-reports': 'GET - Get fire reports (Phase 2)',
            '/api/fire-reports/today': 'GET - Get today fire reports (Phase 2)'
        }
    })

@app.route('/predict', methods=['POST'])
def predict():
    if model is None or scaler is None:
        return jsonify({'error': 'Model not loaded'}), 500
        
    try:
        data = request.get_json()
        # รับข้อมูล 3 วันล่าสุด [v1, v2, v3]
        inputs = np.array(data['inputs']).reshape(-1, 1)
        
        # 2. ทำการ Pre-processing (เหมือนใน Colab)
        input_scaled = scaler.transform(inputs)
        X_input = np.reshape(input_scaled, (1, 3, 1))
        
        # 3. พยากรณ์
        prediction_scaled = model.predict(X_input, verbose=0)
        prediction_final = scaler.inverse_transform(prediction_scaled)
        
        predicted_value = float(prediction_final[0][0])
        
        # 4. บันทึกลง database (ถ้ามี)
        if DB_AVAILABLE:
            try:
                today = date.today()
                tomorrow = today + timedelta(days=1)
                
                input_dict = {
                    "day1": float(inputs[0][0]),
                    "day2": float(inputs[1][0]),
                    "day3": float(inputs[2][0])
                }
                
                db.save_prediction(
                    prediction_date=today,
                    target_date=tomorrow,
                    predicted_value=predicted_value,
                    input_values=input_dict,
                    model_version=os.getenv('MODEL_VERSION', 'v1.0')
                )
            except Exception as e:
                print(f"⚠️ Failed to save prediction to database: {e}")
        
        return jsonify({
            'prediction': predicted_value,
            'unit': 'µg/m³',
            'status': 'success',
            'saved_to_db': DB_AVAILABLE
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    """ดึงข้อมูลการพยากรณ์ล่าสุด"""
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        limit = request.args.get('limit', 10, type=int)
        location = request.args.get('location', 'Nakhon Phanom')
        
        predictions = db.get_predictions(limit=limit, location=location)
        return jsonify({
            'data': predictions,
            'count': len(predictions)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/readings', methods=['GET'])
def get_readings():
    """ดึงข้อมูลค่าจริง"""
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        limit = request.args.get('limit', 10, type=int)
        location = request.args.get('location', 'Nakhon Phanom')
        
        readings = db.get_actual_readings(limit=limit, location=location)
        return jsonify({
            'data': readings,
            'count': len(readings)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """ดึงสถิติความแม่นยำ"""
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        days = request.args.get('days', 30, type=int)
        location = request.args.get('location', 'Nakhon Phanom')
        
        stats = db.get_accuracy_stats(days=days, location=location)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/save-reading', methods=['POST'])
def save_reading():
    """บันทึกค่าจริง (สำหรับ cron job หรือ manual update)"""
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        data = request.get_json()
        
        reading_date = date.fromisoformat(data['reading_date'])
        pm25_value = float(data['pm25_value'])
        
        # คำนวณ AQI level
        aqi_level, aqi_color = db.calculate_aqi_level(pm25_value)
        
        result = db.save_actual_reading(
            reading_date=reading_date,
            pm25_value=pm25_value,
            aqi_level=aqi_level,
            aqi_color=aqi_color,
            temperature=data.get('temperature'),
            humidity=data.get('humidity'),
            wind_speed=data.get('wind_speed'),
            location=data.get('location', 'Nakhon Phanom'),
            data_source=data.get('data_source', 'Manual'),
            raw_data=data.get('raw_data')
        )
        
        # อัปเดตค่าจริงในตาราง predictions
        db.update_actual_value(
            target_date=reading_date,
            actual_value=pm25_value,
            location=data.get('location', 'Nakhon Phanom')
        )
        
        return jsonify({
            'status': 'success',
            'data': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ============================================
# Phase 2: LINE Webhook Endpoints
# ============================================

@app.route('/webhook', methods=['POST'])
def line_webhook():
    """LINE Webhook - รับข้อความจาก LINE OA"""
    if not LINE_BOT_AVAILABLE:
        return 'OK', 200
    
    # ตรวจสอบ signature
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    # Log for debugging
    print(f"📨 Webhook received: {body[:100]}...")
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("❌ Invalid signature")
        return 'Invalid signature', 400
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()
        # Return 200 anyway to prevent LINE from retrying
        return 'OK', 200
    
    return 'OK', 200


def save_fire_report_from_session(user_id, session, reply_token, address=None):
    """บันทึกรายงานไฟไหม้จาก session ที่สมบูรณ์"""
    try:
        # ดึงข้อมูลผู้ใช้
        try:
            profile = line_bot_api.get_profile(user_id)
            display_name = profile.display_name
        except:
            display_name = None
        
        # ดึงค่า PM2.5 ล่าสุด
        pm25_value = None
        try:
            readings = db.get_actual_readings(limit=1)
            if readings:
                pm25_value = readings[0]['pm25_value']
        except:
            pass
        
        # บันทึกรายงาน
        report = db.save_fire_report(
            line_user_id=user_id,
            latitude=session['latitude'],
            longitude=session['longitude'],
            image_url=session['image_url'],
            user_display_name=display_name,
            location_address=address,
            image_message_id=session.get('image_message_id'),
            pm25_value=pm25_value
        )
        
        if report:
            # ทำเครื่องหมาย session ว่าเสร็จแล้ว
            db.complete_session(session['id'])
            
            # ส่งข้อความตอบกลับ
            reply_text = (
                "✅ ขอบคุณสำหรับข้อมูล!\n\n"
                "ระบบได้รับแจ้งเหตุและบันทึกพิกัดลงแผนที่เรียบร้อยแล้ว\n\n"
                f"📍 ตำแหน่ง: {session['latitude']:.6f}, {session['longitude']:.6f}\n"
                f"🕐 เวลา: {datetime.now().strftime('%H:%M น.')}\n\n"
                "ดูแผนที่: https://project-pm25-1.onrender.com"
            )
            
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=reply_text)
            )
            
            print(f"✅ Fire report saved: {report.get('id')}")
        else:
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text="❌ เกิดข้อผิดพลาดในการบันทึกข้อมูล")
            )
    
    except Exception as e:
        print(f"❌ Error saving fire report: {e}")
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text="❌ เกิดข้อผิดพลาดในการบันทึกข้อมูล")
        )


# LINE Message Handlers (only register if LINE Bot is available)
if LINE_BOT_AVAILABLE and handler:
    @handler.add(MessageEvent, message=TextMessage)
    def handle_text_message(event):
        """จัดการข้อความ text"""
        user_id = event.source.user_id
        text = event.message.text.strip()
        
        try:
            # อัปเดตข้อมูลผู้ใช้
            try:
                profile = line_bot_api.get_profile(user_id)
                db.upsert_line_user(
                    line_user_id=user_id,
                    display_name=profile.display_name,
                    picture_url=profile.picture_url,
                    status_message=profile.status_message
                )
            except:
                pass
            
            # คำสั่งพิเศษ
            if text.lower() in ['สวัสดี', 'hello', 'hi', 'เริ่ม', 'start']:
                reply_text = (
                    "🔥 สวัสดีครับ! ยินดีต้อนรับสู่ระบบแจ้งเหตุไฟไหม้\n\n"
                    "📌 วิธีการแจ้งเหตุ:\n"
                    "1️⃣ ส่งรูปภาพจุดไฟไหม้/ควัน\n"
                    "2️⃣ ส่งพิกัดสถานที่ (กดแชร์ Location)\n\n"
                    "⚠️ ต้องส่งครบทั้ง 2 อย่างนะครับ\n\n"
                    "💨 ตรวจสอบค่าฝุ่น PM2.5: พิมพ์ 'ฝุ่น' หรือ 'pm25'"
                )
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
            
            elif text.lower() in ['ฝุ่น', 'pm25', 'pm2.5', 'aqi']:
                # ดึงค่า PM2.5 ล่าสุด
                readings = db.get_actual_readings(limit=1)
                if readings:
                    latest = readings[0]
                    pm25 = latest['pm25_value']
                    level = latest['aqi_level']
                    date_str = latest['reading_date']
                    
                    reply_text = (
                        f"💨 ค่าฝุ่น PM2.5 ล่าสุด\n\n"
                        f"📅 วันที่: {date_str}\n"
                        f"📊 ค่า PM2.5: {pm25:.1f} µg/m³\n"
                        f"🎨 ระดับ: {level}\n\n"
                        f"ดูข้อมูลเพิ่มเติม: https://project-pm25-1.onrender.com"
                    )
                else:
                    reply_text = "ไม่พบข้อมูลค่าฝุ่นในขณะนี้"
                
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
            
            elif text.lower() in ['ช่วยเหลือ', 'help', 'คำสั่ง']:
                reply_text = (
                    "📋 คำสั่งที่ใช้ได้:\n\n"
                    "🔥 แจ้งเหตุไฟไหม้\n"
                    "   → ส่งรูป + พิกัด\n\n"
                    "💨 ตรวจสอบค่าฝุ่น\n"
                    "   → พิมพ์ 'ฝุ่น' หรือ 'pm25'\n\n"
                    "📍 ดูแผนที่จุดไฟไหม้\n"
                    "   → https://project-pm25-1.onrender.com"
                )
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
            
            else:
                # ข้อความทั่วไป
                reply_text = (
                    "ขอบคุณสำหรับข้อความครับ 🙏\n\n"
                    "หากต้องการแจ้งเหตุไฟไหม้:\n"
                    "1️⃣ ส่งรูปภาพจุดไฟไหม้\n"
                    "2️⃣ ส่งพิกัดสถานที่\n\n"
                    "พิมพ์ 'ช่วยเหลือ' เพื่อดูคำสั่งทั้งหมด"
                )
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
        
        except Exception as e:
            print(f"❌ Error handling text message: {e}")

    @handler.add(MessageEvent, message=ImageMessage)
    def handle_image_message(event):
        """จัดการรูปภาพ"""
        user_id = event.source.user_id
        message_id = event.message.id
        
        try:
            # ดาวน์โหลดรูปภาพ
            message_content = line_bot_api.get_message_content(message_id)
            
            # บันทึกรูปชั่วคราว (ในระบบจริงควรอัปโหลดไป cloud storage)
            # ตอนนี้เราจะใช้ LINE CDN URL
            image_url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
            
            # ดึง session ปัจจุบัน
            session = db.get_or_create_session(user_id)
            
            if not session:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌ เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง")
                )
                return
            
            # อัปเดต session ด้วยรูปภาพ
            db.update_session_image(
                session_id=session['id'],
                image_url=image_url,
                image_message_id=message_id
            )
            
            # ตรวจสอบว่ามีพิกัดแล้วหรือยัง
            if session.get('has_location'):
                # มีครบแล้ว! บันทึกรายงาน
                save_fire_report_from_session(user_id, session, event.reply_token)
            else:
                # ยังไม่มีพิกัด
                reply_text = (
                    "✅ ได้รับรูปภาพแล้ว\n\n"
                    "📍 กรุณาส่งพิกัดสถานที่ของจุดไฟไหม้\n"
                    "(กดปุ่ม + → Location → แชร์ตำแหน่งปัจจุบัน)"
                )
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
        
        except Exception as e:
            print(f"❌ Error handling image: {e}")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ เกิดข้อผิดพลาดในการรับรูปภาพ")
            )

    @handler.add(MessageEvent, message=LocationMessage)
    def handle_location_message(event):
        """จัดการพิกัด Location"""
        user_id = event.source.user_id
        latitude = event.message.latitude
        longitude = event.message.longitude
        address = event.message.address or ""
        
        try:
            # ดึง session ปัจจุบัน
            session = db.get_or_create_session(user_id)
            
            if not session:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌ เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง")
                )
                return
            
            # อัปเดต session ด้วยพิกัด
            db.update_session_location(
                session_id=session['id'],
                latitude=latitude,
                longitude=longitude
            )
            
            # ตรวจสอบว่ามีรูปแล้วหรือยัง
            if session.get('has_image'):
                # มีครบแล้ว! บันทึกรายงาน
                save_fire_report_from_session(user_id, session, event.reply_token, address)
            else:
                # ยังไม่มีรูป
                reply_text = (
                    "✅ ได้รับพิกัดแล้ว\n\n"
                    "📷 กรุณาส่งรูปภาพจุดไฟไหม้/ควัน"
                )
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
        
        except Exception as e:
            print(f"❌ Error handling location: {e}")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ เกิดข้อผิดพลาดในการรับพิกัด")
            )


@app.route('/api/fire-reports', methods=['GET'])
def get_fire_reports_api():
    """API: ดึงรายงานจุดไฟไหม้"""
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        limit = request.args.get('limit', 50, type=int)
        status = request.args.get('status')
        
        reports = db.get_fire_reports(limit=limit, status=status)
        return jsonify({
            'data': reports,
            'count': len(reports)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fire-reports/today', methods=['GET'])
def get_fire_reports_today_api():
    """API: ดึงรายงานวันนี้"""
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        reports = db.get_fire_reports_today()
        return jsonify({
            'data': reports,
            'count': len(reports)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
