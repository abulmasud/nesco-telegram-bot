import os
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Telegram Config
BOT_TOKEN = "8841919944:AAGR4bYNVPfAQFFWcx8xrHKSlbqFmrINbHA"
DEFAULT_CHAT_ID = "5276103292"

# আপনার ১০টি মিটারের তালিকা
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
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_meter_balance(driver, meter_num):
    url = "https://customer.nesco.gov.bd/pre/panel"
    driver.get(url)
    
    # ইনপুট ফিল্ড ও বাটন খোঁজা
    wait = WebDriverWait(driver, 15)
    input_box = wait.until(EC.presence_of_element_located((By.NAME, "cust_no")))
    input_box.clear()
    input_box.send_keys(meter_num)
    
    submit_btn = driver.find_element(By.XPATH, "//button[@type='submit'] | //input[@type='submit']")
    submit_btn.click()
    
    # রেসপন্স আসার জন্য অপেক্ষা
    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'অবশিষ্ট ব্যালেন্স')]")))
    
    page_source = driver.page_source
    match = re.search(r'অবশিষ্ট ব্যালেন্স[\s\S]*?([\d\.\,]+)', page_source)
    if match:
        clean_bal = match.group(1).replace(',', '')
        return float(clean_bal)
    return None

def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        for meter in METERS:
            try:
                balance = get_meter_balance(driver, meter["num"])
                if balance is not None:
                    msg = f"⚡ *NESCO Balance Update* ⚡\n━━━━━━━━━━━━━━━━━━━\n🏷️ *মিটারের নাম:* *{meter['name']}*\n🔢 *মিটার নম্বর:* `{meter['num']}`\n💰 *অবশিষ্ট ব্যালেন্স:* *{balance:.2f} ৳*\n🟢 _Developed by SK JOY_\n━━━━━━━━━━━━━━━━━━━"
                else:
                    msg = f"🚨 *NESCO Update Failed* 🚨\n🏷️ *মিটারের নাম:* *{meter['name']}*\n🔢 *মিটার নম্বর:* `{meter['num']}`\n❌ ব্যালেন্স পাওয়া যায়নি।"
                
                send_telegram(msg)
            except Exception as e:
                print(f"Error fetching {meter['num']}: {e}")
                send_telegram(f"🚨 *NESCO Error* 🚨\n🏷️ *{meter['name']}* ({meter['num']})\n❌ {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
