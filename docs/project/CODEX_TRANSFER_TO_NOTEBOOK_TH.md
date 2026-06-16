# ย้ายงาน Codex ไปทำต่อในโน้ตบุ๊ก

ไฟล์นี้ใช้สำหรับย้ายบริบทงานจาก Codex เครื่องนี้ ไปเปิดต่อในโน้ตบุ๊กหรือเครื่องอื่น

## สิ่งที่ต้องเข้าใจก่อน

ข้อมูลในภาพฝั่งซ้ายของ Codex มี 2 แบบ:

1. ไฟล์โปรเจกต์จริง เช่น notebook, scripts, results, docs
2. ประวัติแชทใน Codex

สิ่งที่ควรย้ายข้ามเครื่องจริง ๆ คือไฟล์โปรเจกต์ และไฟล์สรุปบริบทนี้ ส่วนประวัติแชทไม่ควรใช้เป็นแหล่งหลัก เพราะเปิดข้ามเครื่องแล้วอาจไม่ครบหรือไม่สะดวกเท่าไฟล์ handoff

## วิธีที่แนะนำที่สุด

ใช้ 2 ที่เก็บคู่กัน:

- GitHub private repo: เก็บโค้ด, notebook, docs, README, ตารางผลลัพธ์เล็ก ๆ
- Google Drive: เก็บ dataset ใหญ่, model ใหญ่, zip outputs, NASA hotspot raw files

โครงสร้างที่ควรมีในโน้ตบุ๊ก:

```text
project จบ/
├── docs/
│   └── project/
│       ├── CODEX_TRANSFER_TO_NOTEBOOK_TH.md
│       └── CODEX_HANDOFF_COLAB_PM25_TH.md
├── notebooks/
│   └── UPLOAD_THIS_TO_COLAB_pm25_nextday_clean_nasa.ipynb
├── scripts/
│   └── create_pm25_clean_colab_notebook.js
├── outputs/
│   ├── pm25_nextday_clean_results/
│   ├── pm25_nextday_with_epochs_results/
│   └── pm25_nextday_nasa_results/
└── data/
    └── processed/
        └── pm25_training_dataset_5stations_2020-2026_openpyxl.xlsx
```

## ไฟล์สำคัญของงานล่าสุด

Dataset ที่ถูกต้อง:

```text
data/processed/pm25_training_dataset_5stations_2020-2026_openpyxl.xlsx
```

Notebook สำหรับ Colab:

```text
notebooks/UPLOAD_THIS_TO_COLAB_pm25_nextday_clean_nasa.ipynb
```

ผลลัพธ์รอบไม่มี NASA:

```text
outputs/pm25_nextday_clean_results/
```

ผลลัพธ์รอบ deep learning พร้อม epoch:

```text
outputs/pm25_nextday_with_epochs_results/
```

ผลลัพธ์รอบ NASA hotspot + wind-distance:

```text
outputs/pm25_nextday_nasa_results/
```

## สถานะโมเดลล่าสุด

งานนี้คือ PM2.5 next-day numeric forecasting ไม่ใช่ anomaly classification

จังหวัด/สถานีที่ใช้:

- นครพนม: `88t`
- บึงกาฬ: `106t`
- หนองคาย: `82t`
- อุบลราชธานี: `83t`
- มุกดาหาร: `102t`

โมเดลที่ดีที่สุดตอนนี้:

```text
Ridge_lag_rolling_spatial
```

ผลรอบแรกก่อนเพิ่ม NASA:

- MAE: 7.7053
- RMSE: 11.7810
- R2: 0.7481
- within +/-20 ug/m3: 93.49%
- within +/-25 ug/m3: 96.03%

ผลรอบเพิ่ม NASA hotspot + wind-distance:

- MAE: 7.5939
- RMSE: 11.8465
- R2: 0.7453
- within +/-20 ug/m3: 93.61%
- within +/-25 ug/m3: 96.08%

สรุปสั้น ๆ:

- NASA ใช้งานได้จริง และมี hotspot rows ประมาณ 2,444,014 rows
- NASA ช่วย MAE และ tolerance เล็กน้อย
- NASA ยังไม่พอให้ within +/-20 ug/m3 ไปถึง 95%
- Ridge ยังเป็นตัวหลักที่ควรใช้เป็น final model ตอนนี้
- CNN-LSTM เป็น deep learning ตัวเปรียบเทียบที่ดีที่สุด แต่ยังแพ้ Ridge

## สิ่งที่ไม่ควรเอาขึ้น GitHub

อย่า commit ไฟล์พวกนี้:

- NASA API key
- `.env`
- dataset ใหญ่ `.xlsx`
- raw NASA hotspot `.csv`
- model ใหญ่ `.h5`, `.pkl`, `.joblib`
- zip output ใหญ่
- โฟลเดอร์ `sample_data`

ให้เก็บไฟล์ใหญ่ไว้ Google Drive แทน

## วิธีเปิดต่อในโน้ตบุ๊ก

1. เปิด Codex ในโน้ตบุ๊ก
2. Login account เดียวกับเครื่องนี้
3. เปิด folder โปรเจกต์ `project จบ`
4. ให้ Codex อ่านไฟล์นี้ก่อน
5. ส่ง prompt นี้:

```text
อ่าน docs/project/CODEX_TRANSFER_TO_NOTEBOOK_TH.md แล้วช่วยทำงาน PM2.5 ต่อจากสถานะล่าสุด โดยโฟกัสที่ model ก่อน paper
```

ถ้าจะให้ทำ Colab ต่อ ให้ส่งเพิ่ม:

```text
ใช้ notebooks/UPLOAD_THIS_TO_COLAB_pm25_nextday_clean_nasa.ipynb เป็น notebook หลัก และอธิบายขั้นตอนรันทีละ cell แบบไม่สับสน
```

## แผนต่อจากนี้

สิ่งที่ควรทำถัดไป:

1. ทำ ablation table เทียบ Ridge ก่อน NASA กับ Ridge หลัง NASA
2. ลองปรับโมเดล tabular เพิ่ม เช่น Ridge alpha search, ElasticNet, LightGBM/XGBoost/CatBoost ถ้า Colab รองรับ
3. ดูผลรายจังหวัด เพื่อหาจังหวัดที่พลาดหนัก
4. เพิ่ม station-specific calibration เฉพาะจังหวัดที่ error สูง
5. ตั้งเป้ารายงานผลเป็น tolerance accuracy เช่น within +/-20 ug/m3 ไม่ใช่ accuracy เฉย ๆ

