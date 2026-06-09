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

## Usage

Import the unified `get_transactions` function from `simple_bank_korea`:

```python
from simple_bank_korea import get_transactions

# bank_name can be either 'kb' (or 'kookmin') or 'woori'
transaction_list = get_transactions(
    bank_name='woori', 
    bank_num='REDACTED',
    birthday='900101',
    password='1234',
    days=30,  # Optional, default is 30
    headless=True  # Optional, default is True (Woori only)
)

for trs in transaction_list:
    print(trs['date'], trs['amount'], trs['transaction_by'], trs['balance'])
```

---

## Args & Returns

### Required Arguments
- `bank_name`: Bank code to crawl. Set to `'kb'` (or `'kookmin'`) or `'woori'`. (String)
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
        'date': datetime.datetime(2026, 6, 9, 13, 28, 15),
        'amount': -10000,
        'balance': 0,
        'transaction_by': '김철수'
    },
    {
        'date': datetime.datetime(2026, 6, 9, 13, 27, 6),
        'amount': 10000,
        'balance': 10000,
        'transaction_by': '홍길동'
    }
]
```

---

## Update Log

#### 0.3.5 (2026-06-09)
- **Doc**: Simplify README by consolidating examples to only use Woori Bank and adding comments about alternative `bank_name` choices.
- **API**: Simplify `get_transactions` function signature by removing backward compatibility fallback defaults and `bank` parameter alias.

#### 0.3.4 (2026-06-09)
- **API**: Rename unified function parameter to `bank_name` and define `__all__` to only export `get_transactions`.

#### 0.3.3 (2026-06-09)
- **Doc**: Update README to import and use the unified `get_transactions` function from the top-level package.

#### 0.3.2 (2026-06-09)
- **Doc**: Add example output results for Kookmin Bank and Woori Bank transaction queries.

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

