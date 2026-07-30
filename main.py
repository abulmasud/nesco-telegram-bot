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

# GitHub Secrets থেকে প্রক্সি রিড করা (নতুন লাইন বা কমা দিয়ে আলাদা করা)
RAW_PROXIES = os.environ.get("PROXY_LIST", "")
PROXIES = [p.strip() for p in re.split(r'[\n,]', RAW_PROXIES) if p.strip()]

def get_random_proxy():
    if PROXIES:
        selected = random.choice(PROXIES)
        print(f"🔗 Using Proxy: {selected}") 
        return selected
    return None

def send_telegram_msg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": DEFAULT_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def send_telegram_photo(photo_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            payload = {"chat_id": DEFAULT_CHAT_ID, "caption": caption}
            requests.post(url, data=payload, files={"photo": photo}, timeout=15)
    except Exception as e:
        print(f"Photo send error: {e}")
        send_telegram_msg(caption)

def get_meter_balance(sb, meter_num):
    url = "https://customer.nesco.gov.bd/pre/panel"
    sb.uc_open_with_reconnect(url, 4)
    
    # ইনপুট বক্স খোঁজা
    sb.wait_for_element('input[name="cust_no"]', timeout=15)
    input_selector = 'input[name="cust_no"]'
    
    sb.clear(input_selector)
    
    for char in meter_num:
        sb.add_text(input_selector, char)
        time.sleep(0.1)
        
    time.sleep(1)
    sb.click('button[type="submit"], input[type="submit"]')
    
    sb.wait_for_text('অবশিষ্ট ব্যালেন্স', timeout=15)
    time.sleep(2)
    
    page_source = sb.get_page_source()
    match = re.search(r'অবশিষ্ট ব্যালেন্স[\s\S]*?([\d\.\,]+)', page_source)
    
    if match:
        clean_bal = match.group(1).replace(',', '')
        return float(clean_bal)
    return None

def main():
    proxy = get_random_proxy()
    
    # proxy প্যারামিটার সহ SeleniumBase রান করা
    sb_kwargs = {
        "uc": True,
        "test": True,
        "headless": True,
        "browser": "chrome",
        "window_size": "1920,1080"
    }
    
    # যদি প্রক্সি পাওয়া যায়, তবে সেটি যুক্ত করবে
    if proxy:
        sb_kwargs["proxy"] = proxy

    with SB(**sb_kwargs) as sb:
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
                
                time.sleep(4) 
                
            except Exception as e:
                err_type = type(e).__name__
                screenshot_file = f"error_{meter['num']}.png"
                sb.save_screenshot(screenshot_file)
                
                msg = f"🚨 *NESCO Error* 🚨\n🏷️ *{meter['name']}* (`{meter['num']}`)\n❌ সমস্যা: {err_type}\n🔗 ব্যবহৃত প্রক্সি: `{proxy}`"
                send_telegram_photo(screenshot_file, msg)

if __name__ == "__main__":
    main()
