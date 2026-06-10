import os
import time
import math
import operator
import datetime
from functools import reduce
from io import BytesIO

from bs4 import BeautifulSoup as bs
from dateutil import parser
from PIL import Image, ImageChops
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def rmsdiff(im1, im2):
    im1 = im1.convert('RGBA')
    im2 = im2.convert('RGBA')
    h = ImageChops.difference(im1, im2).histogram()
    return math.sqrt(
        reduce(operator.add, map(lambda h, i: h * (i ** 2), h, range(256)))
        / (float(im1.size[0]) * im1.size[1])
    )


keys_info = [
    {"index": 0,  "coords": [161, 74,  205, 116], "center": (183, 95)},
    {"index": 1,  "coords": [208, 74,  252, 116], "center": (230, 95)},
    {"index": 2,  "coords": [208, 120, 252, 162], "center": (230, 141)},
    {"index": 3,  "coords": [208, 166, 252, 208], "center": (230, 187)},
    {"index": 4,  "coords": [208, 212, 252, 254], "center": (230, 233)},
    {"index": 5,  "coords": [161, 212, 205, 254], "center": (183, 233)},
    {"index": 6,  "coords": [114, 212, 158, 254], "center": (136, 233)},
    {"index": 7,  "coords": [67,  212, 111, 254], "center": (89,  233)},
    {"index": 8,  "coords": [67,  166, 111, 208], "center": (89,  187)},
    {"index": 9,  "coords": [67,  120, 111, 162], "center": (89,  141)},
    {"index": 10, "coords": [67,  74,  111, 116], "center": (89,  95)},
    {"index": 11, "coords": [114, 74,  158, 116], "center": (136, 95)},
]

# Ordered fallback selectors for each step — first match wins.
# Extend these lists when the bank updates their page without touching logic.
_DATE_FIELD_IDS = [
    ('INQ_STA_DT', 'INQ_END_DT'),
    ('inqStaDt',   'inqEndDt'),
    ('startDt',    'endDt'),
    ('fromDate',   'toDate'),
]

_INQUIRY_BUTTON_SELECTORS = [
    (By.CSS_SELECTOR, "input[type='submit'][value='조회']"),
    (By.CSS_SELECTOR, "input[value='조회']"),
    (By.XPATH,        "//input[@value='조회']"),
    (By.XPATH,        "//button[normalize-space()='조회']"),
    (By.XPATH,        "//a[normalize-space()='조회']"),
]

_TABLE_SELECTORS = [
    'table.tbl-type-1',
    'table.tbl-type',
    'table[summary]',
]


def _dismiss_alerts(driver, max_alerts=5):
    for _ in range(max_alerts):
        try:
            driver.switch_to.alert.dismiss()
            time.sleep(0.5)
        except Exception:
            break


def _wait_for_inquiry_form(driver, timeout=15):
    """Wait for the date-range form after login.

    Tries known element IDs/names so a single renamed field doesn't break
    everything — returns the (start_id, end_id) pair that was found.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        for sta_id, end_id in _DATE_FIELD_IDS:
            for by, val in [(By.ID, sta_id), (By.NAME, sta_id),
                            (By.CSS_SELECTOR, f'input[name="{sta_id}"]')]:
                try:
                    driver.find_element(by, val)
                    return sta_id, end_id
                except Exception:
                    pass
        time.sleep(0.5)

    raise ValueError(
        "Timed out waiting for Woori inquiry date-range form after login. "
        f"Tried IDs: {[s for s, _ in _DATE_FIELD_IDS]}. "
        "Authentication may have failed, or the bank changed their selectors."
    )


def _set_date_range(driver, sta_id, end_id, start_str, end_str):
    """Set start/end date using the page's own calSetVal, with a direct
    value-assignment fallback for when the JS API changes."""
    for field_id, value in [(sta_id, start_str), (end_id, end_str)]:
        set_ok = driver.execute_script(
            """
            if (typeof calSetVal === 'function') {
                calSetVal(arguments[0], arguments[1]);
                return true;
            }
            return false;
            """,
            field_id, value,
        )
        if not set_ok:
            driver.execute_script(
                """
                var el = document.getElementById(arguments[0])
                      || document.querySelector('[name="' + arguments[0] + '"]');
                if (el) el.value = arguments[1];
                """,
                field_id, value,
            )


def _click_inquiry_button(driver):
    for by, selector in _INQUIRY_BUTTON_SELECTORS:
        try:
            driver.find_element(by, selector).click()
            return
        except Exception:
            pass
    raise ValueError(
        "Could not find the 조회 (inquiry) button. "
        f"Tried selectors: {[s for _, s in _INQUIRY_BUTTON_SELECTORS]}"
    )


def _parse_transactions(soup):
    """Parse the transaction table, deriving column indices from the header
    row so column reordering doesn't silently corrupt the output."""
    table = None
    for sel in _TABLE_SELECTORS:
        table = soup.select_one(sel)
        if table:
            break
    if not table:
        return []

    header_cells = table.select('thead th') or table.select('tr:first-child th')
    headers = [th.get_text(' ', strip=True) for th in header_cells]

    def _col(keywords):
        for i, h in enumerate(headers):
            if any(k in h for k in keywords):
                return i
        return None

    date_col       = _col(['거래일시', '거래일자', '일시', '일자'])
    brief_col      = _col(['적요'])
    detail_col     = _col(['기재내용', '내용'])
    withdrawal_col = _col(['찾으신금액', '출금'])
    deposit_col    = _col(['맡기신금액', '입금'])
    balance_col    = _col(['거래후잔액', '잔액'])

    transactions = []
    for row in table.select('tbody tr'):
        tds = row.select('td')
        if not tds:
            continue

        # Date — may be wrapped in an <a>
        if date_col is not None and date_col < len(tds):
            a = tds[date_col].select_one('a')
            date_text = (a or tds[date_col]).get_text(' ', strip=True)
        elif tds:
            a = tds[0].select_one('a')
            date_text = (a or tds[0]).get_text(' ', strip=True)
        else:
            continue

        try:
            date = parser.parse(date_text)
        except (ValueError, TypeError):
            continue

        def _int(col):
            if col is None or col >= len(tds):
                return 0
            return int(tds[col].get_text(' ', strip=True).replace(',', '').strip() or 0)

        withdrawal = _int(withdrawal_col)
        deposit    = _int(deposit_col)
        amount     = deposit - withdrawal

        balance = _int(balance_col)

        brief  = tds[brief_col].get_text(' ', strip=True)  if brief_col  is not None and brief_col  < len(tds) else ''
        detail = tds[detail_col].get_text(' ', strip=True) if detail_col is not None and detail_col < len(tds) else ''
        transaction_by = detail or brief

        transactions.append({
            'date': date,
            'amount': amount,
            'balance': balance,
            'transaction_by': transaction_by,
        })

    return transactions


def get_transactions(bank_num, birthday, password, days=30,
                     PHANTOM_PATH=None,
                     LOG_PATH=os.path.devnull,
                     cache=False,
                     headless=True):
    del PHANTOM_PATH, LOG_PATH, cache

    bank_num = str(bank_num).replace('-', '')
    birthday = str(birthday)
    password = str(password)
    days     = int(days)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir  = os.path.join(current_dir, 'assets')
    templates   = {d: Image.open(os.path.join(assets_dir, f'{d}.png')) for d in range(10)}

    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    brave_path = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
    if os.path.exists(brave_path):
        chrome_options.binary_location = brave_path

    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get('https://spib.wooribank.com/pib/Dream?withyou=CMSPD0010')
        time.sleep(2)
        _dismiss_alerts(driver)

        acc_input = driver.find_element(By.ID, 'pup01')
        acc_input.clear()
        acc_input.send_keys(bank_num)

        def enter_via_keypad(input_id, layout_id, value_str):
            driver.find_element(By.ID, input_id).click()
            time.sleep(1)

            img_el     = driver.find_element(By.CSS_SELECTOR, f'#{layout_id} img')
            keypad_img = Image.open(BytesIO(img_el.screenshot_as_png))

            digit_map = {}
            for key in keys_info:
                crop = keypad_img.crop(key['coords'])
                best_diff, best_digit = 9999, None
                for d, tmpl in templates.items():
                    diff = rmsdiff(crop, tmpl)
                    if diff < best_diff:
                        best_diff, best_digit = diff, d
                if best_diff < 15:
                    digit_map[str(best_digit)] = key['center']

            for char in value_str:
                if char not in digit_map:
                    raise ValueError(f"Digit '{char}' not found in Woori virtual keypad.")
                cx, cy = digit_map[char]
                ActionChains(driver).move_to_element_with_offset(
                    img_el, cx - 157.5, cy - 135.5
                ).click().perform()
                time.sleep(0.5)

        enter_via_keypad('pup03', 'Tk_pup03_layoutSingle', birthday)
        enter_via_keypad('pup02', 'Tk_pup02_layoutSingle', password)
        time.sleep(1)

        # Click the authentication submit button
        clicked = False
        for link in driver.find_elements(By.TAG_NAME, 'a'):
            onclick = link.get_attribute('onclick') or ''
            if 'doSubmit' in onclick or link.text.strip() == '확인':
                link.click()
                clicked = True
                break
        if not clicked:
            driver.find_element(By.CSS_SELECTOR, 'a.btn-pack.btn-type-3c').click()

        # Wait for navigation, then dismiss the recurring security alerts.
        # The sleep must precede the loop — without it the loop exits before
        # the alerts appear and they block subsequent JS execution.
        time.sleep(3)
        _dismiss_alerts(driver)

        # Fast-fail on authentication error page rather than waiting 15s.
        try:
            driver.find_element(By.ID, 'error-area-TopLayer')
            raise ValueError(
                "Woori bank returned an authentication error page. "
                "Check your credentials, or wait a few minutes if you've "
                "made several login attempts in a short period."
            )
        except ValueError:
            raise
        except Exception:
            pass

        sta_id, end_id = _wait_for_inquiry_form(driver)

        end_dt   = datetime.datetime.now()
        start_dt = end_dt - datetime.timedelta(days=days)
        _set_date_range(driver, sta_id, end_id,
                        start_dt.strftime('%Y%m%d'),
                        end_dt.strftime('%Y%m%d'))

        _click_inquiry_button(driver)

        time.sleep(3)
        _dismiss_alerts(driver)

        return _parse_transactions(bs(driver.page_source, 'html.parser'))

    finally:
        driver.quit()
