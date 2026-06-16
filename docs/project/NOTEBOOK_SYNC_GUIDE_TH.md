# คู่มือเชื่อมงานระหว่าง PC, GitHub, Google Drive และโน้ตบุ๊ก

เป้าหมายคือให้เปิดงาน PM2.5 ต่อในโน้ตบุ๊กได้ โดยไม่ต้องไล่แชทเก่า และไม่เผลออัปไฟล์ใหญ่ขึ้น GitHub

## สรุปวิธีเชื่อม

ใช้ 2 ทางพร้อมกัน:

- GitHub: เก็บไฟล์เบา เช่น notebook, script, docs, ตารางผลลัพธ์, กราฟ
- Google Drive: เก็บไฟล์ใหญ่ เช่น Excel dataset, model, ZIP output, NASA raw hotspot

ภาพรวม:

```text
PC เครื่องนี้
  ├─ GitHub: code/notebook/docs/results เล็ก
  └─ Google Drive: dataset/model/output ใหญ่

โน้ตบุ๊ก
  ├─ clone/pull จาก GitHub
  └─ เปิด Google Drive folder เดียวกันเพื่อใช้ dataset ใหญ่
```

## ไฟล์ที่ควรขึ้น GitHub

ควรขึ้น:

```text
docs/project/CODEX_TRANSFER_TO_NOTEBOOK_TH.md
docs/project/NOTEBOOK_SYNC_GUIDE_TH.md
docs/project/CODEX_HANDOFF_COLAB_PM25_TH.md
data/README.md
notebooks/UPLOAD_THIS_TO_COLAB_pm25_nextday_clean_nasa.ipynb
scripts/create_pm25_clean_colab_notebook.js
outputs/pm25_nextday_clean_results/
outputs/pm25_nextday_with_epochs_results/
outputs/pm25_nextday_nasa_results/
```

ไม่ควรขึ้น:

```text
data/processed/*.xlsx
models/
*.h5
*.pkl
*.joblib
*_outputs*.zip
outputs/**/nasa_firms_hotspots_raw.csv
outputs/**/nasa_firms_hotspots_prepared.csv
outputs/**/nasa_fire_features_by_station_hour.csv
.env
```

## ไฟล์ใหญ่ที่ต้องเอาไปไว้ Google Drive

เอาไฟล์นี้ไปไว้ใน Drive:

```text
data/processed/pm25_training_dataset_5stations_2020-2026_openpyxl.xlsx
```

แนะนำ path ใน Google Drive:

```text
My Drive/pm25_project/data/pm25_training_dataset_5stations_2020-2026_openpyxl.xlsx
```

ถ้าจะเก็บ output ใหญ่จาก Colab:

```text
My Drive/pm25_project/outputs/
```

## ขั้นตอนบนโน้ตบุ๊ก

1. เปิด Codex ในโน้ตบุ๊ก
2. เปิด folder โปรเจกต์ที่ clone จาก GitHub
3. เปิดไฟล์นี้ก่อน:

```text
docs/project/CODEX_TRANSFER_TO_NOTEBOOK_TH.md
```

4. ส่งข้อความให้ Codex:

```text
อ่าน docs/project/CODEX_TRANSFER_TO_NOTEBOOK_TH.md และ docs/project/NOTEBOOK_SYNC_GUIDE_TH.md แล้วช่วยทำงาน PM2.5 ต่อจากสถานะล่าสุด โดยโฟกัส model ก่อน paper
```

## คำสั่ง Git ที่ใช้บนโน้ตบุ๊ก

ถ้าเป็นครั้งแรก:

```bash
git clone https://github.com/face007d/project-pm25.git
```

ถ้ามี repo อยู่แล้ว:

```bash
git pull
```

## สถานะงานล่าสุดที่ต้องจำ

งานนี้คือการทำนาย PM2.5 วันพรุ่งนี้แบบตัวเลข ไม่ใช่ classification

โมเดลหลักตอนนี้:

```text
Ridge_lag_rolling_spatial
```

ผลก่อนเพิ่ม NASA:

- within +/-20 ug/m3: 93.49%
- within +/-25 ug/m3: 96.03%

ผลหลังเพิ่ม NASA hotspot + wind-distance:

- within +/-20 ug/m3: 93.61%
- within +/-25 ug/m3: 96.08%

NASA ช่วยเล็กน้อย แต่ยังไม่พอให้ +/-20 ไปถึง 95%

