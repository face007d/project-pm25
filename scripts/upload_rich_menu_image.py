#!/usr/bin/env python3
"""
อัพโหลดรูป Rich Menu และตั้งเป็น default
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
RICH_MENU_ID = 'richmenu-fd7a497af0c707300c2cdc50101edf24'  # จาก output ก่อนหน้า

def upload_image(rich_menu_id, image_path):
    """อัพโหลดรูป Rich Menu"""
    url = f'https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content'
    headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'image/png'
    }
    
    with open(image_path, 'rb') as f:
        response = requests.post(url, headers=headers, data=f)
    
    if response.status_code == 200:
        print(f"✅ Uploaded image successfully")
        return True
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return False

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
    print("🚀 Uploading Rich Menu image...")
    
    # 1. อัพโหลดรูป
    print("\n1️⃣ Uploading image...")
    if not upload_image(RICH_MENU_ID, 'rich_menu.png'):
        return
    
    # 2. ตั้งเป็น default
    print("\n2️⃣ Setting as default...")
    set_default_rich_menu(RICH_MENU_ID)
    
    print("\n✅ Rich Menu is now active!")
    print("🎉 ลองเปิด LINE Bot ดูได้เลย")

if __name__ == '__main__':
    main()
