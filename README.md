# Korean Bank Tx Crawler [![PyPI version](https://badge.fury.io/py/korean-bank-tx-crawler.svg)](https://badge.fury.io/py/korean-bank-tx-crawler)

> **Forked from [beomi/simple_bank_korea](https://github.com/beomi/simple_bank_korea)**

## Simplest Transaction Crawler for Korean Banks

Currently supports:
- **KB국민은행 (Kookmin Bank)**
- **우리은행 (Woori Bank)**

> [!WARNING]
> **Legal Disclaimer**: This library is for educational purposes only. Automated crawling of banking transactions may violate the bank's terms of service and/or local regulations. Sensitive credentials (account numbers, passwords, and birthdates) are processed entirely on your local machine, but handling them carries inherent security risks. The authors and contributors assume no liability for financial loss, account suspension, or security breaches. Use at your own risk.

### Requirements

- `beautifulsoup4`
- `requests`
- `python-dateutil`
- `pillow`
- `selenium`
- `webdriver-manager`
- Chrome or Brave Browser installed on the system (for virtual keypad template matching)

## Install

Install package with pip:

```bash
pip install -U korean_bank_tx_crawler
```

## Before Use

You must activate the **'빠른조회' (Speed Inquiry)** service for each bank account. You can only query accounts that have been registered for this service.

- **KB (Kookmin Bank)**: Quick inquiry can be activated on the KB Internet Banking site.
- **Woori Bank**: Quick inquiry can be activated on the Woori Internet Banking site.

---

## KB (Kookmin Bank) Usage

Import the KB-specific transaction function:

```python
from simple_bank_korea.kb import get_transactions

# get_transactions returns a list of transaction dicts
transaction_list = get_transactions(
    bank_num='47380204123456',
    birthday='941021',
    password='5432',
    days=30  # Optional, default is 30
)

for trs in transaction_list:
    print(trs['date'], trs['amount'], trs['transaction_by'], trs['balance'])
```

---

## Woori Bank Usage

Import the Woori-specific transaction function:

```python
from simple_bank_korea.woori import get_transactions

# get_transactions returns a list of transaction dicts using headless browser automation
transaction_list = get_transactions(
    bank_num='REDACTED',
    birthday='900101',
    password='1234',
    days=30,  # Optional, default is 30
    headless=True  # Optional, default is True
)

for trs in transaction_list:
    print(trs['date'], trs['amount'], trs['transaction_by'], trs['balance'])
```

---

## Args & Returns

### Required Arguments
- `bank_num`: Your bank account number. (String)
- `birthday`: Your birthday with birth year (e.g., if 1994/10/21, use `'941021'`), 6 digits. (String)
- `password`: Your 4-digit bank account password. (String)

### Optional Arguments
- `days`: Number of days to retrieve transactions for. Default is `30`. (Integer)
- `headless`: Whether to run Chrome/Brave in headless mode (Woori only). Default is `True`. (Boolean)

### Return Types
Returns a `list` of transaction dictionaries. Each dictionary contains:
- `date`: `datetime` object representing the transaction date and time.
- `amount`: `int` (positive for deposit, negative for withdrawal).
- `balance`: `int` representing the balance after transaction.
- `transaction_by`: `str` representing the sender or transaction description.

#### Example Result
```python
[
    {
        'date': datetime.datetime(2026, 5, 8, 0, 41, 52),
        'amount': -27300,
        'balance': 125000,
        'transaction_by': '박상준'
    },
    {
        'date': datetime.datetime(2026, 5, 6, 15, 21, 31),
        'amount': 27300,
        'balance': 152300,
        'transaction_by': '(주)알라딘커뮤니케'
    }
]
```

---

## Update Log

#### 0.3.0 (2026-06-09)
- **Feature**: Add support for **Woori Bank** transaction crawling.
- **Mechanism**: Added virtual keypad digit recognition using template matching (`rmsdiff` on element cropped keypads) to work around SEED-128 mouse click coordinates requirement.
- **Dependencies**: Added `selenium` and `webdriver-manager` requirements.
- **Compatibility**: Automatic detection and fallback to Brave Browser on macOS.

#### 0.2.15 (2020-06-04)
- HotFix bugs on `setup.py`

#### 0.2.14 (2020-06-04)
- Fix bugs #4: (downloaded) phantomJS permission error

#### 0.2.13 (2020-06-04)
- Fix bugs when downloading phantomjs (Linux and macOS only).
- Add Guide (OS, Progress) when downloading phantomjs.

#### 0.2.10 (2017-11-11)
- Hot-fix: implicitly import to explicit relevant import to prevent `ImportError`.

