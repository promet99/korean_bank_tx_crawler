import os
from simple_bank_korea.woori import get_transactions

# Manually parse .env to avoid extra dependencies
env = {}
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if '=' in line:
                k, v = line.strip().split('=', 1)
                env[k] = v.strip()

bank_num = env.get('WOORI_ACCOUNT', '')
password = env.get('WOORI_PASSWORD', '')
birthday = env.get('WOORI_BIRTHDAY', '')

print(f"Running Woori get_transactions using usage pattern:")
print(f"  bank_num: {bank_num}")
print(f"  birthday: {birthday}")

transaction_list = get_transactions(
    bank_num=bank_num,
    birthday=birthday,
    password=password,
    days=30
)

print("\n--- Woori Transactions Result ---")
for trs in transaction_list:
    print(trs.get('date'), trs.get('amount'), trs.get('transaction_by'), trs.get('balance'))
