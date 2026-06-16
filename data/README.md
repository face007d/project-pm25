# PM2.5 Training Dataset

ไฟล์หลัก:

- `processed/pm25_training_dataset_5stations_2020-2026.xlsx`

ช่วงข้อมูล:

- `2020-06-13 00:00:00` ถึง `2026-06-12 23:00:00`
- 5 สถานีตามรูป: นครพนม, บึงกาฬ, หนองคาย, อุบลราชธานี, มุกดาหาร

## Sheets

- `train_ready_pm25` - ข้อมูล PM2.5 จาก Air4Thai เฉพาะแถวที่มีค่าจริงจากสถานี เหมาะกับการ train จากค่าที่วัดจริง
- `model_ready_openmeteo_aq` - ข้อมูลมลพิษจาก Open-Meteo Air Quality/CAMS global พร้อม weather เหมาะกับการ train ชุดยาวกว่าเมื่อรับได้ว่าเป็นข้อมูลแบบ gridded model
- `dataset_full_6y` - ตารางรายชั่วโมงเต็ม 6 ปีของทุกสถานี มี weather ครบ แต่ pollutant จาก Air4Thai จะว่างในช่วงที่ API ไม่มีข้อมูล
- `stations` - รายชื่อสถานีและพิกัด
- `data_quality` - จำนวนแถวและ coverage ของแต่ละตัวแปร
- `sources` - แหล่งข้อมูลและหมายเหตุ

## Notes

- Air4Thai history endpoint ให้ข้อมูลย้อนหลังของสถานีกลุ่มนี้ได้จำกัด ไม่ครบ 6 ปี
- Open-Meteo Air Quality เป็นข้อมูลแบบ gridded model ไม่ใช่ค่าจากสถานีวัดโดยตรง และ global air quality availability เริ่มช่วงปี 2022 เป็นต้นไป
- Weather ใช้ Open-Meteo Historical Weather API เพื่อให้ได้ข้อมูลรายชั่วโมงต่อเนื่องครบกรอบ 6 ปี

## แหล่งอ้างอิงและค่าใช้จ่าย

- Air4Thai / กรมควบคุมมลพิษ
  - ใช้สำหรับข้อมูลที่วัดจากสถานีจริงใน sheet `train_ready_pm25`
  - หน้าเว็บอ้างอิง: https://air4thai.pcd.go.th/webV3/#/History
  - Endpoint ที่ใช้ดึงข้อมูล: http://air4thai.com/forweb/getHistoryData.php
  - ไม่มีค่าใช้จ่ายตอนดึงข้อมูลชุดนี้ และไม่ต้องใช้ API key

- Open-Meteo Historical Weather API
  - ใช้สำหรับ weather variables เช่น อุณหภูมิ ความชื้น ความกดอากาศ ฝน ความเร็วลม และทิศทางลม
  - เอกสารอ้างอิง: https://open-meteo.com/en/docs/historical-weather-api
  - ไม่มีค่าใช้จ่ายตอนดึงข้อมูลชุดนี้ผ่าน free/open-access API แต่ควรให้ attribution ตามเงื่อนไขของ Open-Meteo

- Open-Meteo Air Quality API / CAMS global
  - ใช้สำหรับ sheet `model_ready_openmeteo_aq`
  - เป็นข้อมูลแบบ gridded/model ไม่ใช่ค่าที่วัดจากสถานี Air4Thai โดยตรง
  - เอกสารอ้างอิง: https://open-meteo.com/en/docs/air-quality-api
  - ไม่มีค่าใช้จ่ายตอนดึงข้อมูลชุดนี้ผ่าน free/open-access API แต่ถ้าใช้เชิงพาณิชย์หรือปริมาณสูงควรตรวจ plan ของ Open-Meteo
