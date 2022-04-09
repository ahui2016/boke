import os
from pathlib import Path
import shutil
import sqlite3
from result import Err, Ok, Result
from . import stmt
from . import model
from . import db


Conn = sqlite3.Connection
BlogConfig = model.BlogConfig


def show_cfg(conn: Conn, cfg: BlogConfig | None = None) -> None:
    if not cfg:
        cfg = db.get_cfg(conn).unwrap()
    print(
        f"\n    [Root Folder] {db.cwd}"
        f"\n    [Blog's name] {cfg.name}"
        f"\n         [Author] {cfg.author}"
        f"\n[home_recent_max] {cfg.home_recent_max}"
    )
    print()


def update_blog_info(conn: Conn, blog_name: str, author: str) -> None:
    cfg = db.get_cfg(conn).unwrap()
    cfg.name = blog_name
    cfg.author = author
    db.update_cfg(conn, cfg)
    show_cfg(conn, cfg)


def dir_not_empty(path=".") -> bool:
    return True if os.listdir(path) else False


def copy_tmpl_files() -> None:
    src_folder = Path(__file__).parent.joinpath(model.Templates_folder_name)
    if not src_folder.exists():
        src_folder = Path(__file__).parent.parent.joinpath(model.Templates_folder_name)
    print(src_folder)

    static_files = src_folder.glob("*")
    for src in static_files:
        dst = db.templates_dir.joinpath(src.name)
        shutil.copyfile(src, dst)


def init_blog(blog_name: str, author: str) -> None:
    has_err = False
    if not blog_name:
        print("\nError. Blog's name is empty.")
        has_err = True
    if not author:
        print("\nError. Author is empty.")
        has_err = True
    if dir_not_empty():
        print(f"\nError. Folder Not Empty: {db.cwd}")
        has_err = True
    if has_err:
        print(f"\n[Blog's name] {blog_name}" f"\n     [Author] {author}")
        print(f"\nboke init: Failed.")
        print()
        return

    db.drafts_dir.mkdir()
    db.posted_dir.mkdir()
    db.output_dir.mkdir()
    db.templates_dir.mkdir()
    copy_tmpl_files()

    with db.connect() as conn:
        conn.executescript(stmt.Create_tables)
        db.init_cfg(conn, BlogConfig(blog_name, author))
        show_cfg(conn)


def get_first_line(filename: os.PathLike) -> Result[str, str]:
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                return Ok(line)
    return Err(f"Cannot get title from {filename}")


def get_md_file_title(filename: os.PathLike) -> Result[str, str]:
    match get_first_line(filename):
        case Err(e):
            return Err(e)
        case Ok(first_line):
            return model.get_md_title(first_line, model.ArticleTitleLimit)


def post_article(
    src_file: os.PathLike, article: model.Article, tags: list[str]
) -> None:
    with db.connect() as conn:
        db.insert_article(conn, article, tags)

    dst = db.posted_dir.joinpath(article.id + ".md")
    shutil.move(src_file, dst)


def show_article_info(
    article: model.Article, cat: str, tags: list[str], cfg: BlogConfig
) -> None:
    author = article.author if article.author else cfg.author
    print(
        "\n"
        f"       [ID] {article.id}\n"
        f"    [Title] {article.title}\n"
        f"   [Author] {author}\n"
        f" [Category] {cat}\n"
        f"[published] {article.published}\n"
        f"  [updated] {article.updated}\n"
    )
    if tags:
        tags_preview = "  #".join(tags)
        print(f"     [Tags] #{tags_preview}")
        print()


def show_article_info_by_id(conn: Conn, article_id: str) -> None:
    article = db.get_article(conn, article_id)
    cat = db.get_cat_name(conn, article.cat_id)
    tags = db.get_tags_by_article(conn, article_id)
    cfg = db.get_cfg(conn).unwrap()
    show_article_info(article, cat, tags, cfg)
