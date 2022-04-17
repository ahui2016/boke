from dataclasses import dataclass
import re
from typing import Final, TypedDict
from random import randrange
import arrow
from result import Err, Ok, Result


RFC3339: Final = "YYYY-MM-DDTHH:mm:ssZZ"
DB_filename: Final = "boke.db"
Drafts_folder_name: Final = "drafts"
Posted_folder_name: Final = "posted"
Output_folder_name: Final = "output"
Templates_folder_name: Final = "templates"
Themes_folder_name: Final = "themes"
Blog_cfg_name: Final = "blog-config"

html_suffix: Final = ".html"
md_suffix: Final = ".md"
atom_xml: Final = "atom.xml"

ArticleTitleLimit: Final = 192  # 文章标题长度上限
Article_ID_Limit: Final = 64  # 文章 ID 长度上限（该 ID 同时也是文件名）

MD_TitlePattern: Final = re.compile(r"^(#{1,6}|>|1.|-|\*) (.+)")
Article_ID_ForbidPattern: Final = re.compile(r"[^_0-9a-zA-Z\-]")


@dataclass
class BlogConfig:
    name: str  # 博客名称
    author: str  # 默认作者（每篇文章也可独立设定作者）
    home_recent_max: int = 20  # 首页 "最近更新" 列表中的项目上限


@dataclass
class Category:
    id: str
    name: str
    notes: str


def new_cat_from(row: dict) -> Category:
    cat_id = row["id"] if row["id"] else rand_id()
    return Category(id=cat_id, name=row["name"], notes=row["notes"])


@dataclass
class Article:
    id: str
    cat_id: str
    title: str
    author: str
    published: str
    updated: str  # 最新修改时间, 如果大于 last_pub 就需要重新生成静态文件
    last_pub: str  # 上次生成静态文件的时间


def new_article_from(row: dict) -> Article:
    article_id = row["id"] if row["id"] else date_id()
    check_article_id(article_id).unwrap()

    published = row["published"] if row["published"] else now()
    _ = arrow.get(published, RFC3339)

    return Article(
        id=article_id,
        cat_id=row["cat_id"],
        title=row["title"],
        author=row["author"],
        published=published,
        updated=row["updated"],
        last_pub=row["last_pub"],
    )


@dataclass
class ArticlesInCat:
    cat: Category
    articles: list[Article]


def now() -> str:
    return arrow.now().format(RFC3339)


# https://github.com/numpy/numpy/blob/main/numpy/core/numeric.py
def base_repr(number: int, base: int = 10, padding: int = 0) -> str:
    """
    Return a string representation of a number in the given base system.
    """
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
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


def check_article_id(article_id: str) -> Result[str, str]:
    if Article_ID_ForbidPattern.search(article_id) is None:
        return Ok()
    else:
        return Err("ID 只可以由 0-9a-zA-Z 以及下划线、短横线组成")


def get_md_title(md_first_line: str, max_bytes: int) -> Result[str, str]:
    """md_first_line 应已去除首尾空白字符。"""
    md_title = MD_TitlePattern.findall(md_first_line)
    if not md_title:
        title = md_first_line
    else:
        # 此时 md_title 大概像这样: [('#', ' abcd')]
        title = md_title[0][1].strip()

    truncated = utf8_byte_truncate(title, max_bytes).strip()
    if not truncated:
        return Err("Cannot get title. (无法获取标题)\n请修改文章的标题(文件内容的第一行)")
    else:
        return Ok(truncated)


def unique_str_list(str_list: list[str]) -> list[str]:
    items = []
    for item in str_list:
        upper_items = [item.upper() for item in items]
        if item.upper() not in upper_items:
            items.append(item)
    return items


class DiffTags(TypedDict):
    """tags_diff 函数的返回值的类型"""

    to_add: list[str]
    to_del: list[str]


def tags_diff(new_tags: list[str], old_tags: list[str]) -> DiffTags:
    """返回需要新增的标签与需要删除的标签"""
    diff_tags = DiffTags(to_add=[], to_del=[])
    upper_new_tags = [tag.upper() for tag in new_tags]
    upper_old_tags = [tag.upper() for tag in old_tags]

    # new_tags 里有，但 old_tags 里没有的，需要添加到数据库。
    for tag in new_tags:
        if tag.upper() not in upper_old_tags:
            diff_tags["to_add"].append(tag)

    # old_tags 里有，但 new_tags 里没有的，需要从数据库中删除。
    for tag in old_tags:
        if tag.upper() not in upper_new_tags:
            diff_tags["to_del"].append(tag)

    return diff_tags
