from .kb.crawler import get_transactions as kb_get_transactions
from .woori.crawler import get_transactions as woori_get_transactions

__all__ = ['get_transactions']

def get_transactions(bank_name=None, bank_num=None, birthday=None, password=None, bank=None, **kwargs):
    """
    Get transactions from the specified bank.
    
    :param bank_name: 'kb' (or 'kookmin') / 'woori'
    :param bank_num: account number
    :param birthday: birthday (YYMMDD)
    :param password: password (4 digits)
    :param kwargs: optional arguments (days, etc.)
    :return: list of transaction dicts
    """
    selected_bank = bank_name or bank
    if not selected_bank:
        raise ValueError("bank_name is a required argument")

    bank_clean = str(selected_bank).strip().lower()
    if bank_clean in ('kb', 'kookmin', '국민', '국민은행'):
        return kb_get_transactions(bank_num=bank_num, birthday=birthday, password=password, **kwargs)
    elif bank_clean in ('woori', 'wooribank', '우리', '우리은행'):
        return woori_get_transactions(bank_num=bank_num, birthday=birthday, password=password, **kwargs)
    else:
        raise ValueError(f"Unsupported bank: {selected_bank}")
