# วิธีเปลี่ยนรูป Rich Menu (โดยไม่เปลี่ยนปุ่ม)

## ขั้นตอนที่ 1: เตรียมรูปภาพใหม่

### ขนาดที่ต้องการ
- **กว้าง x สูง**: 2500 x 1686 พิกเซล (ต้องตรงนี้!)
- **ไฟล์**: JPG หรือ PNG
- **ขนาดไฟล์**: < 1 MB

### ตำแหน่งปุ่ม (ต้องวาดให้ตรง!)
```
┌─────────────────────┬──────────────┬─────────────────────┐
│     ปุ่ม 1          │              │     ปุ่ม 2          │
│  ค่าฝุ่น PM2.5      │   (ว่าง)     │  สภาพอากาศ         │
│  x: 0, y: 0         │              │  x: 1667, y: 0      │
│  w: 833, h: 843     │              │  w: 833, h: 843     │
├─────────────────────┼──────────────┼─────────────────────┤
│     ปุ่ม 3          │   ปุ่ม 4     │     ปุ่ม 5          │
│  แจ้งจุดเกิดไฟ     │  เว็บไซต์    │  วิธีแจ้งเหตุ       │
│  x: 0, y: 843       │ x: 833       │  x: 1667, y: 843    │
│  w: 833, h: 843     │ y: 843       │  w: 833, h: 843     │
│                     │ w: 834       │                     │
│                     │ h: 843       │                     │
└─────────────────────┴──────────────┴─────────────────────┘

รวม: 2500 x 1686 พิกเซล
```

### ตัวอย่างการวาด
1. สร้างรูปใหม่ขนาด 2500x1686 px
2. วาดปุ่มตามพิกัดด้านบน
3. ใส่ไอคอนและข้อความในแต่ละปุ่ม
4. บันทึกเป็น JPG หรือ PNG

---

## ขั้นตอนที่ 2: Compress รูปภาพ

```bash
# วิธีที่ 1: ใช้สคริปต์
python compress_new_rich_menu.py new_rich_menu.png

# Output: new_rich_menu_compressed.jpg (< 1 MB)
```

```bash
# วิธีที่ 2: ใช้เว็บไซต์
# ไปที่ https://tinypng.com/ หรือ https://compressor.io/
# อัปโหลดและดาวน์โหลดรูปที่บีบอัดแล้ว
```

---

## ขั้นตอนที่ 3: อัปโหลดรูปใหม่

### วิธีที่ 1: ใช้สคริปต์ (แนะนำ)
```bash
# อัปเดตรูปใหม่ (ปุ่มยังเหมือนเดิม)
python scripts/update_rich_menu_image.py new_rich_menu_compressed.jpg
```

### วิธีที่ 2: สร้าง Rich Menu ใหม่ทั้งหมด
```bash
# 1. สร้าง Rich Menu ใหม่
python scripts/setup_rich_menu_4buttons.py

# 2. คัดลอก Rich Menu ID ที่ได้
# ตัวอย่าง: richmenu-abc123...

# 3. อัปโหลดรูป
python scripts/upload_rich_menu_image_6buttons.py richmenu-abc123... new_rich_menu_compressed.jpg
```

---

## ขั้นตอนที่ 4: ตั้งเป็นค่าเริ่มต้น (ถ้าต้องการ)

```bash
# ให้ Rich Menu แสดงกับทุกคนโดยอัตโนมัติ
python scripts/set_default_rich_menu.py richmenu-abc123...
```

---

## การทดสอบ

1. เปิด LINE แอพ
2. เข้าไปที่ LINE Official Account: Naka Monitor
3. ดู Rich Menu ด้านล่าง
4. ลองกดปุ่มทุกปุ่มเพื่อทดสอบว่ายังทำงานได้

**หมายเหตุ**: อาจต้องรอ 1-2 นาทีจึงจะเห็นการเปลี่ยนแปลง หรือลองปิด-เปิดแอพใหม่

---

## Troubleshooting

### ❌ ปัญหา: รูปขนาดไม่ตรง
```
Error: Image size must be 2500x1686 pixels
```
**แก้**: ใช้โปรแกรมแก้ไขรูปปรับขนาดให้ตรง 2500x1686 px

### ❌ ปัญหา: ไฟล์ใหญ่เกิน 1 MB
```
Error: File size exceeds 1MB
```
**แก้**: รัน `python compress_new_rich_menu.py <รูป>` อีกครั้ง

### ❌ ปัญหา: ปุ่มไม่ตรงที่วาด
**แก้**: ตรวจสอบพิกัดปุ่มให้ตรงกับที่กำหนด (ดูด้านบน)

### ❌ ปัญหา: Rich Menu ไม่เปลี่ยน
**แก้**: 
1. รอ 1-2 นาที
2. ปิด-เปิด LINE แอพใหม่
3. ลบ Rich Menu เก่าแล้วสร้างใหม่

---

## เครื่องมือออนไลน์ช่วยออกแบบ

### Figma Template
1. ไปที่ https://www.figma.com/
2. สร้าง Frame ขนาด 2500x1686 px
3. วาดปุ่มตามพิกัด
4. Export เป็น JPG

### Canva
1. ไปที่ https://www.canva.com/
2. สร้างรูปแบบ Custom Size: 2500x1686 px
3. ออกแบบ
4. ดาวน์โหลดเป็น JPG

### Photoshop / GIMP
1. สร้างไฟล์ใหม่ 2500x1686 px
2. สร้าง Guides ตามพิกัดปุ่ม
3. ออกแบบ
4. Save for Web (JPG, Quality 80-90%)

---

## ตัวอย่างโค้ดวาดพิกัด (Python + Pillow)

```python
from PIL import Image, ImageDraw, ImageFont

# สร้างรูปพื้นฐาน
img = Image.new('RGB', (2500, 1686), color='white')
draw = ImageDraw.Draw(img)

# วาดเส้นแบ่งปุ่ม (เพื่อดูพิกัด)
# แถวบน
draw.rectangle([0, 0, 833, 843], outline='red', width=5)  # ปุ่ม 1
draw.rectangle([1667, 0, 2500, 843], outline='red', width=5)  # ปุ่ม 2

# แถวล่าง
draw.rectangle([0, 843, 833, 1686], outline='blue', width=5)  # ปุ่ม 3
draw.rectangle([833, 843, 1667, 1686], outline='blue', width=5)  # ปุ่ม 4
draw.rectangle([1667, 843, 2500, 1686], outline='blue', width=5)  # ปุ่ม 5

# บันทึก
img.save('rich_menu_template.png')
print("✅ Template created: rich_menu_template.png")
```

---

## สรุป

1. ✅ เตรียมรูป 2500x1686 px
2. ✅ วาดปุ่มตามพิกัด
3. ✅ Compress ให้ < 1 MB
4. ✅ อัปโหลดด้วยสคริปต์
5. ✅ ทดสอบใน LINE

**พร้อมเปลี่ยนรูปใหม่แล้ว!** 🎨
