import datetime
import json
import math
import operator
import os
import time
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
from webdriver_manager.chrome import ChromeDriverManager

HANA_URL = 'https://www.kebhana.com/flex/quick/quickService.do?subMenu=1'
HANA_XHR_URL = '/quick_service/inquiryAcct02_01.do'


def rmsdiff(im1, im2):
    im1 = im1.convert('RGBA')
    im2 = im2.convert('RGBA')
    h = ImageChops.difference(im1, im2).histogram()
    return math.sqrt(
        reduce(operator.add, map(lambda h, i: h * (i ** 2), h, range(256)))
        / (float(im1.size[0]) * im1.size[1])
    )


def _load_digit_templates(assets_dir):
    return {
        str(digit): Image.open(os.path.join(assets_dir, f'{digit}.png'))
        for digit in range(10)
    }


def _build_digit_map(keypad_img, keys, templates, threshold):
    digit_map = {}
    for key in keys:
        if key.get('name'):
            continue

        left = min(key['xpoints'])
        right = max(key['xpoints'])
        top = min(key['ypoints'])
        bottom = max(key['ypoints'])
        crop = keypad_img.crop((left, top, right, bottom))

        best_digit = None
        best_diff = float('inf')
        for digit, template in templates.items():
            diff = rmsdiff(crop, template)
            if diff < best_diff:
                best_digit = digit
                best_diff = diff

        if best_digit is not None and best_diff < threshold and best_digit not in digit_map:
            digit_map[best_digit] = {
                'center_x': (left + right) / 2.0,
                'center_y': (top + bottom) / 2.0,
                'diff': best_diff,
            }

    return digit_map


def _click_transkey_chars(driver, image_el, digit_map, value):
    rect = driver.execute_script(
        'const r = arguments[0].getBoundingClientRect();'
        'return {width: r.width, height: r.height};',
        image_el,
    )

    for char in value:
        if char not in digit_map:
            raise ValueError(f'TransKey digit {char} was not found in keypad mapping.')

        key = digit_map[char]
        offset_x = key['center_x'] - (rect['width'] / 2.0)
        offset_y = key['center_y'] - (rect['height'] / 2.0)
        ActionChains(driver).move_to_element_with_offset(image_el, offset_x, offset_y).click().perform()
        time.sleep(0.25)


def _close_transkey(driver, transkey_name):
    driver.execute_script(
        '''
        var tk = window.transkey && window.transkey[arguments[0]];
        if (tk && typeof tk.close === 'function') {
            tk.close();
        }
        ''',
        transkey_name,
    )
    time.sleep(0.4)


def _enter_account_number(driver, bank_num, templates):
    driver.find_element(By.ID, 'acctNo').click()
    time.sleep(1.5)

    image_el = driver.find_element(By.CSS_SELECTOR, '#Tk_acctNo_layout #imgTwinLower')
    keypad_img = Image.open(BytesIO(image_el.screenshot_as_png))
    keys = driver.execute_script('return window.transkey.Tk_acctNo.keys;')
    digit_map = _build_digit_map(keypad_img, keys, templates, threshold=20)
    _click_transkey_chars(driver, image_el, digit_map, bank_num)
    _close_transkey(driver, 'Tk_acctNo')


def _enter_numeric_secret(driver, field_id, templates, value):
    driver.find_element(By.ID, field_id).click()
    time.sleep(1.5)

    image_el = driver.find_element(By.CSS_SELECTOR, f'#Tk_{field_id}_layoutSingle #imgSingle')
    keypad_img = Image.open(BytesIO(image_el.screenshot_as_png))
    keys = driver.execute_script(f'return window.transkey.Tk_{field_id}.keys;')
    digit_map = _build_digit_map(keypad_img, keys, templates, threshold=20)
    _click_transkey_chars(driver, image_el, digit_map, value)
    _close_transkey(driver, f'Tk_{field_id}')


def _compute_hana_account_type(bank_num):
    acct_no = str(bank_num)
    acct_kind = 1

    if len(acct_no) == 14:
        acct_kind = acct_no[12:14]
    elif len(acct_no) == 12:
        prefix = acct_no[:2]
        if prefix in ('73', '74'):
            acct_kind = 13
        elif prefix in ('64', '65'):
            acct_kind = 31
        else:
            acct_kind = 1
    elif len(acct_no) == 11:
        subject = acct_no[3:5]
        if subject in ('86', '90'):
            acct_kind = 13
        elif subject in ('11', '26', '13', '33', '18', '38', '19', '22'):
            acct_kind = 1
        else:
            acct_kind = 1

    if 'J' in acct_no:
        acct_kind = 31

    acct_kind = int(acct_kind)
    if acct_kind in (1, 2, 4, 5, 7, 8):
        return '01'
    if acct_kind in (11, 21, 22, 23, 24, 25, 26, 15):
        return '02'
    if acct_kind in (31, 32, 33, 34, 38):
        return '03'
    if acct_kind in (13, 14, 36):
        return '04'
    if acct_kind in (41, 42, 44, 47):
        return '05'
    if acct_kind in (50, 52, 53, 55, 56, 57, 58):
        return '06'
    if len(acct_no) == 14 and acct_no[12:14] == '38':
        return '20'
    return '09'


def _install_xhr_capture(driver):
    driver.execute_script(
        '''
        window.__hana_xhr_log = [];
        if (!window.__hana_xhr_capture_installed) {
            const originalOpen = XMLHttpRequest.prototype.open;
            const originalSend = XMLHttpRequest.prototype.send;

            XMLHttpRequest.prototype.open = function(method, url) {
                this.__hana_method = method;
                this.__hana_url = url;
                return originalOpen.apply(this, arguments);
            };

            XMLHttpRequest.prototype.send = function(body) {
                this.__hana_body = body;
                this.addEventListener('load', function() {
                    window.__hana_xhr_log.push({
                        method: this.__hana_method,
                        url: this.__hana_url,
                        status: this.status,
                        body: this.__hana_body,
                        response: this.responseText || '',
                    });
                });
                return originalSend.apply(this, arguments);
            };

            window.__hana_xhr_capture_installed = true;
        }
        '''
    )


def _wait_for_inquiry_response(driver, timeout=20):
    end_time = time.time() + timeout
    while time.time() < end_time:
        response = driver.execute_script(
            '''
            var logs = window.__hana_xhr_log || [];
            for (var i = logs.length - 1; i >= 0; i--) {
                if ((logs[i].url || '').indexOf(arguments[0]) >= 0) {
                    return logs[i];
                }
            }
            return null;
            ''',
            HANA_XHR_URL,
        )
        if response:
            return response
        time.sleep(0.5)
    raise TimeoutError('Timed out waiting for Hana inquiry response.')


def _parse_error_response(response_text):
    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError:
        return None

    if isinstance(payload, list) and payload:
        message = payload[0].get('errorMessage') or 'Unknown Hana quick inquiry error.'
        message = ' '.join(part.strip() for part in message.splitlines() if part.strip())
        return message
    return None


def _find_transaction_table(soup):
    for table in soup.select('table'):
        headers = [
            th.get_text(' ', strip=True)
            for th in table.select('thead th, tr:first-child th')
        ]
        header_text = ' '.join(headers)
        if '잔액' in header_text and ('입금' in header_text or '출금' in header_text):
            return table, headers
    return None, []


def _match_header_index(headers, keywords):
    for idx, header in enumerate(headers):
        normalized = header.replace(' ', '')
        for keyword in keywords:
            if keyword in normalized:
                return idx
    return None


def _clean_amount(text):
    cleaned = text.replace(',', '').replace('원', '').replace('+', '').replace('-', '').strip()
    if not cleaned:
        return 0
    return int(cleaned)


def _parse_transactions_html(html):
    soup = bs(html, 'html.parser')
    table, headers = _find_transaction_table(soup)
    if table is None:
        raise ValueError('Hana inquiry response did not contain a recognizable transaction table.')

    date_idx = _match_header_index(headers, ('거래일시', '거래일자', '기장일시', '일시', '일자'))
    summary_idx = _match_header_index(headers, ('적요', '내용', '거래내용', '거래처'))
    withdrawal_idx = _match_header_index(headers, ('출금',))
    deposit_idx = _match_header_index(headers, ('입금',))
    balance_idx = _match_header_index(headers, ('잔액',))
    amount_idx = _match_header_index(headers, ('거래금액',))

    rows = table.select('tbody tr') or table.select('tr')[1:]
    transactions = []
    for row in rows:
        cells = [td.get_text(' ', strip=True) for td in row.select('td')]
        if not cells:
            continue

        if date_idx is None or date_idx >= len(cells):
            continue

        date_text = cells[date_idx]
        try:
            date = parser.parse(date_text)
        except (ValueError, TypeError):
            continue

        transaction_by = ''
        if summary_idx is not None and summary_idx < len(cells):
            transaction_by = cells[summary_idx]

        if amount_idx is not None and amount_idx < len(cells):
            amount_text = cells[amount_idx].replace(',', '').strip()
            amount = int(amount_text) if amount_text else 0
        else:
            withdrawal = _clean_amount(cells[withdrawal_idx]) if withdrawal_idx is not None and withdrawal_idx < len(cells) else 0
            deposit = _clean_amount(cells[deposit_idx]) if deposit_idx is not None and deposit_idx < len(cells) else 0
            amount = -withdrawal if withdrawal else deposit

        balance = _clean_amount(cells[balance_idx]) if balance_idx is not None and balance_idx < len(cells) else 0
        transactions.append({
            'date': date,
            'amount': amount,
            'balance': balance,
            'transaction_by': transaction_by,
        })

    if not transactions:
        raise ValueError('Hana inquiry response contained a transaction table, but no rows were parsed.')

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
    days = int(days)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    account_templates = _load_digit_templates(os.path.join(current_dir, 'assets', 'account'))
    numeric_templates = _load_digit_templates(os.path.join(current_dir, 'assets', 'numeric'))

    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    brave_path = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
    if os.path.exists(brave_path):
        chrome_options.binary_location = brave_path

    service = Service(ChromeDriverManager(chrome_type='brave').install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(HANA_URL)
        time.sleep(3)
        _install_xhr_capture(driver)

        _enter_account_number(driver, bank_num, account_templates)
        _enter_numeric_secret(driver, 'acctPw', numeric_templates, password)
        _enter_numeric_secret(driver, 'bkfgResRegNo', numeric_templates, birthday)

        end_dt = datetime.datetime.now()
        max_span = 730
        start_dt = end_dt - datetime.timedelta(days=min(days, max_span))
        driver.execute_script(
            '''
            document.getElementById('inqStrDt').value = arguments[0];
            document.getElementById('inqEndDt').value = arguments[1];
            ''',
            start_dt.strftime('%Y-%m-%d'),
            end_dt.strftime('%Y-%m-%d'),
        )

        driver.execute_script(
            '''
            var form = document.forms['frmQuickInquiry'];
            form.maxRowCount && (form.maxRowCount.value = '700');
            pbk.quickService.acctInquiry.submitInquiry(form, '1', 'KOR');
            '''
        )

        response = _wait_for_inquiry_response(driver)
        error_message = _parse_error_response(response.get('response', ''))
        if error_message:
            raise ValueError(error_message)

        return _parse_transactions_html(response.get('response', ''))
    finally:
        driver.quit()
