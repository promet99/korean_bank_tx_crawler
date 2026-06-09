import os
import time
import math
import operator
from functools import reduce
from PIL import Image, ImageChops
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
# Manually parse .env
env = {}
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if '=' in line:
                k, v = line.strip().split('=', 1)
                env[k] = v.strip()

bank_num = env.get('WOORI_ACCOUNT', '')
birthday = env.get('WOORI_BIRTHDAY', '')
password = env.get('WOORI_PASSWORD', '')

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

templates = {}
assets_dir = 'simple_bank_korea/woori/assets'
for d in range(10):
    templates[d] = Image.open(os.path.join(assets_dir, f"{d}.png"))

chrome_options = Options()
chrome_options.binary_location = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
chrome_options.add_argument('--headless')
chrome_options.add_argument('--window-size=1920,1080')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    driver.get('https://spib.wooribank.com/pib/Dream?withyou=CMSPD0010')
    time.sleep(2)

    # Dismiss alerts
    for _ in range(5):
        try:
            alert = driver.switch_to.alert
            print('Dismissing alert:', alert.text)
            alert.dismiss()
            time.sleep(0.5)
        except:
            break

    # Enter account number
    acc_input = driver.find_element(By.ID, 'pup01')
    acc_input.clear()
    acc_input.send_keys(bank_num)

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

    enter_via_keypad('pup03', 'Tk_pup03_layoutSingle', birthday)
    enter_via_keypad('pup02', 'Tk_pup02_layoutSingle', password)
    time.sleep(1)

    # Find the submit button
    try:
        # Let's list all links
        links = driver.find_elements(By.TAG_NAME, 'a')
        print(f"Total links found: {len(links)}")
        for l in links:
            onclick = l.get_attribute('onclick') or ''
            text = l.text.strip()
            if 'doSubmit' in onclick or text == '확인':
                print(f"Found match: Text='{text}', Onclick='{onclick}', Class='{l.get_attribute('class')}'")
                submit_btn = l
                submit_btn.click()
                print("Clicked submit button via link search!")
                break
        else:
            # Try finding via selector
            submit_btn = driver.find_element(By.CSS_SELECTOR, 'a.btn-pack.btn-type-3c')
            submit_btn.click()
            print("Clicked submit button via CSS selector!")
    except Exception as click_err:
        print("Error clicking submit button:", click_err)
        # Take error screenshot
        driver.save_screenshot('woori_error.png')
        with open('woori_error.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("Saved debug files 'woori_error.png' and 'woori_error.html'")
        raise click_err

    time.sleep(3)
    # Dismiss alerts on the new page
    for _ in range(5):
        try:
            alert = driver.switch_to.alert
            print('Dismissing post-submit alert:', alert.text)
            alert.dismiss()
            time.sleep(0.5)
        except:
            break

    print('Current URL after submit:', driver.current_url)
    with open('woori_result.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print('Saved woori_result.html')

    # Query transaction history for last 30 days
    import datetime
    days_to_query = 30
    end_dt = datetime.datetime.now()
    start_dt = end_dt - datetime.timedelta(days=days_to_query)
    start_str = start_dt.strftime('%Y%m%d')
    end_str = end_dt.strftime('%Y%m%d')
    print(f"Querying transactions from {start_str} to {end_str}")

    driver.execute_script(f"document.getElementById('INQ_STA_DT').value = '{start_str}';")
    driver.execute_script(f"document.getElementById('INQ_END_DT').value = '{end_str}';")

    # Click the Inquiry (조회) button
    try:
        inquiry_btn = driver.find_element(By.CSS_SELECTOR, "input[value='조회']")
        inquiry_btn.click()
        print("Clicked Inquiry button!")
    except Exception as e:
        print("Could not find input[value='조회'], trying fallback click:", e)
        # Try finding submit button in btn-area
        inquiry_btn = driver.find_element(By.XPATH, "//input[@value='조회']")
        inquiry_btn.click()
        print("Clicked Inquiry button via fallback!")

    time.sleep(3)
    # Dismiss alerts on transaction list page
    for _ in range(5):
        try:
            alert = driver.switch_to.alert
            print('Dismissing post-inquiry alert:', alert.text)
            alert.dismiss()
            time.sleep(0.5)
        except:
            break

    print('Current URL after inquiry submit:', driver.current_url)
    with open('woori_tx_result.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print('Saved woori_tx_result.html')

finally:
    driver.quit()
