from __future__ import annotations

from datetime import datetime
from typing import Any, List
from typing_extensions import TypedDict

from .kb.crawler import get_transactions as kb_get_transactions
from .hana.crawler import get_transactions as hana_get_transactions
from .woori.crawler import get_transactions as woori_get_transactions

__all__ = ['Transaction', 'get_transactions']


class Transaction(TypedDict):
    """A single bank transaction row returned by all crawlers."""
    date: datetime
    amount: int          # positive = deposit, negative = withdrawal
    balance: int
    transaction_by: str  # counterparty / memo


def get_transactions(
    bank_name: str,
    bank_num: str | int,
    birthday: str | int,
    password: str | int,
    **kwargs: Any,
) -> List[Transaction]:
    """
    Get transactions from the specified bank.

    :param bank_name: ``'kb'`` / ``'kookmin'`` / ``'hana'`` / ``'woori'``
                      (Korean aliases are also accepted)
    :param bank_num:  Account number (digits only, hyphens are stripped automatically)
    :param birthday:  Birthday in ``YYMMDD`` format
    :param password:  4-digit account password
    :param kwargs:    Extra keyword arguments forwarded to the bank crawler
                      (e.g. ``days=30``, ``headless=True``)
    :return:          List of :class:`Transaction` dicts, ordered newest-first
    """
    bank_clean = str(bank_name).strip().lower()
    if bank_clean in ('kb', 'kookmin', '국민', '국민은행'):
        return kb_get_transactions(bank_num=bank_num, birthday=birthday, password=password, **kwargs)  # type: ignore[return-value]
    elif bank_clean in ('hana', 'hanabank', '하나', '하나은행'):
        return hana_get_transactions(bank_num=bank_num, birthday=birthday, password=password, **kwargs)  # type: ignore[return-value]
    elif bank_clean in ('woori', 'wooribank', '우리', '우리은행'):
        return woori_get_transactions(bank_num=bank_num, birthday=birthday, password=password, **kwargs)  # type: ignore[return-value]
    else:
        raise ValueError(f"Unsupported bank: {bank_name}")
