from .kb.crawler import get_transactions as kb_get_transactions
from .woori.crawler import get_transactions as woori_get_transactions

def get_transactions(bank, bank_num, birthday, password, **kwargs):
    """
    Get transactions from the specified bank.
    
    :param bank: 'kb' (or 'kookmin') / 'woori'
    :param bank_num: account number
    :param birthday: birthday (YYMMDD)
    :param password: password (4 digits)
    :param kwargs: optional arguments (days, etc.)
    :return: list of transaction dicts
    """
    bank_name = str(bank).strip().lower()
    if bank_name in ('kb', 'kookmin', '국민', '국민은행'):
        return kb_get_transactions(bank_num=bank_num, birthday=birthday, password=password, **kwargs)
    elif bank_name in ('woori', 'wooribank', '우리', '우리은행'):
        return woori_get_transactions(bank_num=bank_num, birthday=birthday, password=password, **kwargs)
    else:
        raise ValueError(f"Unsupported bank: {bank}")
