#!/usr/bin/env python3
"""
ส่งการแจ้งเตือนค่าฝุ่น PM2.5 ทุกเช้า
ทำงานผ่าน GitHub Actions หรือ Cron Job
"""

import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv

# โหลด environment variables
load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
WAQI_API_TOKEN = os.getenv('WAQI_API_TOKEN', '6e19dc4d73747ab27c397b590fdbd504f1f496fc')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def get_pm25_data():
    """ดึงข้อมูล PM2.5 จาก WAQI API"""
    try:
        keyword = 'nakhon phanom'
        
        # 1. ค้นหาสถานี
        search_url = f'https://api.waqi.info/search/?token={WAQI_API_TOKEN}&keyword={keyword}'
        search_res = requests.get(search_url, timeout=10)
        search_data = search_res.json()
        
        if search_data.get('status') == 'ok' and search_data.get('data'):
            station_uid = search_data['data'][0]['uid']
            
            # 2. ดึงข้อมูลจากสถานี
            feed_url = f'https://api.waqi.info/feed/@{station_uid}/?token={WAQI_API_TOKEN}'
            feed_res = requests.get(feed_url, timeout=10)
            data = feed_res.json()
            
            if data.get('status') == 'ok':
                pm25 = data['data']['iaqi'].get('pm25', {}).get('v', 0)
                aqi = data['data'].get('aqi', pm25)
                city = data['data']['city'].get('name', 'นครพนม')
                time = data['data']['time'].get('s', '')
                
                # ข้อมูลสภาพอากาศ
                temp = data['data']['iaqi'].get('t', {}).get('v', 0)
                humidity = data['data']['iaqi'].get('h', {}).get('v', 0)
                
                return {
                    'pm25': pm25,
                    'aqi': aqi,
                    'city': city,
                    'time': time,
                    'temp': temp,
                    'humidity': humidity
                }
    except Exception as e:
        print(f"❌ Error fetching PM2.5 data: {e}")
    
    return None

def get_pm25_level(pm25):
    """กำหนดระดับและสีตามค่า PM2.5"""
    if pm25 <= 25:
        return {
            'level': 'ดีมาก',
            'color': '#16A34A',
            'emoji': '🟢',
            'advice': 'อากาศดี เหมาะสำหรับกิจกรรมกลางแจ้ง',
            'bg_color': '#F0FDF4'
        }
    elif pm25 <= 37.5:
        return {
            'level': 'ปานกลาง',
            'color': '#EAB308',
            'emoji': '🟡',
            'advice': 'ผู้ที่มีความไวควรระวัง',
            'bg_color': '#FEFCE8'
        }
    elif pm25 <= 50:
        return {
            'level': 'เริ่มมีผล',
            'color': '#F59E0B',
            'emoji': '🟠',
            'advice': 'ควรสวมหน้ากากเมื่อออกนอกบ้าน',
            'bg_color': '#FEF3C7'
        }
    elif pm25 <= 90:
        return {
            'level': 'ไม่ดี',
            'color': '#DC2626',
            'emoji': '🔴',
            'advice': 'หลีกเลี่ยงกิจกรรมกลางแจ้ง',
            'bg_color': '#FEE2E2'
        }
    else:
        return {
            'level': 'อันตราย',
            'color': '#7C3AED',
            'emoji': '🟣',
            'advice': 'ห้ามออกนอกบ้านโดยเด็ดขาด',
            'bg_color': '#F3E8FF'
        }

def get_all_line_users():
    """ดึงรายชื่อผู้ใช้ทั้งหมดจาก Supabase"""
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
        print(f"❌ Error fetching users: {e}")
    
    return []

def create_flex_message(pm25_data):
    """สร้าง Flex Message สวยงาม"""
    level_info = get_pm25_level(pm25_data['pm25'])
    now = datetime.now()
    
    return {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "☀️ รายงานคุณภาพอากาศ",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#FFFFFF"
                },
                {
                    "type": "text",
                    "text": now.strftime("%d/%m/%Y · %H:%M น."),
                    "size": "xs",
                    "color": "#FFFFFF",
                    "margin": "sm"
                }
            ],
            "backgroundColor": level_info['color'],
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": f"{level_info['emoji']} PM2.5",
                                    "size": "sm",
                                    "color": "#A89E8E"
                                },
                                {
                                    "type": "text",
                                    "text": f"{pm25_data['pm25']}",
                                    "size": "4xl",
                                    "weight": "bold",
                                    "color": level_info['color']
                                },
                                {
                                    "type": "text",
                                    "text": "µg/m³",
                                    "size": "xs",
                                    "color": "#A89E8E"
                                }
                            ],
                            "flex": 1
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": level_info['level'],
                                    "size": "xl",
                                    "weight": "bold",
                                    "color": level_info['color'],
                                    "align": "end"
                                },
                                {
                                    "type": "text",
                                    "text": f"AQI: {pm25_data['aqi']}",
                                    "size": "sm",
                                    "color": "#706B60",
                                    "align": "end",
                                    "margin": "sm"
                                }
                            ],
                            "flex": 1
                        }
                    ],
                    "spacing": "md"
                },
                {
                    "type": "separator",
                    "margin": "xl"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "💡 คำแนะนำ",
                            "size": "sm",
                            "weight": "bold",
                            "color": "#1C1A17"
                        },
                        {
                            "type": "text",
                            "text": level_info['advice'],
                            "size": "sm",
                            "color": "#706B60",
                            "wrap": True,
                            "margin": "sm"
                        }
                    ],
                    "margin": "xl",
                    "paddingAll": "12px",
                    "backgroundColor": level_info['bg_color'],
                    "cornerRadius": "8px"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "🌡️ อุณหภูมิ",
                                    "size": "xs",
                                    "color": "#A89E8E"
                                },
                                {
                                    "type": "text",
                                    "text": f"{pm25_data['temp']}°C",
                                    "size": "md",
                                    "weight": "bold",
                                    "color": "#1C1A17"
                                }
                            ],
                            "flex": 1
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "💧 ความชื้น",
                                    "size": "xs",
                                    "color": "#A89E8E"
                                },
                                {
                                    "type": "text",
                                    "text": f"{pm25_data['humidity']}%",
                                    "size": "md",
                                    "weight": "bold",
                                    "color": "#1C1A17"
                                }
                            ],
                            "flex": 1
                        }
                    ],
                    "spacing": "md",
                    "margin": "xl"
                }
            ],
            "spacing": "md",
            "paddingAll": "20px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "uri",
                        "label": "📍 ดูแผนที่",
                        "uri": "https://pm25-nakhon-phanom.onrender.com"
                    },
                    "style": "primary",
                    "color": level_info['color'],
                    "height": "sm"
                }
            ],
            "spacing": "sm",
            "paddingAll": "20px"
        }
    }

def send_broadcast_message(user_ids, flex_message):
    """ส่งข้อความไปยังผู้ใช้ทั้งหมด"""
    url = 'https://api.line.me/v2/bot/message/multicast'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }
    
    # LINE multicast รองรับสูงสุด 500 คนต่อครั้ง
    batch_size = 500
    success_count = 0
    
    for i in range(0, len(user_ids), batch_size):
        batch = user_ids[i:i + batch_size]
        
        payload = {
            'to': batch,
            'messages': [
                {
                    'type': 'flex',
                    'altText': '☀️ รายงานคุณภาพอากาศประจำวัน',
                    'contents': flex_message
                }
            ]
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                success_count += len(batch)
                print(f"✅ Sent to {len(batch)} users (Total: {success_count})")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Error sending batch: {e}")
    
    return success_count

def main():
    """Main function"""
    print("🚀 Starting daily notification...")
    
    # 1. ดึงข้อมูล PM2.5
    print("📊 Fetching PM2.5 data...")
    pm25_data = get_pm25_data()
    
    if not pm25_data:
        print("❌ Failed to fetch PM2.5 data")
        sys.exit(1)
    
    print(f"✅ PM2.5: {pm25_data['pm25']} µg/m³")
    
    # 2. ดึงรายชื่อผู้ใช้
    print("👥 Fetching LINE users...")
    user_ids = get_all_line_users()
    
    if not user_ids:
        print("⚠️ No users found")
        sys.exit(0)
    
    print(f"✅ Found {len(user_ids)} users")
    
    # 3. สร้าง Flex Message
    print("🎨 Creating Flex Message...")
    flex_message = create_flex_message(pm25_data)
    
    # 4. ส่งข้อความ
    print("📤 Sending messages...")
    success_count = send_broadcast_message(user_ids, flex_message)
    
    print(f"✅ Successfully sent to {success_count}/{len(user_ids)} users")
    print("🎉 Daily notification completed!")

if __name__ == '__main__':
    main()
