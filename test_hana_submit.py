import os

from simple_bank_korea.hana.crawler import get_transactions


env = {}
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if '=' in line:
                k, v = line.strip().split('=', 1)
                env[k] = v

bank_num = env.get('HANA_ACCOUNT', '')
birthday = env.get('HANA_BIRTHDAY', '')
password = env.get('HANA_PASSWORD', '')

print('Testing Hana Bank submit with:')
print('  using HANA_ACCOUNT / HANA_BIRTHDAY / HANA_PASSWORD from .env')

transactions = get_transactions(
    bank_num=bank_num,
    birthday=birthday,
    password=password,
    days=30,
)

print(f'Returned {len(transactions)} transactions')
for transaction in transactions[:10]:
    print(transaction)
