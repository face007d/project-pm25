from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import joblib
import os
import warnings
from datetime import date, timedelta
warnings.filterwarnings('ignore')

# ปิด TensorFlow logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import tensorflow as tf
from tensorflow import keras

# Import database module
try:
    from database import get_db
    db = get_db()
    DB_AVAILABLE = True
    print("✅ Database module loaded successfully")
except Exception as e:
    print(f"⚠️ Database module not available: {e}")
    DB_AVAILABLE = False

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
        'endpoints': {
            '/predict': 'POST - Predict PM2.5 value',
            '/api/predictions': 'GET - Get recent predictions',
            '/api/readings': 'GET - Get actual readings',
            '/api/stats': 'GET - Get accuracy statistics',
            '/api/save-reading': 'POST - Save actual reading'
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
