# Korean Bank Tx Crawler [![PyPI version](https://badge.fury.io/py/korean-bank-tx-crawler.svg)](https://badge.fury.io/py/korean-bank-tx-crawler)

한국 은행의 `빠른조회` 페이지를 자동으로 열어서
거래내역을 가져오는 파이썬 라이브러리입니다.

원본 프로젝트: [beomi/simple_bank_korea](https://github.com/beomi/simple_bank_korea)

## 지원 은행

- `kb` : KB국민은행
- `hana` : 하나은행
- `woori` : 우리은행

## 설치

```bash
pip install -U korean_bank_tx_crawler
```

## 필요한 것

1. 계좌가 해당 은행의 `빠른조회` 서비스에 등록되어 있어야 합니다.
2. PC에 `Chrome` 또는 `Brave Browser`가 설치되어 있어야 합니다.
3. 계좌번호, 생년월일 6자리, 계좌 비밀번호 4자리가 필요합니다.

## 바로 사용하기

```python
from simple_bank_korea import get_transactions

transactions = get_transactions(
    bank_name='hana',
    bank_num='12345678901234',
    birthday='900101',
    password='1234',
    days=30,
    headless=True,
)

for tx in transactions:
    print(tx['date'], tx['amount'], tx['transaction_by'], tx['balance'])
```

## 인자 설명

- `bank_name`
  - `kb`, `kookmin`, `국민`, `국민은행`
  - `hana`, `hanabank`, `하나`, `하나은행`
  - `woori`, `wooribank`, `우리`, `우리은행`
- `bank_num`: 계좌번호 문자열
- `birthday`: 생년월일 6자리 문자열. 예: `900101`
- `password`: 계좌 비밀번호 4자리 문자열
- `days`: 최근 몇 일 거래내역을 가져올지. 기본값 `30`
- `headless`: 브라우저 화면 없이 실행할지 여부. 기본값 `True`

## 반환값

리스트를 반환합니다.
각 원소는 아래 형태의 딕셔너리입니다.

```python
{
    'date': datetime.datetime(2026, 6, 10, 9, 30, 0),
    'amount': -10000,
    'balance': 250000,
    'transaction_by': '카카오페이'
}
```

- `amount`
  - 입금: 양수
  - 출금: 음수

## `.env`로 테스트하기

예시:

```env
HANA_ACCOUNT=12345678901234
HANA_BIRTHDAY=900101
HANA_PASSWORD=1234
```

실행:

```bash
./venv/bin/python run_usage_hana.py
```

## 주의

- 이 라이브러리는 은행 웹페이지 구조가 바뀌면 바로 깨질 수 있습니다.
- 하나은행, 우리은행은 가상 키패드를 사용하므로 Selenium 브라우저 자동화에 의존합니다.
- 계좌가 `빠른조회` 대상이 아니면 은행에서 조회를 거절합니다.
- 민감한 정보는 로컬 환경에서만 다루세요.

## 이번 버전 변경

`0.3.6`

- 하나은행 빠른조회 지원 추가
- 하나은행 가상 키패드 입력 자동화 추가
- 패키지에 하나은행 키패드 템플릿 포함

## 면책

이 프로젝트는 학습 및 개인 자동화 용도입니다.
은행 이용약관이나 관련 규정을 위반할 수 있습니다.
사용으로 인해 발생하는 문제는 사용자 책임입니다.
