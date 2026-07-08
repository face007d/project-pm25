"""
Update Rich Menu Image (Keep Same Button Areas)
Usage: python scripts/update_rich_menu_image.py <image_path>
"""

import os
import sys
from linebot import LineBotApi
from dotenv import load_dotenv

load_dotenv()

def update_rich_menu_image(image_path):
    """
    อัปเดตรูป Rich Menu ใหม่โดยไม่เปลี่ยนปุ่ม
    """
    line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
    
    print("🔍 Finding current Rich Menu...")
    
    # หา Rich Menu ปัจจุบัน
    rich_menu_list = line_bot_api.get_rich_menu_list()
    
    if not rich_menu_list:
        print("❌ No Rich Menu found. Please create one first.")
        print("   Run: python scripts/setup_rich_menu_4buttons.py")
        return None
    
    # ใช้ Rich Menu แรก
    current_rich_menu = rich_menu_list[0]
    rich_menu_id = current_rich_menu.rich_menu_id
    
    print(f"✅ Found Rich Menu: {rich_menu_id}")
    print(f"   Name: {current_rich_menu.name}")
    print(f"   Size: {current_rich_menu.size.width}x{current_rich_menu.size.height}")
    
    # ตรวจสอบไฟล์รูป
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return None
    
    file_size = os.path.getsize(image_path)
    file_size_mb = file_size / (1024 * 1024)
    
    print(f"\n📷 Uploading new image...")
    print(f"   File: {image_path}")
    print(f"   Size: {file_size_mb:.2f} MB")
    
    if file_size_mb > 1:
        print(f"⚠️ Warning: File size > 1 MB. LINE may reject it.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("❌ Cancelled")
            return None
    
    # อัปโหลดรูปใหม่
    try:
        with open(image_path, 'rb') as f:
            line_bot_api.set_rich_menu_image(rich_menu_id, 'image/jpeg', f)
        
        print(f"✅ Image uploaded successfully!")
        print(f"\n📱 Rich Menu updated!")
        print(f"   Rich Menu ID: {rich_menu_id}")
        print(f"\n⚠️ หมายเหตุ: อาจต้องรอ 1-2 นาทีจึงจะเห็นการเปลี่ยนแปลงใน LINE")
        
        return rich_menu_id
        
    except Exception as e:
        print(f"❌ Error uploading image: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/update_rich_menu_image.py <image_path>")
        print("Example: python scripts/update_rich_menu_image.py new_rich_menu_compressed.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    update_rich_menu_image(image_path)
