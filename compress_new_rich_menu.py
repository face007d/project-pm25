"""
Compress Rich Menu Image to < 1MB
Usage: python compress_new_rich_menu.py <input_image>
Output: <input_image>_compressed.jpg
"""

import sys
from PIL import Image
import os

def compress_image(input_path, max_size_mb=1):
    """
    บีบอัดรูปภาพให้มีขนาดไม่เกิน max_size_mb MB
    """
    # เปิดรูป
    img = Image.open(input_path)
    
    # ตรวจสอบขนาด
    width, height = img.size
    expected_size = (2500, 1686)
    
    if (width, height) != expected_size:
        print(f"⚠️ Warning: Image size is {width}x{height}, expected {expected_size[0]}x{expected_size[1]}")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("❌ Cancelled")
            return None
    
    # แปลงเป็น RGB (ถ้าเป็น RGBA)
    if img.mode == 'RGBA':
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    # สร้างชื่อไฟล์ output
    base_name = os.path.splitext(input_path)[0]
    output_path = f"{base_name}_compressed.jpg"
    
    # ลอง quality ต่างๆ
    quality = 95
    max_size_bytes = max_size_mb * 1024 * 1024
    
    while quality > 10:
        img.save(output_path, 'JPEG', quality=quality, optimize=True)
        size = os.path.getsize(output_path)
        size_mb = size / (1024 * 1024)
        
        print(f"🔄 Trying quality {quality}... Size: {size_mb:.2f} MB")
        
        if size <= max_size_bytes:
            print(f"✅ Success! Compressed to {size_mb:.2f} MB (quality {quality})")
            print(f"📁 Output: {output_path}")
            return output_path
        
        quality -= 5
    
    print(f"⚠️ Could not compress below {max_size_mb} MB. Final size: {size_mb:.2f} MB")
    print(f"📁 Output: {output_path}")
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compress_new_rich_menu.py <input_image>")
        print("Example: python compress_new_rich_menu.py new_rich_menu.png")
        sys.exit(1)
    
    input_image = sys.argv[1]
    
    if not os.path.exists(input_image):
        print(f"❌ File not found: {input_image}")
        sys.exit(1)
    
    compress_image(input_image)
