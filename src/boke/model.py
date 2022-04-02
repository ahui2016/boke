from dataclasses import dataclass
import re
from typing import Final
from random import randrange
import arrow
from result import Err, Ok, Result


RFC3339: Final[str] = "YYYY-MM-DDTHH:mm:ssZZ"
DB_filename: Final[str] = "boke.db"
Drafts_folder_name: Final[str] = "drafts"
Posted_folder_name: Final[str] = "posted"
Output_folder_name: Final[str] = "output"
Templates_folder_name: Final[str] = "templates"
Blog_cfg_name: Final[str] = "blog-config"

ArticleTitleLimit: Final = 256 # 文章标题长度上限
Article_ID_Limit: Final = 64 # 文章 ID 长度上限（该 ID 同时也是文件名）

MD_TitlePattern: Final = re.compile(r"^(#{1,6}|>|1.|-|\*) (.+)")

@dataclass
class BlogConfig:
    name: str  # 博客名称
    author: str  # 默认作者（每篇文章也可独立设定作者）
    home_recent_max: int = 15  # 首页 "最近更新" 列表中的项目上限


@dataclass
class Category:
    id: str
    name: str
    notes: str

    def __init__(self, id: str, name: str, notes: str):
        self.id = id if id else rand_id()
        self.name = name
        self.notes = notes


@dataclass
class Article:
    id: str
    cat_id: str
    title: str
    author: str
    published: str

    def __init__(self, id: str, cat_id: str, title: str, author: str, published: str):
        self.id = id if id else date_id()
        self.cat_id = cat_id
        self.title = title
        self.author = author
        self.published = published if published else now()


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


def byte_len(s: str) -> int:
    return len(s.encode("utf8"))


def utf8_lead_byte(b):
    """A UTF-8 intermediate byte starts with the bits 10xxxxxx."""
    return (b & 0xC0) != 0x80


# https://stackoverflow.com/questions/13727977/truncating-string-to-byte-length-in-python
def utf8_byte_truncate(text: str, max_bytes: int) -> str:
    """If text[max_bytes] is not a lead byte, back up until a lead byte is
    found and truncate before that character."""
    utf8 = text.encode("utf8")
    if len(utf8) <= max_bytes:
        return text
    i = max_bytes
    while i > 0 and not utf8_lead_byte(utf8[i]):
        i -= 1
    return utf8[:i].decode("utf8")

def get_md_title(md_first_line:str, max_bytes:int) -> Result[str, str]:
    """md_first_line 应已去除首尾空白字符。"""
    md_title = MD_TitlePattern.findall(md_first_line)
    if not md_title:
        title = md_first_line
    else:
        # 此时 md_title 大概像这样: [('#', ' abcd')]
        title = md_title[0][1].strip()
    
    truncated = utf8_byte_truncate(title, max_bytes).strip()
    if not truncated:
        return Err(f"Cannot get title. (无法获取标题)\n"
            "请修改文章的标题(文件内容的第一行)")
    else:
        return Ok(truncated)
