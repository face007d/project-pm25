# Codex Handoff: PM2.5 Colab / Paper Model Work

ไฟล์นี้ใช้สำหรับย้าย context ไปคุยต่อในแอป Codex ในเครื่อง

## สถานะล่าสุด

- โปรเจกต์อยู่ที่ `D:\project จบ`
- Dataset หลักอยู่ที่ `data/processed/pm25_training_dataset_5stations_2020-2026.xlsx`
- ไฟล์เดิมอ่านใน Colab ด้วย `openpyxl` ไม่ได้ เพราะโครงสร้าง zip ภายในใช้ backslash
- แก้แล้วเป็นไฟล์:
  - `data/processed/pm25_training_dataset_5stations_2020-2026_openpyxl.xlsx`
- อัปไฟล์ fixed ขึ้น Google Drive แล้ว:
  - Drive file id: `1y1r8qK_1kulKOsITQSGjfBEj-PXXjPX3`
  - ชื่อไฟล์: `pm25_training_dataset_5stations_2020-2026_FIXED_OPENPYXL`

## Notebook

- Notebook สำหรับ Colab:
  - `notebooks/UPLOAD_THIS_TO_COLAB_pm25_st_had_colab.ipynb`
- Notebook แบ่งเป็น 49 cells:
  - 25 markdown cells
  - 24 code cells
- งานหลักคือ next-day numeric PM2.5 forecasting: ใช้ lookback 72 ชั่วโมงเพื่อทำนาย PM2.5 อีก 24 ชั่วโมงข้างหน้า ไม่ใช่ anomaly classification
- ค่า 95% ต้องรายงานแบบมี tolerance เช่น accuracy ภายใน +/-10 หรือ +/-20 ug/m3 ไม่ควรเรียกเป็น accuracy เฉย ๆ
- ใช้เทรนและเปรียบเทียบหลายโมเดล:
  - `Persistence_last_value`
  - `Ridge_last_hour_spatial`
  - `Ridge_lag_rolling_spatial_v2`
  - `HistGradientBoosting_last_hour_spatial`
  - `HistGradientBoosting_lag_rolling_spatial_v2`
  - `ExtraTrees_lag_rolling_spatial_v2`
  - `LSTM_temporal`
  - `GRU_temporal`
  - `BiLSTM_temporal`
  - `CNN_LSTM_temporal`
  - `Attention_BiLSTM_temporal`
  - `Proposed_ST_Attention_BiLSTM`
  - `SimpleAverage_top3`
  - `WeightedEnsemble_top3`
- เพิ่ม section `5.1 Optional NASA FIRMS hotspot and wind-distance features`
  - ใส่ `RUN_NASA_FIRMS_HOTSPOT_FEATURES = True`
  - ใส่ `FIRMS_MAP_KEY`
  - ระบบจะสร้าง fire features เช่น hotspot count, FRP, nearest distance และ upwind hotspot ตามทิศทางลม
- เพิ่ม section `10.3 Next-day forecast accuracy target`
  - วัดเปอร์เซ็นต์คำทำนายที่คลาดเคลื่อนไม่เกิน +/-5, +/-10, +/-15, +/-20, +/-25, +/-30 ug/m3
  - สร้างกราฟเทียบ forecast accuracy กับเส้นเป้า 95%
- เพิ่ม section `12.1 Optional paper-style residual detector appendix`
  - ถอดเทคนิคจาก IEEE BigData 2025: normal training ด้วย 3-sigma, MinMax normalization, sliding window 20 ชั่วโมง, BiLSTM + temporal attention, stacked LSTM decoder
  - ใช้เป็นภาคเสริม residual diagnostics หลังการ forecast ไม่ใช่ตัวชี้วัดหลักของงาน
  - ค่าเริ่มต้นปิดไว้ด้วย `RUN_PAPER_STYLE_ANOMALY_DETECTOR = False`

## Colab ตอนนี้

รัน cell force fix แล้วสำเร็จ:

- `Has xl/workbook.xml? True`
- `Air4Thai train rows: 8541`
- `Open-Meteo/CAMS model rows: 169045`
- สถานี 5 จังหวัด:
  - นครพนม `88t`
  - บึงกาฬ `106t`
  - หนองคาย `82t`
  - อุบลราชธานี `83t`
  - มุกดาหาร `102t`

ตัวแปรที่ถูกโหลดใน Colab แล้ว:

- `book`
- `obs_raw`
- `model_raw`
- `stations`
- `quality`
- `sources`

ดังนั้นใน Colab ให้ข้าม cell 3 เดิม แล้วรันต่อที่:

```text
4. Cleaning and feature engineering
```

ถ้า cell ดาวน์โหลดไฟล์ขึ้น `HttpError 404 File not found` แปลว่า Google account ใน Colab มองไม่เห็น Drive file id นั้น ให้ใช้ fallback ใน notebook ตัวล่าสุดแล้วอัปโหลดไฟล์จากเครื่องเอง:

```text
D:\project จบ\data\processed\pm25_training_dataset_5stations_2020-2026.xlsx
```

หลังอัปโหลดสำเร็จ cell ถัดไปจะอ่านไฟล์จาก `/content/pm25_training_dataset_5stations_2020-2026.xlsx`

## เหตุผลของข้อมูล

- `train_ready_pm25`: ค่าจากสถานี Air4Thai จริง ใช้ calibration/validation
- `model_ready_openmeteo_aq`: ข้อมูล Open-Meteo/CAMS แบบ gridded/model ใช้เรียนรู้ pattern ย้อนหลังหลายปี
- ไม่ใช่ mock data แต่ต้องเขียนใน paper ให้ชัดว่า Open-Meteo/CAMS ไม่ใช่ station observation โดยตรง

## Output ที่ต้องดูหลังรัน Colab

- `model_comparison_overall.csv`
- `model_comparison_by_station.csv`
- `best_model_summary.json`
- `model_training_log.csv`
- `next_day_forecast_accuracy/next_day_forecast_accuracy_by_model.csv`
- `next_day_forecast_accuracy/next_day_forecast_accuracy_by_tolerance.csv`
- `next_day_forecast_accuracy/next_day_forecast_accuracy_summary.json`
- `ridge_v2/ridge_lag_rolling_spatial_v2.pkl`
- `ridge_v2/hist_gradient_boosting_lag_rolling_spatial_v2.pkl`
- `ridge_v2/extra_trees_lag_rolling_spatial_v2.pkl`
- `ridge_v2/ridge_alpha_validation_search.csv`
- `ridge_v2/ridge_v2_feature_ablation.csv`
- `ridge_v2/tabular_v2_validation_metrics.csv`
- `ridge_v2/ridge_v2_model_comparison.csv`
- `ridge_v2/tabular_v2_model_comparison.csv`
- `ridge_v2/ridge_v2_test_predictions.csv`
- `ridge_v2/tabular_v2_test_predictions.csv`
- `ensemble_validation_rank.csv`
- `ensemble_weights_top3.csv`
- `nasa_fire_feature_status.json`
- `nasa_firms_hotspots_raw.csv`
- `nasa_firms_hotspots_prepared.csv`
- `nasa_fire_features_by_station_hour.csv`
- `figures/model_comparison_metrics.png`
- `figures/model_station_rmse_heatmap.png`
- `figures/ensemble_weights_top3.png`
- `figures/best_model_true_vs_predicted.png`
- `figures/next_day_forecast_accuracy_by_tolerance.png`
- `figures/next_day_forecast_accuracy_within_10ug.png`
- `figures/next_day_forecast_accuracy_within_20ug.png`
- `figures/nasa_firms_hotspot_map.png`
- `air4thai_calibration_metrics_by_station.csv`
- `air4thai_high_error_residual_candidates.csv`
- `pm25_training_outputs.zip`

## Prompt สำหรับเริ่มคุยต่อใน Codex

เปิด Codex ในเครื่อง แล้วพิมพ์:

```text
อ่าน docs/project/CODEX_HANDOFF_COLAB_PM25_TH.md แล้วช่วยพาฉันทำงาน PM2.5 Colab/paper model ต่อจากสถานะล่าสุด
```
