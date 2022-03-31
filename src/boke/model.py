from typing import Final, TypedDict
from random import randrange
import arrow


RFC3339: Final[str] = "YYYY-MM-DDTHH:mm:ssZZ"


class BlogConfig(TypedDict):
    name: str
    author: str


class Category(TypedDict):
    id: str
    name: str
    notes: str


class Article(TypedDict):
    id: str
    cat_id: str
    title: str
    author: str
    published: str


def new_cat(name: str, notes: str) -> Category:
    return Category(id=rand_id(), name=name, notes=notes)


def new_article(cat_id: str, title: str, author: str) -> Article:
    return Article(
        id=date_id(), cat_id=cat_id, title=title, author=author, published=now()
    )


def now() -> str:
    return arrow.now().format(RFC3339)


# https://github.com/numpy/numpy/blob/main/numpy/core/numeric.py
def base_repr(number: int, base: int = 10, padding: int = 0) -> str:
    """
    Return a string representation of a number in the given base system.
    """
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if base > len(digits):
        raise ValueError("Bases greater than 36 not handled in base_repr.")
    elif base < 2:
        raise ValueError("Bases less than 2 not handled in base_repr.")

    num = abs(number)
    res = []
    while num:
        res.append(digits[num % base])
        num //= base
    if padding:
        res.append("0" * padding)
    if number < 0:
        res.append("-")
    return "".join(reversed(res or "0"))


def date_id() -> str:
    """时间戳转base36"""
    now = arrow.now().int_timestamp
    return base_repr(now, 36)


def rand_id() -> str:
    """只有 3～4 个字符的随机字符串"""
    n_min = int("100", 36)
    n_max = int("zzzz", 36)
    n_rand = randrange(n_min, n_max + 1)
    return base_repr(n_rand, 36)