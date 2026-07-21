import re
import time
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

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": DEFAULT_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_meter_balance(sb, meter_num):
    url = "https://customer.nesco.gov.bd/pre/panel"
    
    # uc_open_with_reconnect ক্লাউডফ্লেয়ার বাইপাস করতে সাহায্য করে
    sb.uc_open_with_reconnect(url, 4)
    
    # ইনপুট বক্স লোড হওয়ার জন্য অপেক্ষা
    sb.wait_for_element('input[name="cust_no"]', timeout=20)
    sb.clear('input[name="cust_no"]')
    
    # মানুষের মতো টাইপ করা
    for char in meter_num:
        sb.add_text('input[name="cust_no"]', char)
        time.sleep(0.1)
        
    time.sleep(1)
    
    # সাবমিট বাটনে ক্লিক
    sb.click('button[type="submit"], input[type="submit"]')
    
    # ব্যালেন্স লেখা আসার জন্য অপেক্ষা
    sb.wait_for_text('অবশিষ্ট ব্যালেন্স', timeout=20)
    time.sleep(2)
    
    page_source = sb.get_page_source()
    match = re.search(r'অবশিষ্ট ব্যালেন্স[\s\S]*?([\d\.\,]+)', page_source)
    
    if match:
        clean_bal = match.group(1).replace(',', '')
        return float(clean_bal)
    return None

def main():
    # UC (Undetected Chromedriver) Mode এ SeleniumBase চালু করা
    with SB(uc=True, test=True, headless=True, browser="chrome", window_size="1920,1080") as sb:
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
                else:
                    msg = f"🚨 *NESCO Update Failed* 🚨\n🏷️ *{meter['name']}* ({meter['num']})\n❌ ব্যালেন্স পেজ থেকে ফেচ করা যায়নি।"
                
                send_telegram(msg)
                time.sleep(4) 
                
            except Exception as e:
                err_type = type(e).__name__
                msg = f"🚨 *NESCO Error* 🚨\n🏷️ *{meter['name']}* (`{meter['num']}`)\n❌ সমস্যা: {err_type}"
                send_telegram(msg)

if __name__ == "__main__":
    main()
