#!/usr/bin/env python3
"""
สร้าง Rich Menu แบบ 6 ปุ่ม (เหมือนเดิม) แต่ใช้ Postback
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

def delete_all_rich_menus():
    """ลบ Rich Menu เก่าทั้งหมด"""
    url = 'https://api.line.me/v2/bot/richmenu/list'
    headers = {'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        for menu in data.get('richmenus', []):
            menu_id = menu['richMenuId']
            delete_url = f'https://api.line.me/v2/bot/richmenu/{menu_id}'
            requests.delete(delete_url, headers=headers)
            print(f"🗑️ Deleted Rich Menu: {menu_id}")

def create_rich_menu_6buttons():
    """สร้าง Rich Menu 6 ปุ่ม"""
    url = 'https://api.line.me/v2/bot/richmenu'
    headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Layout: 2 แถว x 3 คอลัมน์
    # แถวบน: สภาพอากาศ | แจ้งจุดเกิดไฟ | จุดเกิดไฟ
    # แถวล่าง: พยากรณ์ล่วงหน้า | วิธีเงื่อนเหตุ | เข้าสู่เว็บไซต์
    
    col_width = 2500 // 3  # 833
    row_height = 843 // 2   # 421
    
    payload = {
        "size": {"width": 2500, "height": 843},
        "selected": True,
        "name": "NagaSkyguard Menu",
        "chatBarText": "เมนู",
        "areas": [
            # แถวบน - ซ้าย: สภาพอากาศ / ค่าฝุ่น
            {
                "bounds": {"x": 0, "y": 0, "width": col_width, "height": row_height},
                "action": {
                    "type": "postback",
                    "label": "สภาพอากาศ / ค่าฝุ่น",
                    "data": "action=check_pm25"
                }
            },
            # แถวบน - กลาง: แจ้งจุดเกิดไฟ
            {
                "bounds": {"x": col_width, "y": 0, "width": col_width + 1, "height": row_height},
                "action": {
                    "type": "postback",
                    "label": "แจ้งจุดเกิดไฟ",
                    "data": "action=report_fire"
                }
            },
            # แถวบน - ขวา: จุดเกิดไฟ (แผนที่)
            {
                "bounds": {"x": col_width * 2 + 1, "y": 0, "width": col_width, "height": row_height},
                "action": {
                    "type": "uri",
                    "label": "จุดเกิดไฟ",
                    "uri": "https://pm25-nakhon-phanom.onrender.com"
                }
            },
            # แถวล่าง - ซ้าย: พยากรณ์ล่วงหน้า
            {
                "bounds": {"x": 0, "y": row_height, "width": col_width, "height": row_height + 1},
                "action": {
                    "type": "postback",
                    "label": "พยากรณ์ล่วงหน้า",
                    "data": "action=forecast"
                }
            },
            # แถวล่าง - กลาง: วิธีเงื่อนเหตุ
            {
                "bounds": {"x": col_width, "y": row_height, "width": col_width + 1, "height": row_height + 1},
                "action": {
                    "type": "postback",
                    "label": "วิธีเงื่อนเหตุ",
                    "data": "action=help"
                }
            },
            # แถวล่าง - ขวา: เข้าสู่เว็บไซต์
            {
                "bounds": {"x": col_width * 2 + 1, "y": row_height, "width": col_width, "height": row_height + 1},
                "action": {
                    "type": "uri",
                    "label": "เข้าสู่เว็บไซต์",
                    "uri": "https://pm25-nakhon-phanom.onrender.com"
                }
            }
        ]
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        rich_menu_id = data['richMenuId']
        print(f"✅ Created Rich Menu: {rich_menu_id}")
        return rich_menu_id
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None

def main():
    print("🚀 Setting up Rich Menu (6 buttons)...")
    
    # 1. ลบ Rich Menu เก่า
    print("\n1️⃣ Deleting old Rich Menus...")
    delete_all_rich_menus()
    
    # 2. สร้าง Rich Menu ใหม่
    print("\n2️⃣ Creating new Rich Menu...")
    rich_menu_id = create_rich_menu_6buttons()
    
    if not rich_menu_id:
        print("❌ Failed to create Rich Menu")
        return
    
    print("\n✅ Rich Menu created!")
    print(f"📝 Rich Menu ID: {rich_menu_id}")
    print("\n⚠️ ต้องอัพโหลดรูป Rich Menu ต่อ")
    print(f"   รันคำสั่ง: python scripts/upload_rich_menu_image_6buttons.py {rich_menu_id}")

if __name__ == '__main__':
    main()
