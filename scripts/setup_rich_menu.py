#!/usr/bin/env python3
"""
สร้างและตั้งค่า Rich Menu ใหม่
รันคำสั่ง: python scripts/setup_rich_menu.py
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

def create_rich_menu():
    """สร้าง Rich Menu ใหม่"""
    url = 'https://api.line.me/v2/bot/richmenu'
    headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "size": {"width": 2500, "height": 843},
        "selected": True,
        "name": "NagaSkyguard Menu",
        "chatBarText": "เมนูหลัก",
        "areas": [
            {
                "bounds": {"x": 0, "y": 0, "width": 833, "height": 843},
                "action": {
                    "type": "postback",
                    "label": "ตรวจสอบค่าฝุ่น",
                    "data": "action=check_pm25"
                }
            },
            {
                "bounds": {"x": 833, "y": 0, "width": 834, "height": 843},
                "action": {
                    "type": "postback",
                    "label": "รายงานไฟไหม้",
                    "data": "action=report_fire"
                }
            },
            {
                "bounds": {"x": 1667, "y": 0, "width": 833, "height": 843},
                "action": {
                    "type": "uri",
                    "label": "ดูแผนที่",
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

def set_default_rich_menu(rich_menu_id):
    """ตั้งเป็น Rich Menu เริ่มต้น"""
    url = f'https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}'
    headers = {'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'}
    
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        print(f"✅ Set as default Rich Menu")
        return True
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return False

def main():
    print("🚀 Setting up Rich Menu...")
    
    # 1. ลบ Rich Menu เก่า
    print("\n1️⃣ Deleting old Rich Menus...")
    delete_all_rich_menus()
    
    # 2. สร้าง Rich Menu ใหม่
    print("\n2️⃣ Creating new Rich Menu...")
    rich_menu_id = create_rich_menu()
    
    if not rich_menu_id:
        print("❌ Failed to create Rich Menu")
        return
    
    # 3. ตั้งเป็น default
    print("\n3️⃣ Setting as default...")
    set_default_rich_menu(rich_menu_id)
    
    print("\n✅ Rich Menu setup completed!")
    print(f"📝 Rich Menu ID: {rich_menu_id}")
    print("\n⚠️ หมายเหตุ:")
    print("- Rich Menu ยังไม่มีรูปภาพ (แสดงเป็นสีขาว)")
    print("- ต้องอัพโหลดรูป 2500x843 px ด้วยตัวเอง")
    print("- หรือใช้ LINE Developers Console")

if __name__ == '__main__':
    main()
