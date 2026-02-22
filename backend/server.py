from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

# ปิด TensorFlow logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import tensorflow as tf
from tensorflow import keras

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
        print(f"Model summary: {model.summary()}")
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
    return app.send_static_file('index.html')

@app.route('/api')
def api_status():
    status = "Ready" if model and scaler else "Model Missing"
    return jsonify({
        'status': status,
        'message': 'PM2.5 Nakhon Phanom API',
        'endpoints': {
            '/predict': 'POST - Predict PM2.5 value'
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
        
        return jsonify({'prediction': float(prediction_final[0][0])})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)