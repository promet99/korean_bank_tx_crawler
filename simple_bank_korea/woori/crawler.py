import os
import time
import math
import operator
import datetime
from functools import reduce
from PIL import Image, ImageChops
from io import BytesIO
from bs4 import BeautifulSoup as bs
from dateutil import parser

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

def rmsdiff(im1, im2):
    im1 = im1.convert('RGBA')
    im2 = im2.convert('RGBA')
    h = ImageChops.difference(im1, im2).histogram()
    return math.sqrt(reduce(operator.add,
                            map(lambda h, i: h * (i ** 2), h, range(256))
                            ) / (float(im1.size[0]) * im1.size[1]))

keys_info = [
    {"index": 0, "coords": [161, 74, 205, 116], "center": (183, 95)},
    {"index": 1, "coords": [208, 74, 252, 116], "center": (230, 95)},
    {"index": 2, "coords": [208, 120, 252, 162], "center": (230, 141)},
    {"index": 3, "coords": [208, 166, 252, 208], "center": (230, 187)},
    {"index": 4, "coords": [208, 212, 252, 254], "center": (230, 233)},
    {"index": 5, "coords": [161, 212, 205, 254], "center": (183, 233)},
    {"index": 6, "coords": [114, 212, 158, 254], "center": (136, 233)},
    {"index": 7, "coords": [67, 212, 111, 254], "center": (89, 233)},
    {"index": 8, "coords": [67, 166, 111, 208], "center": (89, 187)},
    {"index": 9, "coords": [67, 120, 111, 162], "center": (89, 141)},
    {"index": 10, "coords": [67, 74, 111, 116], "center": (89, 95)},
    {"index": 11, "coords": [114, 74, 158, 116], "center": (136, 95)}
]

def get_transactions(bank_num, birthday, password, days=30,
                     PHANTOM_PATH=None,
                     LOG_PATH=os.path.devnull,
                     cache=False,
                     headless=True):
    bank_num = str(bank_num).replace('-', '')
    birthday = str(birthday)
    password = str(password)
    days = int(days)

    # Load templates relative to this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(current_dir, 'assets')
    templates = {}
    for d in range(10):
        templates[d] = Image.open(os.path.join(assets_dir, f"{d}.png"))

    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # Fallback detection for Brave Browser on macOS
    brave_path = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
    if os.path.exists(brave_path):
        chrome_options.binary_location = brave_path

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get('https://spib.wooribank.com/pib/Dream?withyou=CMSPD0010')
        time.sleep(2)

        # Dismiss alerts (e.g. security install prompt)
        for _ in range(5):
            try:
                alert = driver.switch_to.alert
                alert.dismiss()
                time.sleep(0.5)
            except:
                break

        # Enter account number
        acc_input = driver.find_element(By.ID, 'pup01')
        acc_input.clear()
        acc_input.send_keys(bank_num)

        # Helper to enter via virtual keypad
        def enter_via_keypad(input_id, layout_id, value_str):
            input_el = driver.find_element(By.ID, input_id)
            input_el.click()
            time.sleep(1)

            img_el = driver.find_element(By.CSS_SELECTOR, f"#{layout_id} img")
            img_png = img_el.screenshot_as_png
            keypad_img = Image.open(BytesIO(img_png))

            digit_map = {}
            for key in keys_info:
                crop = keypad_img.crop(key["coords"])
                min_diff = 9999
                matched_digit = None
                for d, t_img in templates.items():
                    diff = rmsdiff(crop, t_img)
                    if diff < min_diff:
                        min_diff = diff
                        matched_digit = d
                if min_diff < 15:
                    digit_map[str(matched_digit)] = key["center"]

            for char in value_str:
                if char in digit_map:
                    center = digit_map[char]
                    offset_x = center[0] - 157.5
                    offset_y = center[1] - 135.5
                    action = ActionChains(driver)
                    action.move_to_element_with_offset(img_el, offset_x, offset_y).click().perform()
                    time.sleep(0.5)
                else:
                    raise Exception(f"Digit {char} not found in virtual keypad mapping!")

        enter_via_keypad('pup03', 'Tk_pup03_layoutSingle', birthday)
        enter_via_keypad('pup02', 'Tk_pup02_layoutSingle', password)
        time.sleep(1)

        # Find the submit button and click it
        clicked = False
        try:
            links = driver.find_elements(By.TAG_NAME, 'a')
            for l in links:
                onclick = l.get_attribute('onclick') or ''
                text = l.text.strip()
                if 'doSubmit' in onclick or text == '확인':
                    l.click()
                    clicked = True
                    break
        except Exception:
            pass

        if not clicked:
            submit_btn = driver.find_element(By.CSS_SELECTOR, 'a.btn-pack.btn-type-3c')
            submit_btn.click()

        time.sleep(3)

        # Dismiss alerts on post-submit page
        for _ in range(5):
            try:
                alert = driver.switch_to.alert
                alert.dismiss()
                time.sleep(0.5)
            except:
                break

        # Query transaction history for specified days
        end_dt = datetime.datetime.now()
        start_dt = end_dt - datetime.timedelta(days=days)
        start_str = start_dt.strftime('%Y%m%d')
        end_str = end_dt.strftime('%Y%m%d')

        driver.execute_script(f"document.getElementById('INQ_STA_DT').value = '{start_str}';")
        driver.execute_script(f"document.getElementById('INQ_END_DT').value = '{end_str}';")

        # Click the Inquiry (조회) button
        inquiry_clicked = False
        try:
            inquiry_btn = driver.find_element(By.CSS_SELECTOR, "input[value='조회']")
            inquiry_btn.click()
            inquiry_clicked = True
        except Exception:
            pass

        if not inquiry_clicked:
            inquiry_btn = driver.find_element(By.XPATH, "//input[@value='조회']")
            inquiry_btn.click()

        time.sleep(3)

        # Dismiss alerts on transaction list page
        for _ in range(5):
            try:
                alert = driver.switch_to.alert
                alert.dismiss()
                time.sleep(0.5)
            except:
                break

        # Parse transaction list from page source
        soup = bs(driver.page_source, 'html.parser')
        table = soup.select_one('table.tbl-type-1')
        if not table:
            return []

        rows = table.select('tbody tr')
        transaction_list = []
        for row in rows:
            tds = row.select('td')
            if len(tds) < 7:
                continue

            a_tag = tds[0].select_one('a')
            if not a_tag:
                continue
            date_text = a_tag.text.strip()
            date = parser.parse(date_text)

            brief = tds[1].text.strip()
            detail = tds[2].text.strip()
            transaction_by = detail if detail else brief

            w_text = tds[3].text.replace(',', '').strip()
            d_text = tds[4].text.replace(',', '').strip()

            withdrawal = int(w_text) if w_text else 0
            deposit = int(d_text) if d_text else 0

            amount = -withdrawal if withdrawal else deposit

            bal_text = tds[5].text.replace(',', '').strip()
            balance = int(bal_text) if bal_text else 0

            transaction_list.append({
                'date': date,
                'amount': amount,
                'balance': balance,
                'transaction_by': transaction_by
            })

        return transaction_list

    finally:
        driver.quit()
