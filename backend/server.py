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
from zoneinfo import ZoneInfo
import io
from PIL import Image
warnings.filterwarnings('ignore')

# Thailand timezone
THAILAND_TZ = ZoneInfo("Asia/Bangkok")

# ปิด TensorFlow logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import tensorflow as tf
from tensorflow import keras

# LINE Bot SDK
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage, LocationMessage,
    TextSendMessage, ImageSendMessage,
    QuickReply, QuickReplyButton, MessageAction, URIAction
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


def create_rich_menu():
    """สร้าง Rich Menu สำหรับ LINE Bot"""
    if not LINE_BOT_AVAILABLE:
        return None
    
    try:
        from linebot.models import RichMenu, RichMenuSize, RichMenuArea, RichMenuBounds, URIAction, MessageAction
        
        # สร้าง Rich Menu
        rich_menu_to_create = RichMenu(
            size=RichMenuSize(width=2500, height=843),
            selected=True,
            name="PM2.5 Menu",
            chat_bar_text="เมนูหลัก",
            areas=[
                RichMenuArea(
                    bounds=RichMenuBounds(x=0, y=0, width=833, height=843),
                    action=MessageAction(label='ตรวจสอบค่าฝุ่น', text='ตรวจสอบค่าฝุ่น')
                ),
                RichMenuArea(
                    bounds=RichMenuBounds(x=833, y=0, width=834, height=843),
                    action=MessageAction(label='รายงานไฟไหม้', text='รายงานไฟไหม้')
                ),
                RichMenuArea(
                    bounds=RichMenuBounds(x=1667, y=0, width=833, height=843),
                    action=URIAction(label='ดูแผนที่', uri='https://project-pm25-1.onrender.com')
                )
            ]
        )
        
        rich_menu_id = line_bot_api.create_rich_menu(rich_menu=rich_menu_to_create)
        print(f"✅ Rich Menu created: {rich_menu_id}")
        
        # TODO: อัพโหลดรูปภาพ Rich Menu ด้วย line_bot_api.set_rich_menu_image()
        # ต้องมีไฟล์รูป 2500x843 px
        
        return rich_menu_id
    except Exception as e:
        print(f"⚠️ Could not create Rich Menu: {e}")
        return None

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
            '/api/fire-reports/today': 'GET - Get today fire reports (Phase 2)',
            '/api/create-rich-menu': 'POST - Create LINE Rich Menu (Phase 2)'
        }
    })

@app.route('/api/create-rich-menu', methods=['POST'])
def api_create_rich_menu():
    """API endpoint สำหรับสร้าง Rich Menu"""
    if not LINE_BOT_AVAILABLE:
        return jsonify({'error': 'LINE Bot not configured'}), 400
    
    rich_menu_id = create_rich_menu()
    if rich_menu_id:
        return jsonify({
            'success': True,
            'rich_menu_id': rich_menu_id,
            'message': 'Rich Menu created successfully. Upload image at: https://developers.line.biz/console/'
        })
    else:
        return jsonify({'error': 'Failed to create Rich Menu'}), 500

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


def upload_image_to_supabase(image_content, user_id, message_id):
    """
    ดาวน์โหลดรูปจาก LINE, resize เป็น 768px, และอัพโหลดไปยัง Supabase Storage
    Returns: public URL ของรูปภาพ หรือ None ถ้าล้มเหลว
    """
    try:
        # ตรวจสอบ credentials
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            print("⚠️ Supabase credentials not found")
            return None
        
        # อ่านข้อมูลรูปภาพ
        image_data = b''
        for chunk in image_content.iter_content():
            image_data += chunk
        
        print(f"📥 Downloaded image: {len(image_data)} bytes")
        
        # เปิดรูปด้วย PIL
        image = Image.open(io.BytesIO(image_data))
        print(f"🖼️ Original image size: {image.size}")
        
        # Resize ให้กว้างสุด 768px (รักษาอัตราส่วน)
        max_width = 768
        if image.width > max_width:
            ratio = max_width / image.width
            new_height = int(image.height * ratio)
            image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
            print(f"📐 Resized to: {image.size}")
        
        # แปลงเป็น RGB ถ้าเป็น RGBA
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        
        # บันทึกเป็น JPEG ใน memory
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)
        
        print(f"💾 Compressed to: {len(output.getvalue())} bytes")
        
        # สร้างชื่อไฟล์ unique
        timestamp = datetime.now(THAILAND_TZ).strftime('%Y%m%d_%H%M%S')
        filename = f"{user_id}_{timestamp}_{message_id}.jpg"
        
        # อัพโหลดไปยัง Supabase Storage
        from supabase import create_client
        supabase = create_client(supabase_url, supabase_key)
        
        bucket_name = 'fire_images'
        
        # ตรวจสอบว่า bucket มีอยู่จริงหรือไม่
        try:
            buckets = supabase.storage.list_buckets()
            bucket_names = [b['name'] for b in buckets]
            print(f"📦 Available buckets: {bucket_names}")
            
            if bucket_name not in bucket_names:
                print(f"❌ Bucket '{bucket_name}' not found!")
                print(f"💡 Please create bucket '{bucket_name}' in Supabase Storage")
                return None
        except Exception as e:
            print(f"⚠️ Could not list buckets: {e}")
        
        # ลองอัพโหลด
        print(f"📤 Uploading to bucket: {bucket_name}/{filename}")
        response = supabase.storage.from_(bucket_name).upload(
            filename,
            output.getvalue(),
            file_options={"content-type": "image/jpeg", "upsert": "true"}
        )
        
        # สร้าง public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(filename)
        
        print(f"✅ Image uploaded successfully: {public_url}")
        return public_url
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error uploading image to Supabase: {error_msg}")
        
        # แสดง error แบบละเอียด
        if 'Bucket not found' in error_msg:
            print("💡 Hint: Please create 'fire_images' bucket in Supabase Storage")
            print("   1. Go to Supabase Dashboard → Storage")
            print("   2. Create new bucket named 'fire_images'")
            print("   3. Set it as Public bucket")
        
        import traceback
        traceback.print_exc()
        return None


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
            import requests
            waqi_token = os.getenv('WAQI_API_TOKEN', '6e19dc4d73747ab27c397b590fdbd504f1f496fc')
            waqi_url = f'https://api.waqi.info/feed/@9696/?token={waqi_token}'
            response = requests.get(waqi_url, timeout=5)
            data = response.json()
            if data.get('status') == 'ok':
                pm25_value = data['data']['iaqi']['pm25']['v']
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
                "✅ บันทึกสำเร็จ!\n\n"
                "━━━━━━━━━━━━━━━━\n\n"
                "ขอบคุณสำหรับข้อมูล\n"
                "ระบบได้บันทึกจุดไฟไหม้\n"
                "ลงแผนที่เรียบร้อยแล้ว\n\n"
                f"📍 พิกัด:\n"
                f"{session['latitude']:.6f}, {session['longitude']:.6f}\n\n"
                f"🕐 เวลา: {datetime.now(THAILAND_TZ).strftime('%d/%m/%Y %H:%M น.')}\n\n"
                "━━━━━━━━━━━━━━━━\n\n"
                "📍 ดูแผนที่:\n"
                "https://project-pm25-1.onrender.com"
            )
            
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=reply_text)
            )
            
            print(f"✅ Fire report saved: {report.get('id')}")
        else:
            reply_text = (
                "❌ เกิดข้อผิดพลาด\n\n"
                "ไม่สามารถบันทึกข้อมูลได้\n"
                "กรุณาลองใหม่อีกครั้ง"
            )
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=reply_text)
            )
    
    except Exception as e:
        print(f"❌ Error saving fire report: {e}")
        import traceback
        traceback.print_exc()
        
        reply_text = (
            "❌ เกิดข้อผิดพลาด\n\n"
            "ไม่สามารถบันทึกข้อมูลได้\n"
            "กรุณาลองใหม่อีกครั้ง"
        )
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=reply_text)
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
                # สร้าง Quick Reply Buttons
                quick_reply = QuickReply(items=[
                    QuickReplyButton(action=MessageAction(label="💨 ตรวจสอบค่าฝุ่น", text="ฝุ่น")),
                    QuickReplyButton(action=MessageAction(label="📋 คำสั่งทั้งหมด", text="help")),
                    QuickReplyButton(action=URIAction(label="📍 ดูแผนที่", uri="https://project-pm25-1.onrender.com"))
                ])
                
                reply_text = (
                    "� สวัสดีครับ!\n"
                    "ยินดีต้อนรับสู่ พญานาคเฝ้าฟ้า\n"
                    "ระบบเฝ้าระวังคุณภาพอากาศ\n\n"
                    "━━━━━━━━━━━━━━━━\n\n"
                    "� คำสั่งที่ใช้ได้:\n\n"
                    "💨 ตรวจสอบค่าฝุ่น\n"
                    "   → พิมพ์ 'ฝุ่น' หรือ 'pm25'\n\n"
                    "🔥 แจ้งเหตุไฟไหม้\n"
                    "   → ส่งรูป + พิกัด\n\n"
                    "📍 ดูแผนที่จุดไฟไหม้\n"
                    "   → https://project-pm25-1.onrender.com\n\n"
                    "━━━━━━━━━━━━━━━━\n\n"
                    "👇 เลือกคำสั่งด้านล่าง"
                )
                
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text, quick_reply=quick_reply)
                )
            
            elif text.lower() in ['ฝุ่น', 'pm25', 'pm2.5', 'aqi']:
                # ดึงค่า PM2.5 แบบ real-time จาก WAQI API (เหมือนเว็บ)
                try:
                    import requests
                    waqi_token = os.getenv('WAQI_API_TOKEN', '6e19dc4d73747ab27c397b590fdbd504f1f496fc')
                    keyword = 'nakhon phanom'
                    
                    # 1. ค้นหาสถานี
                    search_url = f'https://api.waqi.info/search/?token={waqi_token}&keyword={keyword}'
                    search_res = requests.get(search_url, timeout=10)
                    search_data = search_res.json()
                    
                    if search_data.get('status') == 'ok' and search_data.get('data'):
                        station_uid = search_data['data'][0]['uid']
                        
                        # 2. ดึงข้อมูลจากสถานี
                        feed_url = f'https://api.waqi.info/feed/@{station_uid}/?token={waqi_token}'
                        feed_res = requests.get(feed_url, timeout=10)
                        data = feed_res.json()
                        
                        if data.get('status') == 'ok':
                            pm25 = data['data']['iaqi']['pm25']['v']
                            aqi = data['data']['aqi']
                            city = data['data']['city']['name']
                            time = data['data']['time']['s']
                            
                            # คำนวณระดับ
                            if pm25 <= 15.0:
                                level = 'ดีมาก 😊'
                                color = '🟦'
                            elif pm25 <= 25.0:
                                level = 'ดี 🙂'
                                color = '🟩'
                            elif pm25 <= 37.5:
                                level = 'ปานกลาง 😐'
                                color = '🟨'
                            elif pm25 <= 75.0:
                                level = 'เริ่มมีผลกระทบ 😷'
                                color = '🟧'
                            else:
                                level = 'มีผลกระทบต่อสุขภาพ ⚠️'
                                color = '🟥'
                            
                            reply_text = (
                                f"💨 ค่าฝุ่น PM2.5 ปัจจุบัน\n\n"
                                f"📍 สถานี: {city}\n"
                                f"📊 PM2.5: {pm25} µg/m³\n"
                                f"🎨 AQI: {aqi}\n"
                                f"{color} ระดับ: {level}\n"
                                f"🕐 อัปเดต: {time}\n\n"
                                f"ดูข้อมูลเพิ่มเติม:\nhttps://project-pm25-1.onrender.com"
                            )
                        else:
                            reply_text = "ไม่สามารถดึงข้อมูลค่าฝุ่นได้ในขณะนี้"
                    else:
                        reply_text = "ไม่พบสถานีตรวจวัดในนครพนม"
                except Exception as e:
                    print(f"❌ Error fetching PM2.5: {e}")
                    reply_text = "เกิดข้อผิดพลาดในการดึงข้อมูล กรุณาลองใหม่อีกครั้ง"
                
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
            
            elif text.lower() in ['ช่วยเหลือ', 'help', 'คำสั่ง', 'เมนู', 'menu']:
                reply_text = (
                    "📋 คำสั่งทั้งหมด\n\n"
                    "━━━━━━━━━━━━━━━━\n\n"
                    "💨 ตรวจสอบค่าฝุ่น\n"
                    "   พิมพ์: ฝุ่น, pm25, aqi\n\n"
                    "� แจ้งเหตุไฟไหม้\n"
                    "   1. ส่งรูปภาพ\n"
                    "   2. ส่งพิกัด (Location)\n\n"
                    "📍 ดูแผนที่\n"
                    "   https://project-pm25-1.onrender.com\n\n"
                    "━━━━━━━━━━━━━━━━\n\n"
                    "💡 พิมพ์ 'สวัสดี' เพื่อเริ่มต้น"
                )
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
            
            else:
                # ข้อความทั่วไป
                reply_text = (
                    "💬 ขอบคุณสำหรับข้อความครับ\n\n"
                    "━━━━━━━━━━━━━━━━\n\n"
                    "📋 คำสั่งที่ใช้ได้:\n\n"
                    "💨 ตรวจสอบค่าฝุ่น\n"
                    "   → พิมพ์ 'ฝุ่น'\n\n"
                    "🔥 แจ้งเหตุไฟไหม้\n"
                    "   → ส่งรูป + พิกัด\n\n"
                    "❓ ดูคำสั่งทั้งหมด\n"
                    "   → พิมพ์ 'help'"
                )
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
        
        except Exception as e:
            print(f"❌ Error handling text message: {e}")

    @handler.add(MessageEvent, message=ImageMessage)
    def handle_image_message(event):
        """จัดการรูปภาพ - ดาวน์โหลดและอัพโหลดไปยัง Supabase"""
        user_id = event.source.user_id
        message_id = event.message.id
        
        try:
            # ดาวน์โหลดรูปภาพจาก LINE
            message_content = line_bot_api.get_message_content(message_id)
            
            # อัพโหลดไปยัง Supabase Storage (resize เป็น 768px)
            image_url = upload_image_to_supabase(message_content, user_id, message_id)
            
            if not image_url:
                # ถ้าอัพโหลดล้มเหลว ใช้ LINE URL แทน (แต่จะหมดอายุ)
                image_url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
                print("⚠️ Using LINE URL as fallback (will expire)")
            
            # ดึง session ปัจจุบัน
            session = db.get_or_create_session(user_id)
            
            if not session:
                reply_text = (
                    "❌ เกิดข้อผิดพลาด\n\n"
                    "กรุณาลองใหม่อีกครั้ง\n"
                    "หรือพิมพ์ 'help' เพื่อดูวิธีใช้งาน"
                )
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
                return
            
            # อัปเดต session ด้วยรูปภาพ (ใช้ Supabase URL)
            db.update_session_image(
                session_id=session['id'],
                image_url=image_url,
                image_message_id=message_id
            )
            
            # ดึง session ใหม่เพื่อให้ได้ค่าที่อัปเดตแล้ว
            session = db.get_or_create_session(user_id)
            
            # ตรวจสอบว่ามีพิกัดแล้วหรือยัง
            if session.get('has_location'):
                # มีครบแล้ว! บันทึกรายงาน
                save_fire_report_from_session(user_id, session, event.reply_token)
            else:
                # ยังไม่มีพิกัด
                reply_text = (
                    "✅ ได้รับรูปภาพแล้ว\n\n"
                    "━━━━━━━━━━━━━━━━\n\n"
                    "📍 ขั้นตอนต่อไป:\n"
                    "ส่งพิกัดสถานที่ของจุดไฟไหม้\n\n"
                    "วิธีส่งพิกัด:\n"
                    "1. กดปุ่ม + ด้านล่าง\n"
                    "2. เลือก Location\n"
                    "3. แชร์ตำแหน่งปัจจุบัน"
                )
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
        
        except Exception as e:
            print(f"❌ Error handling image: {e}")
            import traceback
            traceback.print_exc()
            
            reply_text = (
                "❌ เกิดข้อผิดพลาด\n\n"
                "ไม่สามารถรับรูปภาพได้\n"
                "กรุณาลองใหม่อีกครั้ง"
            )
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
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
                reply_text = (
                    "❌ เกิดข้อผิดพลาด\n\n"
                    "กรุณาลองใหม่อีกครั้ง\n"
                    "หรือพิมพ์ 'help' เพื่อดูวิธีใช้งาน"
                )
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
                return
            
            # อัปเดต session ด้วยพิกัด
            db.update_session_location(
                session_id=session['id'],
                latitude=latitude,
                longitude=longitude
            )
            
            # ดึง session ใหม่เพื่อให้ได้ค่า latitude/longitude ที่อัปเดตแล้ว
            session = db.get_or_create_session(user_id)
            
            # ตรวจสอบว่ามีรูปแล้วหรือยัง
            if session.get('has_image'):
                # มีครบแล้ว! บันทึกรายงาน
                save_fire_report_from_session(user_id, session, event.reply_token, address)
            else:
                # ยังไม่มีรูป
                reply_text = (
                    "✅ ได้รับพิกัดแล้ว\n\n"
                    "━━━━━━━━━━━━━━━━\n\n"
                    "📷 ขั้นตอนต่อไป:\n"
                    "ส่งรูปภาพจุดไฟไหม้/ควัน"
                )
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
        
        except Exception as e:
            print(f"❌ Error handling location: {e}")
            import traceback
            traceback.print_exc()
            
            reply_text = (
                "❌ เกิดข้อผิดพลาด\n\n"
                "ไม่สามารถรับพิกัดได้\n"
                "กรุณาลองใหม่อีกครั้ง"
            )
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
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
