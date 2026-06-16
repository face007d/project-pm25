# แผนเทรนโมเดลใน Colab จากโจทย์ PDF

ไฟล์หลัก:

- `notebooks/pm25_st_had_colab.ipynb`
- ใช้ Google Sheet: `pm25_training_dataset_5stations_2020-2026`

## แนวคิดหลัก

งานหลักไม่ใช่ anomaly classification แต่เป็นการทำนายค่า PM2.5 ล่วงหน้า 24 ชั่วโมง/วันพรุ่งนี้แบบ numeric forecasting ในบริบทหมอกควัน/มลพิษข้ามแดน ดังนั้นตัวชี้วัดหลักต้องเป็น RMSE, MAE, R2 และ forecast accuracy แบบมี error tolerance เช่น คลาดเคลื่อนไม่เกิน +/-10 หรือ +/-20 ug/m3

แนวทางที่ใช้ใน notebook:

1. ใช้ `model_ready_openmeteo_aq` เพื่อให้โมเดลเรียนรู้ pattern ระยะยาวจากข้อมูลย้อนหลังหลายปี
2. สร้างกราฟ 5 สถานีจากพิกัดจริง โดยใช้ระยะทางระหว่างสถานีเป็น adjacency matrix
3. เทรนและเปรียบเทียบหลายโมเดลด้วย lookback 72 ชั่วโมง เพื่อทำนาย PM2.5 อีก 24 ชั่วโมงข้างหน้า
4. เลือกโมเดลที่ดีที่สุดจาก test set ตาม RMSE/MAE/R2 และเก็บตารางเปรียบเทียบไว้ใช้ใน paper
5. ใช้ `train_ready_pm25` จาก Air4Thai เพื่อ calibrate ให้ผลทำนายเข้าใกล้ค่าที่สถานีวัดจริง
6. รายงาน next-day forecast accuracy ว่ากี่เปอร์เซ็นต์ของคำทำนายคลาดเคลื่อนไม่เกิน tolerance ที่กำหนด
7. ใช้ residual error หลัง calibration เป็น diagnostic เพื่อดูเคสที่ทำนายพลาดมาก ไม่ใช่เป้าหมายหลัก
8. export โมเดล, scaler, metrics, validation predictions, forecast accuracy, figures และไฟล์ compatibility สำหรับ backend เดิม

## โมเดลที่ใช้เปรียบเทียบ

- `Persistence_last_value`: baseline ง่ายสุด ใช้ค่าล่าสุดทำนายอนาคต
- `Ridge_last_hour_spatial`: linear/tabular baseline
- `Ridge_lag_rolling_spatial_v2`: Ridge ที่เพิ่ม PM2.5 lag, rolling statistics, spatial context และ target-hour calendar features โดยใช้เฉพาะข้อมูลย้อนหลัง
- `HistGradientBoosting_last_hour_spatial`: tree-based/tabular baseline
- `HistGradientBoosting_lag_rolling_spatial_v2`: tree-based model บนชุด feature lag/rolling/spatial เดียวกับ Ridge v2
- `ExtraTrees_lag_rolling_spatial_v2`: ensemble tree model สำหรับเช็กว่า non-linear feature interaction ช่วยดันผลได้ไหม
- `LSTM_temporal`: deep learning baseline แบบ LSTM
- `GRU_temporal`: deep learning baseline แบบ GRU
- `BiLSTM_temporal`: baseline แบบ bidirectional LSTM
- `CNN_LSTM_temporal`: baseline แบบ convolution + LSTM
- `Attention_BiLSTM_temporal`: ablation model ที่มี attention แต่ยังไม่มี spatial graph
- `Proposed_ST_Attention_BiLSTM`: proposed model ที่ใช้ temporal attention + spatial context จากกราฟ 5 สถานี
- `SimpleAverage_top3`: ensemble เฉลี่ยผลทำนายจาก 3 โมเดลที่ validation RMSE ดีที่สุด
- `WeightedEnsemble_top3`: ensemble ถ่วงน้ำหนักจาก 3 โมเดลที่ validation RMSE ดีที่สุด โดยน้ำหนักมาจาก inverse RMSE

## การแบ่ง cell ใน Colab

Notebook ถูกแบ่งเป็น 49 cells พร้อมหัวข้อ markdown เพื่อให้รันและตรวจผลได้เป็นช่วง:

- configuration และ import
- download/load Google Sheet
- cleaning และ feature engineering
- spatial graph และ tensor preparation
- optional NASA FIRMS hotspot + wind-distance feature engineering
- sequence dataset
- model definitions
- baseline models
- deep learning models
- model ranking และ comparison table
- tabular v2 lag/rolling/spatial feature upgrade พร้อม feature ablation
- visualization สำหรับเปรียบเทียบโมเดล
- Air4Thai calibration
- next-day forecast accuracy target
- forecast residual diagnostics
- optional paper-style residual detector appendix จาก IEEE BigData 2025
- backend-compatible export
- artifact export และ download ZIP

## Sheet ที่ใช้

- `model_ready_openmeteo_aq`: ใช้เป็นข้อมูลหลักสำหรับเรียนรู้ pattern ระยะยาว
- `train_ready_pm25`: ใช้เป็นข้อมูลสถานีจริงสำหรับ calibration และ validation กับ Air4Thai
- `stations`: ใช้พิกัดและ station id เพื่อสร้าง spatial graph
- `data_quality`: ใช้รายงาน coverage ใน paper
- `sources`: ใช้อ้างอิงแหล่งข้อมูล

## NASA FIRMS hotspot features

ถ้าต้องการใช้ข้อมูลจุดไฟไหม้จริง ให้เปิดใน cell configuration:

- `RUN_NASA_FIRMS_HOTSPOT_FEATURES = True`
- ใส่ `FIRMS_MAP_KEY`

MAP_KEY ขอฟรีจาก NASA FIRMS: https://firms.modaps.eosdis.nasa.gov/api/map_key/

features ที่สร้างเพิ่ม:

- `hotspot_count_24h`, `hotspot_count_48h`, `hotspot_count_72h`, `hotspot_count_168h`
- `hotspot_frp_sum_24h`, `hotspot_frp_sum_72h`, `hotspot_frp_sum_168h`
- `nearest_hotspot_distance_km`
- `upwind_hotspot_count_24h`, `upwind_hotspot_count_72h`
- `upwind_frp_weighted_24h`, `upwind_frp_weighted_72h`

## เทคนิคจาก Deep Learning Based Anomaly Detection Approach for Air Pollution Assessment

นำมาใช้เป็นภาคเสริมใน section `12.1 Optional paper-style residual detector appendix` เท่านั้น ไม่ใช่ตัวชี้วัดหลักของงาน เพราะโจทย์เราคือทำนาย PM2.5 วันพรุ่งนี้

- ใช้แนวคิด forecasting-based residual detection: ให้โมเดลทำนายค่าถัดไป แล้วดู prediction error
- ใช้ 3-sigma rule คัด normal training samples
- ใช้ MinMaxScaler
- ใช้ sliding window ขนาด 20 ชั่วโมง
- ใช้ BiLSTM encoder + temporal attention + stacked LSTM decoder
- ใช้ maximum prediction error จาก normal training เป็น threshold เพื่อวิเคราะห์เคสที่พลาดมาก
- ไม่ใช้ accuracy/precision/recall/F1 เป็นคะแนนหลักของงาน forecast

## สิ่งที่ต้องระวังตอนเขียน paper

- Open-Meteo/CAMS ไม่ใช่ mock data แต่เป็น gridded/model data ไม่ใช่ค่าที่วัดจากสถานีโดยตรง
- Air4Thai เป็นค่าจากสถานีจริง แต่ endpoint ที่ใช้ให้ประวัติย้อนหลังได้จำกัด ไม่ครบ 6 ปี
- ห้ามรายงานว่าได้ accuracy 95% แบบลอย ๆ ต้องระบุเสมอว่า 95% นั้นคือ within +/- กี่ ug/m3 หรือ tolerance แบบใด
- NASA VIIRS/FIRMS hotspot ใช้เป็น feature ช่วย forecast และใช้ประกอบเหตุผลด้านไฟไหม้/หมอกควัน ไม่ใช่ label สำหรับ classification
- research model ใน notebook เป็น multi-feature/multi-station ส่วน backend เดิมรับ input แค่ PM2.5 ย้อนหลัง 3 ค่า จึงมี section export model compatibility แยกไว้

## Output จาก Colab

หลังรัน notebook จะได้ไฟล์ ZIP:

- `st_attention_bilstm_pm25_model.h5`
- `st_model_artifacts.pkl`
- `air4thai_calibrator.pkl`
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
- `ridge_v2/ridge_v2_feature_columns.csv`
- `ridge_v2/ridge_v2_feature_ablation.csv`
- `ridge_v2/tabular_v2_validation_metrics.csv`
- `ridge_v2/ridge_v2_model_comparison.csv`
- `ridge_v2/ridge_v2_station_comparison.csv`
- `ridge_v2/tabular_v2_model_comparison.csv`
- `ridge_v2/tabular_v2_station_comparison.csv`
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
- `st_model_test_metrics_by_station.csv`
- `air4thai_calibration_metrics_by_station.csv`
- `air4thai_high_error_residual_candidates.csv`
- `adaptive_thresholds_by_station.csv`
- `paper_method_notes.json`
- `lstm_pm25_model.h5`
- `scaler.pkl`

ไฟล์ `lstm_pm25_model.h5` และ `scaler.pkl` เป็นตัวที่ออกแบบให้ใกล้กับ backend เดิมที่สุด ส่วนโมเดลวิจัยตัวเต็มต้องปรับ backend เพิ่มถ้าจะนำไป deploy จริง
