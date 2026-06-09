import os

from simple_bank_korea import get_transactions


env = {}
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if '=' in line:
                k, v = line.strip().split('=', 1)
                env[k] = v.strip()

bank_num = env.get('HANA_ACCOUNT', '')
password = env.get('HANA_PASSWORD', '')
birthday = env.get('HANA_BIRTHDAY', '')

print('Running Hana get_transactions using usage pattern:')
print('  using HANA_ACCOUNT / HANA_BIRTHDAY / HANA_PASSWORD from .env')

transaction_list = get_transactions(
    bank_name='hana',
    bank_num=bank_num,
    birthday=birthday,
    password=password,
    days=30,
)

print('\n--- Hana Transactions Result ---')
for trs in transaction_list:
    print(trs.get('date'), trs.get('amount'), trs.get('transaction_by'), trs.get('balance'))
