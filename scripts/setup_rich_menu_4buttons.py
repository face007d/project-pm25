"""
Setup Rich Menu 4 Buttons for NagaSkyguard LINE Bot
Layout: 2500x1686 pixels (4 buttons)
"""

import os
from linebot import LineBotApi
from linebot.models import RichMenu, RichMenuSize, RichMenuArea, RichMenuBounds, PostbackAction, URIAction
from dotenv import load_dotenv

load_dotenv()

def setup_rich_menu():
    """สร้าง Rich Menu 4 ปุ่ม"""
    
    line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
    
    print("🚀 Setting up Rich Menu (2500x1686 - 4 buttons)...")
    
    # 1. ลบ Rich Menu เก่าทั้งหมด
    print("\n1️⃣ Deleting old Rich Menus...")
    rich_menu_list = line_bot_api.get_rich_menu_list()
    for rm in rich_menu_list:
        line_bot_api.delete_rich_menu(rm.rich_menu_id)
        print(f"🗑️ Deleted Rich Menu: {rm.rich_menu_id}")
    
    # 2. สร้าง Rich Menu ใหม่
    print("\n2️⃣ Creating new Rich Menu...")
    
    rich_menu = RichMenu(
        size=RichMenuSize(width=2500, height=1686),
        selected=True,
        name="Naka_monitoring Menu 5 Buttons",
        chat_bar_text="Naka Monitor",
        areas=[
            # ปุ่ม 1: ค่าฝุ่น PM2.5 ณ ขณะนี้ (บนซ้าย)
            RichMenuArea(
                bounds=RichMenuBounds(x=0, y=0, width=833, height=843),
                action=PostbackAction(label='ค่าฝุ่น PM2.5', data='action=check_pm25')
            ),
            # ปุ่ม 2: ดูข้อมูลเพิ่มเติมบนเว็บไซต์ (บนกลาง)
            RichMenuArea(
                bounds=RichMenuBounds(x=833, y=0, width=834, height=843),
                action=URIAction(label='ดูข้อมูลเพิ่มเติม', uri='https://pm25-nakhon-phanom.onrender.com')
            ),
            # ปุ่ม 3: สภาพอากาศ (บนขวา)
            RichMenuArea(
                bounds=RichMenuBounds(x=1667, y=0, width=833, height=843),
                action=PostbackAction(label='สภาพอากาศ', data='action=weather')
            ),
            # ปุ่ม 4: แจ้งจุดเกิดไฟ (ล่างซ้าย)
            RichMenuArea(
                bounds=RichMenuBounds(x=0, y=843, width=833, height=843),
                action=PostbackAction(label='แจ้งจุดเกิดไฟ', data='action=report_fire')
            ),
            # ปุ่ม 5: วิธีแจ้งเหตุ (ล่างขวา)
            RichMenuArea(
                bounds=RichMenuBounds(x=1667, y=843, width=833, height=843),
                action=PostbackAction(label='วิธีแจ้งเหตุ', data='action=help')
            )
        ]
    )
    
    rich_menu_id = line_bot_api.create_rich_menu(rich_menu=rich_menu)
    print(f"✅ Created Rich Menu: {rich_menu_id}")
    
    print(f"\n✅ Rich Menu created!")
    print(f"📝 Rich Menu ID: {rich_menu_id}")
    print(f"\n⚠️ ต้องอัพโหลดรูป Rich Menu ต่อ")
    print(f"   รันคำสั่ง: python scripts/upload_rich_menu_image.py {rich_menu_id} <path_to_image>")
    
    return rich_menu_id

if __name__ == "__main__":
    setup_rich_menu()
