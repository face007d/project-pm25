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

app = Flask(__name__)
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
        # แก้ไข model config เพื่อรองรับ Keras ใหม่
        import h5py
        import json
        
        # อ่าน model config และแก้ไข batch_shape -> shape
        with h5py.File(model_path, 'r') as f:
            if 'model_config' in f.attrs:
                config = json.loads(f.attrs['model_config'])
                
                # แก้ไข InputLayer config
                if 'config' in config and 'layers' in config['config']:
                    for layer in config['config']['layers']:
                        if layer.get('class_name') == 'InputLayer':
                            if 'batch_shape' in layer['config']:
                                batch_shape = layer['config'].pop('batch_shape')
                                # แปลง batch_shape เป็น shape (ตัดมิติแรกออก)
                                layer['config']['batch_input_shape'] = batch_shape
        
        # โหลด model ด้วย custom object scope
        from tensorflow.keras.layers import InputLayer
        
        # สร้าง custom InputLayer ที่รองรับ batch_shape
        class CustomInputLayer(InputLayer):
            def __init__(self, batch_shape=None, **kwargs):
                if batch_shape is not None:
                    kwargs['batch_input_shape'] = batch_shape
                super().__init__(**kwargs)
        
        custom_objects = {'InputLayer': CustomInputLayer}
        
        model = keras.models.load_model(
            model_path, 
            custom_objects=custom_objects,
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