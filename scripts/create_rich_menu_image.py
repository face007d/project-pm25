#!/usr/bin/env python3
"""
สร้างรูป Rich Menu 2500x843 px
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_rich_menu_image():
    """สร้างรูป Rich Menu"""
    # สร้างภาพ 2500x843
    width, height = 2500, 843
    img = Image.new('RGB', (width, height), color='#1C1A17')
    draw = ImageDraw.Draw(img)
    
    # แบ่ง 3 ส่วน
    section_width = width // 3
    
    # ส่วนที่ 1: ตรวจสอบค่าฝุ่น (สีเขียว)
    draw.rectangle([0, 0, section_width, height], fill='#16A34A')
    
    # ส่วนที่ 2: รายงานไฟไหม้ (สีแดง)
    draw.rectangle([section_width, 0, section_width*2, height], fill='#DC2626')
    
    # ส่วนที่ 3: ดูแผนที่ (สีน้ำเงิน)
    draw.rectangle([section_width*2, 0, width, height], fill='#2563EB')
    
    # เส้นแบ่ง
    draw.line([section_width, 0, section_width, height], fill='white', width=3)
    draw.line([section_width*2, 0, section_width*2, height], fill='white', width=3)
    
    # ข้อความ (ใช้ font เริ่มต้น)
    try:
        # พยายามใช้ font ไทย
        font_large = ImageFont.truetype("C:/Windows/Fonts/tahoma.ttf", 80)
        font_small = ImageFont.truetype("C:/Windows/Fonts/tahoma.ttf", 40)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # ข้อความส่วนที่ 1
    text1_main = "💨"
    text1_sub = "ตรวจสอบค่าฝุ่น"
    draw.text((section_width//2, height//2 - 80), text1_main, fill='white', font=font_large, anchor='mm')
    draw.text((section_width//2, height//2 + 60), text1_sub, fill='white', font=font_small, anchor='mm')
    
    # ข้อความส่วนที่ 2
    text2_main = "🔥"
    text2_sub = "แจ้งจุดเกิดไฟ"
    draw.text((section_width + section_width//2, height//2 - 80), text2_main, fill='white', font=font_large, anchor='mm')
    draw.text((section_width + section_width//2, height//2 + 60), text2_sub, fill='white', font=font_small, anchor='mm')
    
    # ข้อความส่วนที่ 3
    text3_main = "📍"
    text3_sub = "ดูแผนที่"
    draw.text((section_width*2 + section_width//2, height//2 - 80), text3_main, fill='white', font=font_large, anchor='mm')
    draw.text((section_width*2 + section_width//2, height//2 + 60), text3_sub, fill='white', font=font_small, anchor='mm')
    
    # บันทึกไฟล์
    output_path = 'rich_menu.png'
    img.save(output_path)
    print(f"✅ Created: {output_path}")
    return output_path

if __name__ == '__main__':
    create_rich_menu_image()
