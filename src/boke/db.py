from dataclasses import asdict
import json
from pathlib import Path
from typing import Callable, Final, Iterable
from result import Err, Ok, Result
import sqlite3
from . import stmt
from . import model

Conn = sqlite3.Connection
BlogConfig = model.BlogConfig

NoResultError = "database-no-result"
OK = Ok("OK.")

cwd = Path.cwd().resolve()
db_path: Final = cwd.joinpath(model.DB_filename)
drafts_dir: Final = cwd.joinpath(model.Drafts_folder_name)
posted_dir: Final = cwd.joinpath(model.Posted_folder_name)
output_dir: Final = cwd.joinpath(model.Output_folder_name)
templates_dir: Final = cwd.joinpath(model.Templates_folder_name)


def connect() -> Conn:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def execute(func: Callable, *args):
    with connect() as conn:
        return func(conn, *args)


def connUpdate(
    conn: Conn, query: str, param: Iterable, many: bool = False
) -> Result[int, str]:
    if many:
        n = conn.executemany(query, param).rowcount
    else:
        n = conn.execute(query, param).rowcount
    if n <= 0:
        return Err("sqlite row affected = 0")
    return Ok(n)


def exists(conn: Conn, query: str, param: Iterable) -> bool:
    return True if conn.execute(query, param).fetchone()[0] else False


def get_cfg(conn: Conn) -> Result[BlogConfig, str]:
    row = conn.execute(stmt.Get_metadata, (model.Blog_cfg_name,)).fetchone()
    if row is None:
        return Err(NoResultError)
    cfg: dict = json.loads(row[0])
    return Ok(BlogConfig(**cfg))


def update_cfg(conn: Conn, cfg: BlogConfig) -> None:
    connUpdate(
        conn,
        stmt.Update_metadata,
        {"name": model.Blog_cfg_name, "value": json.dumps(asdict(cfg))},
    ).unwrap()


def init_cfg(conn: Conn, cfg: BlogConfig) -> None:
    if get_cfg(conn).is_err():
        connUpdate(
            conn,
            stmt.Insert_metadata,
            {"name": model.Blog_cfg_name, "value": json.dumps(asdict(cfg))},
        ).unwrap()


def set_author(conn: Conn, author: str) -> None:
    cfg = get_cfg(conn).unwrap()
    cfg.author = author
    update_cfg(conn, cfg)


def get_all_cats(conn: Conn) -> list[model.Category]:
    rows = conn.execute(stmt.Get_all_cats).fetchall()
    return [model.new_cat_from(row) for row in rows]


def get_all_cats_name(conn: Conn) -> list[str]:
    rows = conn.execute(stmt.Get_all_cats).fetchall()
    return [row["name"] for row in rows]


def get_cat_id(conn: Conn, cat_name: str) -> str:
    return conn.execute(stmt.Get_cat_id, (cat_name,)).fetchone()[0]


def get_cat_name(conn: Conn, cat_id: str) -> str:
    return conn.execute(stmt.Get_cat_name, (cat_id,)).fetchone()[0]


def get_articles_by_cat(conn: Conn, cat_id: str) -> list[model.Article]:
    rows = conn.execute(stmt.Get_articles_by_cat, (cat_id,)).fetchall()
    return [model.new_article_from(row) for row in rows]


def get_article(conn: Conn, article_id: str) -> model.Article:
    row = conn.execute(stmt.Get_article, (article_id,)).fetchone()
    return model.new_article_from(row)


def get_tags_by_article(conn: Conn, article_id: str) -> list[str]:
    rows = conn.execute(stmt.Get_tags_by_article, (article_id,)).fetchall()
    return [row[0] for row in rows]


def insert_cat(
    conn: Conn, name: str, notes: str = "", id: str = ""
) -> Result[str, str]:
    cat = model.new_cat_from(dict(id=id, name=name, notes=notes))
    try:
        conn.execute(stmt.Insert_cat, asdict(cat))
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            return Err(f"Category Exists (类别已存在): {cat.name}")
        else:
            raise
    return Ok()


def insert_tags(conn: Conn, tags: list[str], article_id: str) -> None:
    for tag in tags:
        if not exists(conn, stmt.Tag_name, (tag,)):
            connUpdate(conn, stmt.Insert_tag, (tag,)).unwrap()
            connUpdate(
                conn,
                stmt.Insert_tag_article,
                {"tag_name": tag, "article_id": article_id},
            ).unwrap()


def insert_article(conn: Conn, article: model.Article, tags: list[str]) -> None:
    connUpdate(conn, stmt.Insert_article, asdict(article)).unwrap()
    insert_tags(conn, tags, article.id)


def update_last_pub(conn: Conn, article_id: str) -> None:
    connUpdate(
        conn, stmt.Update_last_pub, dict(last_pub=model.now(), id=article_id)
    ).unwrap()
