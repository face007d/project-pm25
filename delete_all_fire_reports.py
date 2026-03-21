"""
ลบข้อมูลจุดไฟทั้งหมดใน Supabase
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def delete_all_fire_reports():
    """ลบข้อมูลจุดไฟทั้งหมด"""
    
    # เชื่อมต่อ Supabase
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY")
        return
    
    client = create_client(url, key)
    print(f"✅ Connected to Supabase: {url}")
    
    try:
        # ดึงข้อมูลทั้งหมดก่อน
        response = client.table('fire_reports').select('*').execute()
        total = len(response.data) if response.data else 0
        
        print(f"\n📊 พบข้อมูลจุดไฟทั้งหมด: {total} จุด")
        
        if total == 0:
            print("✅ ไม่มีข้อมูลที่ต้องลบ")
            return
        
        # แสดงข้อมูลที่จะลบ
        print("\n🔥 รายการจุดไฟที่จะลบ:")
        for i, report in enumerate(response.data, 1):
            print(f"  {i}. ID: {report.get('id')} | พิกัด: {report.get('latitude')}, {report.get('longitude')} | วันที่: {report.get('created_at')}")
        
        # ยืนยันการลบ
        confirm = input(f"\n⚠️  ต้องการลบข้อมูลทั้งหมด {total} จุดใช่หรือไม่? (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("❌ ยกเลิกการลบ")
            return
        
        # ลบข้อมูลทั้งหมด (ใช้ gt แทน neq เพื่อหลีกเลี่ยง UUID error)
        delete_response = client.table('fire_reports').delete().gte('created_at', '2000-01-01').execute()
        
        print(f"\n✅ ลบข้อมูลสำเร็จ!")
        print(f"📊 ลบไปทั้งหมด: {total} จุด")
        print("\n🎯 พร้อมสำหรับการทดสอบใหม่ 20 จุด")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    delete_all_fire_reports()
