from .kb.crawler import get_transactions as kb_get_transactions
from .hana.crawler import get_transactions as hana_get_transactions
from .woori.crawler import get_transactions as woori_get_transactions

__all__ = ['get_transactions']

def get_transactions(bank_name, bank_num, birthday, password, **kwargs):
    """
    Get transactions from the specified bank.
    
    :param bank_name: 'kb' (or 'kookmin') / 'hana' / 'woori'
    :param bank_num: account number
    :param birthday: birthday (YYMMDD)
    :param password: password (4 digits)
    :param kwargs: optional arguments (days, etc.)
    :return: list of transaction dicts
    """
    bank_clean = str(bank_name).strip().lower()
    if bank_clean in ('kb', 'kookmin', '국민', '국민은행'):
        return kb_get_transactions(bank_num=bank_num, birthday=birthday, password=password, **kwargs)
    elif bank_clean in ('hana', 'hanabank', '하나', '하나은행'):
        return hana_get_transactions(bank_num=bank_num, birthday=birthday, password=password, **kwargs)
    elif bank_clean in ('woori', 'wooribank', '우리', '우리은행'):
        return woori_get_transactions(bank_num=bank_num, birthday=birthday, password=password, **kwargs)
    else:
        raise ValueError(f"Unsupported bank: {bank_name}")
