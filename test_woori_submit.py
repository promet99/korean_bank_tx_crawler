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
                env[k] = v

bank_num = env.get('WOORI_ACCOUNT', '')
birthday = env.get('WOORI_BIRTHDAY', '')
password = env.get('WOORI_PASSWORD', '')

print(f"Testing Woori Bank submit with:")
print(f"  Account: {bank_num}")
print(f"  Birthday: {birthday}")

def rmsdiff(im1, im2):
    im1 = im1.convert('RGBA')
    im2 = im2.convert('RGBA')
    h = ImageChops.difference(im1, im2).histogram()
    return math.sqrt(reduce(operator.add,
                            map(lambda h, i: h * (i ** 2), h, range(256))
                            ) / (float(im1.size[0]) * im1.size[1]))

# Coordinates of the 12 keys
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

# Load templates
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
    print('Entered account number')

    # Helper function to enter a value via virtual keypad
    def enter_via_keypad(input_id, layout_id, value_str):
        # Click input to open keypad
        input_el = driver.find_element(By.ID, input_id)
        input_el.click()
        time.sleep(1)

        # Take screenshot of the keypad image
        img_el = driver.find_element(By.CSS_SELECTOR, f"#{layout_id} img")
        img_png = img_el.screenshot_as_png
        keypad_img = Image.open(BytesIO(img_png))

        # Map each digit to center coordinates
        digit_map = {}
        for key in keys_info:
            crop = keypad_img.crop(key["coords"])
            # Compare crop with templates
            min_diff = 9999
            matched_digit = None
            for d, t_img in templates.items():
                diff = rmsdiff(crop, t_img)
                if diff < min_diff:
                    min_diff = diff
                    matched_digit = d
            if min_diff < 15:
                digit_map[str(matched_digit)] = key["center"]

        print(f"Mapped digits for {input_id}: {list(digit_map.keys())}")

        # Click the keys in sequence
        for char in value_str:
            if char in digit_map:
                center = digit_map[char]
                # ActionChains offset in Selenium is relative to center of element
                # For move_to_element_with_offset: moves to center of element first, then adds offsets.
                # Since image is 315x271, center of element is at (157.5, 135.5).
                # So we calculate offsets relative to center.
                offset_x = center[0] - 157.5
                offset_y = center[1] - 135.5
                action = ActionChains(driver)
                action.move_to_element_with_offset(img_el, offset_x, offset_y).click().perform()
                print(f"  Clicked {char} at offset ({offset_x}, {offset_y})")
                time.sleep(0.5)
            else:
                raise Exception(f"Digit {char} not found in virtual keypad mapping!")

    # Enter birthday
    enter_via_keypad('pup03', 'Tk_pup03_layoutSingle', birthday)
    print('Entered birthday')

    # Enter password
    enter_via_keypad('pup02', 'Tk_pup02_layoutSingle', password)
    print('Entered password')

    # Submit form
    submit_btn = driver.find_element(By.CSS_SELECTOR, 'a.btn-pack.btn-type-3c')
    submit_btn.click()
    print('Clicked submit')
    time.sleep(3)

    # Save and print resulting page source details
    print('Current URL:', driver.current_url)
    page_source = driver.page_source
    with open('woori_result.html', 'w', encoding='utf-8') as f:
        f.write(page_source)
    print('Saved woori_result.html')

finally:
    driver.quit()
