from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import joblib
import os
from tensorflow.keras.models import load_model

app = Flask(__name__)
CORS(app)  # เพื่อให้ HTML เรียก API ได้โดยไม่ติดปัญหาความปลอดภัย

# 1. โหลดโมเดลและ Scaler (ตรวจสอบชื่อไฟล์ให้ตรงกับที่โหลดมา)
# หา path ของไฟล์ปัจจุบัน
base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, 'lstm_pm25_model (2).h5')
scaler_path = os.path.join(base_dir, 'scaler (2).pkl')

model = None
scaler = None

if os.path.exists(model_path) and os.path.exists(scaler_path):
    model = load_model(model_path)
    scaler = joblib.load(scaler_path)
    print("✅ Model and Scaler loaded successfully!")
    print(f"Model path: {model_path}")
else:
    print("❌ Error: Missing model or scaler files!")
    print(f"Looking for model at: {model_path}")
    print(f"Looking for scaler at: {scaler_path}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Files in base_dir: {os.listdir(base_dir) if os.path.exists(base_dir) else 'N/A'}")

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