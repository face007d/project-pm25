"""
Test Supabase Storage Connection
ทดสอบการเชื่อมต่อกับ Supabase Storage bucket
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import io

# โหลด environment variables
load_dotenv()

def test_storage_connection():
    """ทดสอบการเชื่อมต่อกับ Supabase Storage"""
    
    print("=" * 60)
    print("🧪 Testing Supabase Storage Connection")
    print("=" * 60)
    
    # 1. ตรวจสอบ credentials (ใช้ service_role key สำหรับ Storage)
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ FAILED: Missing SUPABASE_URL or SUPABASE_KEY in .env")
        return False
    
    key_type = "service_role" if os.getenv('SUPABASE_SERVICE_KEY') else "anon"
    print(f"✅ Credentials found ({key_type} key)")
    print(f"   URL: {supabase_url}")
    print(f"   Key: {supabase_key[:20]}...")
    
    try:
        # 2. สร้าง Supabase client
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created")
        
        # 3. ทดสอบเข้าถึง bucket โดยตรง
        print("\n📦 Testing bucket access...")
        bucket_name = 'fire_image'
        
        try:
            # ลองลิสต์ไฟล์ใน bucket เพื่อทดสอบว่า bucket มีอยู่จริง
            files = supabase.storage.from_(bucket_name).list()
            print(f"✅ Bucket '{bucket_name}' exists")
            print(f"   Files in bucket: {len(files)}")
        except Exception as bucket_error:
            print(f"❌ FAILED: Cannot access bucket '{bucket_name}'")
            print(f"   Error: {bucket_error}")
            print(f"\n💡 Please create bucket '{bucket_name}' in Supabase:")
            print(f"   1. Go to: {supabase_url}/project/_/storage/buckets")
            print(f"   2. Click 'New bucket'")
            print(f"   3. Name: {bucket_name}")
            print(f"   4. Make it Public")
            return False
        
        # 4. ทดสอบอัพโหลดไฟล์ทดสอบ
        print(f"\n📤 Testing upload to '{bucket_name}'...")
        test_content = b"Test image content from Python script"
        test_filename = "test_connection.txt"
        
        response = supabase.storage.from_(bucket_name).upload(
            test_filename,
            test_content,
            file_options={"content-type": "text/plain", "upsert": "true"}
        )
        print(f"✅ Upload successful")
        
        # 5. ทดสอบสร้าง public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(test_filename)
        print(f"✅ Public URL generated:")
        print(f"   {public_url}")
        
        # 6. ทดสอบลบไฟล์
        print(f"\n🗑️  Cleaning up test file...")
        supabase.storage.from_(bucket_name).remove([test_filename])
        print(f"✅ Test file deleted")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_storage_connection()
    exit(0 if success else 1)
