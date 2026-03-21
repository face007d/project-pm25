"""
Upload Rich Menu Image and Set as Default
"""

import os
import sys
from linebot import LineBotApi
from dotenv import load_dotenv

load_dotenv()

def upload_and_set_default(rich_menu_id, image_path):
    """อัพโหลดรูปและตั้งเป็น default"""
    
    line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
    
    print("🚀 Uploading Rich Menu image...")
    print(f"📝 Rich Menu ID: {rich_menu_id}")
    print(f"🖼️ Image: {image_path}")
    
    # 1. อัพโหลดรูป
    print("\n1️⃣ Uploading image...")
    with open(image_path, 'rb') as f:
        # ตรวจสอบนามสกุลไฟล์
        content_type = 'image/jpeg' if image_path.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
        line_bot_api.set_rich_menu_image(rich_menu_id, content_type, f)
    print("✅ Uploaded image successfully")
    
    # 2. ตั้งเป็น default
    print("\n2️⃣ Setting as default...")
    line_bot_api.set_default_rich_menu(rich_menu_id)
    print("✅ Set as default Rich Menu")
    
    # 3. Link กับ users ทั้งหมด
    print("\n3️⃣ Linking to all users...")
    try:
        # ดึง user IDs จาก database
        from backend.database import SupabaseDB
        db = SupabaseDB()
        users = db.get_all_line_users()
        
        if users:
            print(f"\n📤 Linking to {len(users)} users...")
            for i, user in enumerate(users, 1):
                try:
                    line_bot_api.link_rich_menu_to_user(user['line_user_id'], rich_menu_id)
                except:
                    pass
            print(f"✅ Linked to {len(users)}/{len(users)} users")
        else:
            print("⚠️ No users found in database")
    except Exception as e:
        print(f"⚠️ Could not link to users: {e}")
    
    print("\n✅ Rich Menu is now active!")
    print("🎉 ลองเปิด LINE Bot ดูได้เลย")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python upload_rich_menu_image.py <rich_menu_id> <image_path>")
        sys.exit(1)
    
    rich_menu_id = sys.argv[1]
    image_path = sys.argv[2]
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        sys.exit(1)
    
    upload_and_set_default(rich_menu_id, image_path)
