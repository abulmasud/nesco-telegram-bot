import os
import re
import time
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Telegram Config
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

def get_meter_balance(driver, meter_num):
    url = "https://customer.nesco.gov.bd/pre/panel"
    driver.get(url)
    
    wait = WebDriverWait(driver, 25)
    
    input_box = wait.until(EC.element_to_be_clickable((By.NAME, "cust_no")))
    input_box.clear()
    
    for char in meter_num:
        input_box.send_keys(char)
        time.sleep(0.1)
        
    time.sleep(1)
    
    submit_btn = driver.find_element(By.XPATH, "//button[@type='submit'] | //input[@type='submit']")
    driver.execute_script("arguments[0].click();", submit_btn)
    
    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'অবশিষ্ট ব্যালেন্স')]")))
    time.sleep(2)
    
    page_source = driver.page_source
    match = re.search(r'অবশিষ্ট ব্যালেন্স[\s\S]*?([\d\.\,]+)', page_source)
    
    if match:
        clean_bal = match.group(1).replace(',', '')
        return float(clean_bal)
    return None

def main():
    options = uc.ChromeOptions()
    # লিনাক্স সার্ভারের জন্য প্রয়োজনীয় ফ্ল্যাগ
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # version_main সরিয়ে দেওয়া হয়েছে যাতে লেটেস্ট ভার্সন অটো-ম্যাচ করে
    driver = uc.Chrome(options=options) 
    
    try:
        for meter in METERS:
            try:
                balance = get_meter_balance(driver, meter["num"])
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
                time.sleep(5) 
                
            except Exception as e:
                err_type = type(e).__name__
                msg = f"🚨 *NESCO Error* 🚨\n🏷️ *{meter['name']}* (`{meter['num']}`)\n❌ সমস্যা: {err_type} (পেজ লোড হয়নি)।"
                send_telegram(msg)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
