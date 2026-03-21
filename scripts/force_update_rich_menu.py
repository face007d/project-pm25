#!/usr/bin/env python3
"""
บังคับอัพเดท Rich Menu ให้ผู้ใช้ทุกคน
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
NEW_RICH_MENU_ID = 'richmenu-fd7a497af0c707300c2cdc50101edf24'

def get_all_line_users():
    """ดึงรายชื่อผู้ใช้ทั้งหมด"""
    try:
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        
        url = f'{SUPABASE_URL}/rest/v1/line_users?select=line_user_id'
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            users = response.json()
            return [user['line_user_id'] for user in users]
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return []

def unlink_rich_menu_from_user(user_id):
    """ลบ Rich Menu เก่าออกจากผู้ใช้"""
    url = f'https://api.line.me/v2/bot/user/{user_id}/richmenu'
    headers = {'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'}
    
    response = requests.delete(url, headers=headers)
    return response.status_code in [200, 204]

def link_rich_menu_to_user(user_id, rich_menu_id):
    """ตั้ง Rich Menu ใหม่ให้ผู้ใช้"""
    url = f'https://api.line.me/v2/bot/user/{user_id}/richmenu/{rich_menu_id}'
    headers = {'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'}
    
    response = requests.post(url, headers=headers)
    return response.status_code == 200

def main():
    print("🚀 Force updating Rich Menu for all users...")
    
    # 1. ดึงรายชื่อผู้ใช้
    print("\n1️⃣ Fetching users...")
    user_ids = get_all_line_users()
    
    if not user_ids:
        print("⚠️ No users found")
        return
    
    print(f"✅ Found {len(user_ids)} users")
    
    # 2. อัพเดท Rich Menu ให้ทุกคน
    print("\n2️⃣ Updating Rich Menu...")
    success_count = 0
    
    for i, user_id in enumerate(user_ids, 1):
        # ลบเก่า
        unlink_rich_menu_from_user(user_id)
        
        # ตั้งใหม่
        if link_rich_menu_to_user(user_id, NEW_RICH_MENU_ID):
            success_count += 1
            print(f"✅ [{i}/{len(user_ids)}] Updated: {user_id}")
        else:
            print(f"❌ [{i}/{len(user_ids)}] Failed: {user_id}")
    
    print(f"\n✅ Updated {success_count}/{len(user_ids)} users")
    print("🎉 Done! ลองเปิด LINE Bot ดูใหม่")

if __name__ == '__main__':
    main()
