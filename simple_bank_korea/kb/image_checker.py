from io import StringIO, BytesIO
import base64
from PIL import Image
from PIL import ImageChops
import requests
from bs4 import BeautifulSoup as bs

import math, operator
from functools import reduce
import re
import os

CURRENT_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_keypad_img(PHANTOM_PATH=None, LOG_PATH=os.path.devnull):
    area_hash_list = []
    area_pattern = re.compile(r"'(\w+)'")

    session = requests.Session()
    headers = {
        'Pragma': 'no-cache',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.6,en;q=0.4,la;q=0.2,da;q=0.2',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
    }
    session.headers.update(headers)

    r = session.get('https://obank.kbstar.com/quics?page=C025255&cc=b028364:b028702&QSL=F')

    JSESSIONID = session.cookies.get('JSESSIONID') or ''
    QSID = session.cookies.get('QSID') or ''

    soup = bs(r.text, 'html.parser')

    keypad_useyn_el = soup.select('input[id*="KEYPAD_USEYN"]')
    KEYPAD_USEYN = keypad_useyn_el[0].get('value') if keypad_useyn_el else ''

    # Extract the hex-encoded HTML string inside vKpd.hex2bin
    match = re.search(r'vKpd\.hex2bin\(\"([0-9a-fA-F]+)\"\)', r.text)
    if not match:
        raise Exception("Failed to locate hex-encoded keypad HTML")

    hex_str = match.group(1)
    decoded_html = bytes.fromhex(hex_str).decode('utf-8')
    keypad_soup = bs(decoded_html, 'html.parser')

    quics_img = keypad_soup.select('img')
    if not quics_img:
        raise Exception("Failed to locate keypad image inside decoded HTML")

    img_url = 'https://obank.kbstar.com' + quics_img[0].get('src')
    keymap = quics_img[0].get('usemap').replace('#divKeypad', '')[:-3]

    area_list = keypad_soup.select('map > area')

    for area in area_list:
        onmousedown = area.get('onmousedown') or ''
        re_matched = area_pattern.findall(onmousedown)
        if re_matched:
            area_hash_list.append(re_matched[0])

    r_img = session.get(img_url)
    real = Image.open(BytesIO(r_img.content)).convert('RGBA')

    # Get list
    num_sequence = _get_keypad_num_list(real)

    PW_DIGITS = {}
    # FIXED
    PW_DIGITS['1'] = area_hash_list[0]
    PW_DIGITS['2'] = area_hash_list[1]
    PW_DIGITS['3'] = area_hash_list[2]
    PW_DIGITS['4'] = area_hash_list[3]
    PW_DIGITS['6'] = area_hash_list[5]

    # Floating..
    for idx, num in enumerate(num_sequence):
        if idx == 0:
            PW_DIGITS[str(num)] = area_hash_list[4]
        elif idx == 1:
            PW_DIGITS[str(num)] = area_hash_list[6]
        elif idx == 2:
            PW_DIGITS[str(num)] = area_hash_list[7]
        elif idx == 3:
            PW_DIGITS[str(num)] = area_hash_list[8]
        elif idx == 4:
            PW_DIGITS[str(num)] = area_hash_list[9]

    return {
        'JSESSIONID': JSESSIONID,
        'QSID': QSID,
        'KEYMAP': keymap,
        'PW_DIGITS': PW_DIGITS,
        'KEYPAD_USEYN': KEYPAD_USEYN
    }


def rmsdiff(im1, im2):
    h = ImageChops.difference(im1, im2).histogram()
    return math.sqrt(reduce(operator.add,
                            map(lambda h, i: h * (i ** 2), h, range(256))
                            ) / (float(im1.size[0]) * im1.size[1]))


def _get_keypad_num_list(img):
    # 57x57 box
    box_5th = Image.open(os.path.join(CURRENT_PACKAGE_DIR, 'assets', '5.png'))
    box_7th = Image.open(os.path.join(CURRENT_PACKAGE_DIR, 'assets', '7.png'))
    box_8th = Image.open(os.path.join(CURRENT_PACKAGE_DIR, 'assets', '8.png'))
    box_9th = Image.open(os.path.join(CURRENT_PACKAGE_DIR, 'assets', '9.png'))
    box_0th = Image.open(os.path.join(CURRENT_PACKAGE_DIR, 'assets', '0.png'))

    box_dict = {
        5: box_5th,
        7: box_7th,
        8: box_8th,
        9: box_9th,
        0: box_0th,
    }

    # 57x57 box
    crop_5th = img.crop(box=(74, 99, 131, 156))
    crop_7th = img.crop(box=(16, 157, 73, 214))
    crop_8th = img.crop(box=(74, 157, 131, 214))
    crop_9th = img.crop(box=(132, 157, 189, 214))
    crop_0th = img.crop(box=(74, 215, 131, 272))

    crop_list = [crop_5th, crop_7th, crop_8th, crop_9th, crop_0th]

    keypad_num_list = []

    for idx, crop in enumerate(crop_list):
        for key, box in box_dict.items():
            try:
                diff = rmsdiff(crop, box)
                if diff < 13:
                    keypad_num_list += [key]
            except Exception as e:
                print(e)
    return keypad_num_list


if __name__ == '__main__':
    print(get_keypad_img('phantomjs'))  # PATH to phantomjs
    print(_get_keypad_num_list())
