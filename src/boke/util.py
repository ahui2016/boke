import os
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

    with db.connect() as conn:
        conn.executescript(stmt.Create_tables)
        db.init_cfg(conn, BlogConfig(blog_name, author))
        show_cfg(conn)


def get_first_line(filename: str) -> Result[str, str]:
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                return Ok(line)
    return Err(f"Cannot get title from {filename}")


def get_md_file_title(filename: str) -> Result[str, str]:
    match get_first_line(filename):
        case Err(e):
            return Err(e)
        case Ok(first_line):
            return model.get_md_title(first_line, model.ArticleTitleLimit)
