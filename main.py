import os
import re
import time
import random
import requests
from seleniumbase import SB

BOT_TOKEN = "8841919944:AAGR4bYNVPfAQFFWcx8xrHKSlbqFmrINbHA"
DEFAULT_CHAT_ID = "5276103292"

METERS = [
    {"num": "24903832", "name": "দোকানের মিটার"},
    {"num": "24032515", "name": "হারোয়া ঘুণ্টির পাড় (বাসা)"},
    {"num": "24903831", "name": "2nd Floor"},
    {"num": "24000679", "name": "2nd 2no."},
    {"num": "24023242", "name": "1st 1no."},
    {"num": "24901143", "name": "1st 2no."},
    {"num": "24904999", "name": "3rd floor"},
    {"num": "24011715", "name": "Apa (বাসা)"},
    {"num": "24902351", "name": "gp"},
    {"num": "24908365", "name": "Robi"}
]

HARDCODED_PROXIES = """
61.178.81.100:1080
61.244.157.239:1080
61.49.7.135:1080
62.101.190.215:11055
62.105.9.127:1025
62.143.179.95:2555
62.243.224.179:1080
62.60.136.28:6688
63.246.179.176:50775
64.216.107.164:22077
64.233.155.225:6487
64.238.174.221:7801
64.92.151.214:29137
65.96.30.103:62093
66.108.170.178:12162
66.142.148.163:5187
66.168.246.241:41229
66.176.133.159:9721
66.41.191.93:3651
67.11.58.89:43639
67.149.192.54:35351
67.163.32.215:22743
67.164.134.211:47029
67.165.59.30:9975
67.166.85.255:54785
"""

PROXIES = [p.strip() for p in re.split(r'[\n,]', HARDCODED_PROXIES) if p.strip()]

def send_telegram_msg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": DEFAULT_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def send_telegram_photo(photo_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            payload = {"chat_id": DEFAULT_CHAT_ID, "caption": caption}
            requests.post(url, data=payload, files={"photo": photo}, timeout=15)
    except:
        send_telegram_msg(caption)

def try_loading_site_with_retries(max_retries=5):
    random.shuffle(PROXIES) # লিস্টটা এলোমেলো করে নেবে
    
    for i in range(min(max_retries, len(PROXIES))):
        proxy = PROXIES[i]
        print(f"Testing Proxy: {proxy}")
        
        sb_kwargs = {
            "uc": True,
            "test": True,
            "headless": True,
            "browser": "chrome",
            "window_size": "1920,1080",
            "proxy": proxy
        }
        
        # sb অবজেক্ট তৈরি করে পেজ লোডের চেষ্টা
        try:
            sb = SB(**sb_kwargs)
            sb.setUp()
            sb.uc_open_with_reconnect("https://customer.nesco.gov.bd/pre/panel", 4)
            
            # যদি ইনপুট বক্স পেয়ে যায়, তার মানে প্রক্সিটা ১০০% ওয়ার্কিং
            if sb.is_element_present('input[name="cust_no"]'):
                return sb, proxy
                
            # না পেলে ব্রাউজার ক্লোজ করে পরের প্রক্সিতে যাবে
            sb.tearDown()
        except Exception:
            try:
                sb.tearDown()
            except:
                pass
            
    return None, None

def get_meter_balance(sb, meter_num):
    sb.clear('input[name="cust_no"]')
    for char in meter_num:
        sb.add_text('input[name="cust_no"]', char)
        time.sleep(0.1)
        
    time.sleep(1)
    sb.click('button[type="submit"], input[type="submit"]')
    
    sb.wait_for_text('অবশিষ্ট ব্যালেন্স', timeout=15)
    time.sleep(2)
    
    page_source = sb.get_page_source()
    match = re.search(r'অবশিষ্ট ব্যালেন্স[\s\S]*?([\d\.\,]+)', page_source)
    
    # পরের মিটারের জন্য আবার মেইন পেজে ফিরে যাওয়া
    sb.uc_open_with_reconnect("https://customer.nesco.gov.bd/pre/panel", 2)
    sb.wait_for_element('input[name="cust_no"]', timeout=10)
    
    if match:
        return float(match.group(1).replace(',', ''))
    return None

def main():
    send_telegram_msg("🔄 বটের কাজ শুরু হচ্ছে, সঠিক প্রক্সি খোঁজা হচ্ছে...")
    
    # কাজ করে এমন একটি প্রক্সি খুঁজে বের করবে (সর্বোচ্চ ৫ বার চেষ্টা করবে)
    sb, working_proxy = try_loading_site_with_retries(5)
    
    if not sb:
        send_telegram_msg("🚨 *Critical Error*\nকোনো ফ্রি প্রক্সি কাজ করেনি। সাইটটি ক্লাউডফ্লেয়ারে ব্লক হয়ে আছে।")
        return

    try:
        for meter in METERS:
            try:
                balance = get_meter_balance(sb, meter["num"])
                if balance is not None:
                    msg = (
                        f"⚡ *NESCO Balance Update* ⚡\n"
                        f"━━━━━━━━━━━━━━━━━━━\n"
                        f"🏷️ *মিটারের নাম:* *{meter['name']}*\n"
                        f"🔢 *মিটার নম্বর:* `{meter['num']}`\n"
                        f"💰 *অবশিষ্ট ব্যালেন্স:* *{balance:.2f} ৳*\n"
                        f"🟢 _Developed by SK JOY_\n"
                        f"━━━━━━━━━━━━━━━━━━━"
                    )
                    send_telegram_msg(msg)
                else:
                    send_telegram_msg(f"🚨 *NESCO Update Failed*\n🏷️ *{meter['name']}*\n❌ ব্যালেন্স পাওয়া যায়নি।")
                time.sleep(3) 
                
            except Exception as e:
                err_type = type(e).__name__
                screenshot_file = f"error_{meter['num']}.png"
                sb.save_screenshot(screenshot_file)
                msg = f"🚨 *NESCO Error* 🚨\n🏷️ *{meter['name']}* (`{meter['num']}`)\n❌ সমস্যা: {err_type}\n🔗 কাজ করা প্রক্সি: `{working_proxy}`"
                send_telegram_photo(screenshot_file, msg)
                
                # যদি এক মিটার ফেইল করে, তবুও পেজটা রিলোড করে পরের মিটারের জন্য রেডি করা
                sb.uc_open_with_reconnect("https://customer.nesco.gov.bd/pre/panel", 3)
    finally:
        try:
            sb.tearDown()
        except:
            pass

if __name__ == "__main__":
    main()
