import os
import re
import time
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
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_meter_balance(driver, meter_num):
    url = "https://customer.nesco.gov.bd/pre/panel"
    driver.get(url)
    
    # পেজ লোডের জন্য অতিরিক্ত সময় দেয়া
    wait = WebDriverWait(driver, 20)
    
    # ইনপুট ফিল্ড অনুসন্ধান
    input_box = wait.until(EC.element_to_be_clickable((By.NAME, "cust_no")))
    input_box.clear()
    input_box.send_keys(meter_num)
    
    time.sleep(1) # টাইপিং সম্পন্ন হতে ছোট বিরতি
    
    # সাবমিট বাটন প্রেস
    submit_btn = driver.find_element(By.XPATH, "//button[@type='submit'] | //input[@type='submit'] | //button[contains(text(), 'রিচার্জ')]")
    driver.execute_script("arguments[0].click();", submit_btn)
    
    # ব্যালেন্স কন্টেইনার আসার জন্য অপেক্ষা
    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'অবশিষ্ট ব্যালেন্স')]")))
    
    time.sleep(2)
    page_source = driver.page_source
    
    match = re.search(r'অবশিষ্ট ব্যালেন্স[\s\S]*?([\d\.\,]+)', page_source)
    if match:
        clean_bal = match.group(1).replace(',', '')
        return float(clean_bal)
    return None

def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Anti-Bot Flags (অটোমেশন লুকানোর জন্য)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # CDP দিয়ে webdriver ফ্ল্যাগ সম্পূর্ণ হাইড করা
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
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
                    msg = (
                        f"🚨 *NESCO Update Failed* 🚨\n"
                        f"🏷️ *{meter['name']}* ({meter['num']})\n"
                        f"❌ ব্যালেন্স পেজ থেকে ফেচ করা যায়নি।"
                    )
                send_telegram(msg)
                time.sleep(3) # সার্ভার প্র his ড়ে প্রেশার কমাতে বিরতি
                
            except Exception as e:
                # লম্বা স্ট্যাকট্রেস বাদ দিয়ে সংক্ষিপ্ত এরর মেসেজ পাঠানো
                err_type = type(e).__name__
                msg = (
                    f"🚨 *NESCO Error* 🚨\n"
                    f"🏷️ *{meter['name']}* (`{meter['num']}`)\n"
                    f"❌ **সমস্যা:** {err_type} (সার্ভার সাড়া দেয়নি বা সিকিউরিটি ব্লক করেছে।)"
                )
                send_telegram(msg)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
