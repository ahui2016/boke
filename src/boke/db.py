from dataclasses import asdict
import json
from pathlib import Path
from typing import Callable, Final, Iterable
from result import Err, Ok, Result
import sqlite3
from . import stmt
from . import model
from .model import Article, BlogConfig, Tag

Conn = sqlite3.Connection

NoResultError = "database-no-result"
OK = Ok("OK.")

cwd = Path.cwd().resolve()
db_path: Final = cwd.joinpath(model.DB_filename)
drafts_dir: Final = cwd.joinpath(model.Drafts_folder_name)
posted_dir: Final = cwd.joinpath(model.Posted_folder_name)
output_dir: Final = cwd.joinpath(model.Output_folder_name)
templates_dir: Final = cwd.joinpath(model.Templates_folder_name)
themes_dir: Final = templates_dir.joinpath(model.Themes_folder_name)


def posted_file_path(article_id: str, published: str) -> Path:
    return posted_dir.joinpath(published[:4], article_id + model.md_suffix)


def connect() -> Conn:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(stmt.Enable_foreign_keys)
    return conn


def execute(func: Callable, *args):
    with connect() as conn:
        return func(conn, *args)


def conn_update(
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


def fetchone(conn: Conn, query: str, param: Iterable):
    return conn.execute(query, param).fetchone()[0]


def get_cfg(conn: Conn) -> Result[BlogConfig, str]:
    row = conn.execute(stmt.Get_metadata, (model.Blog_cfg_name,)).fetchone()
    if row is None:
        return Err(NoResultError)
    cfg: dict = json.loads(row[0])
    return Ok(BlogConfig(**cfg))


def update_cfg(conn: Conn, cfg: BlogConfig) -> None:
    conn_update(
        conn,
        stmt.Update_metadata,
        {"name": model.Blog_cfg_name, "value": json.dumps(asdict(cfg))},
    ).unwrap()


def update_cfg_now(conn: Conn) -> None:
    cfg = get_cfg(conn).unwrap()
    cfg.updated = model.now()
    update_cfg(conn, cfg)


def init_cfg(conn: Conn, cfg: BlogConfig) -> None:
    if get_cfg(conn).is_err():
        conn_update(
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


def get_all_tags(conn: Conn) -> list[Tag]:
    rows = conn.execute(stmt.Get_all_tags).fetchall()
    return [model.new_tag_from(row) for row in rows]


def get_articles_by_cat(conn: Conn, cat_id: str) -> list[Article]:
    rows = conn.execute(stmt.Get_articles_by_cat, (cat_id,)).fetchall()
    return [model.new_article_from(row) for row in rows]


def get_recent_articles(conn: Conn, limit: int) -> list[Article]:
    rows = conn.execute(stmt.Get_recent_articles, (limit,)).fetchall()
    return [model.new_article_from(row) for row in rows]


def get_article(conn: Conn, article_id: str) -> Article:
    row = conn.execute(stmt.Get_article, (article_id,)).fetchone()
    return model.new_article_from(row)


def get_tag_names(conn: Conn, article_id: str) -> list[str]:
    rows = conn.execute(stmt.Get_tag_names, (article_id,)).fetchall()
    return [row[0] for row in rows]


def get_tags_by_article(conn: Conn, article_id: str) -> list[Tag]:
    rows = conn.execute(stmt.Get_tags_by_article, (article_id,)).fetchall()
    return [model.new_tag_from(row) for row in rows]


def count_articles_by_tag(conn: Conn, tag_name: str) -> int:
    return fetchone(conn, stmt.Count_articles_by_tag, (tag_name,))


def get_art_ids_by_tag(conn: Conn, tag_name: str) -> list[str]:
    rows = conn.execute(stmt.Get_art_ids_by_tag, (tag_name,)).fetchall()
    return [row[0] for row in rows]


def get_pub_arts_by_tag(conn: Conn, tag_name: str) -> list[Article]:
    """获取公开的文章"""
    pub_arts = []
    art_ids = get_art_ids_by_tag(conn, tag_name)
    for art_id in art_ids:
        art = get_article(conn, art_id)
        if not art.hidden:
            pub_arts.append(art)
    return pub_arts


def count_pub_arts_by_tag(conn: Conn, tag_name: str) -> int:
    n = 0
    art_ids = get_art_ids_by_tag(conn, tag_name)
    for art_id in art_ids:
        hidden = fetchone(conn, stmt.Get_article_hidden, (art_id,))
        if hidden == 0:
            n += 1
    return n


def get_cat(conn: Conn, cat_id: str) -> Result[model.Category, str]:
    row = conn.execute(stmt.Get_cat, (cat_id,)).fetchone()
    if not row:
        return Err(f"Not Found: {cat_id}")
    return Ok(model.new_cat_from(row))


def insert_cat(
    conn: Conn, name: str, notes: str = "", cat_id: str = ""
) -> Result[str, str]:
    name = name.replace(" ", "")
    cat = model.new_cat_from(dict(id=cat_id, name=name, notes=notes))
    try:
        conn.execute(stmt.Insert_cat, asdict(cat))
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            return Err(f"Category Exists (类别已存在): {cat.name}")
        else:
            raise
    return Ok(name)


def update_cat(
    conn: Conn, name: str, notes: str, cat_id: str
) -> Result[str, str]:
    name = name.replace(" ", "")
    try:
        conn.execute(stmt.Update_cat, dict(name=name, notes=notes, id=cat_id))
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            return Err(f"Category Exists (类别已存在): {name}")
        else:
            raise
    return Ok(name)


def rename_tag(conn: Conn, new_name: str, old_name: str) -> Result[str, str]:
    try:
        conn.execute(
            stmt.Rename_tag, dict(new_name=new_name, old_name=old_name)
        )
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            return Err(f"Tag Exists (标签已存在): {new_name}")
        else:
            raise
    return Ok()


def delete_cat(conn: Conn, cat_id: str) -> Result[str, str]:
    n = fetchone(conn, stmt.Count_articles_by_cat, (cat_id,))
    if n > 0:
        return Err(f"有 {n} 篇文章与该类别关联，不可删除。")
    return conn_update(conn, stmt.Delete_cat, (cat_id,))


def insert_tags(conn: Conn, tags: list[str], article_id: str) -> None:
    if not tags:
        return
    tag_ids = []
    for tag_name in tags:
        tag_id = conn.execute(stmt.Get_tag_id, (tag_name,)).fetchone()
        if not tag_id:
            tag = model.new_tag_from({"name": tag_name})
            tag_ids.append(tag.id)
            conn_update(conn, stmt.Insert_tag, asdict(tag)).unwrap()
        else:
            tag_ids.append(tag_id[0])
    params = [
        {"tag_id": tag_id, "article_id": article_id} for tag_id in tag_ids
    ]
    conn_update(conn, stmt.Insert_tag_article, params, many=True).unwrap()


def insert_article(
    conn: Conn, article: Article, tags: list[str]
) -> None:
    conn_update(conn, stmt.Insert_article, asdict(article)).unwrap()
    insert_tags(conn, tags, article.id)


def update_last_pub(conn: Conn, article_id: str) -> None:
    conn_update(
        conn, stmt.Update_last_pub, dict(last_pub=model.now(), id=article_id)
    ).unwrap()


def update_article_date(conn: Conn, title: str, article_id: str) -> None:
    conn_update(
        conn,
        stmt.Update_article_date,
        dict(updated=model.now(), title=title, id=article_id),
    ).unwrap()


def delete_tags(conn: Conn, article_id: str, tags: list[str]) -> None:
    if not tags:
        return
    params = [{"tag_name": tag, "article_id": article_id} for tag in tags]
    conn_update(conn, stmt.Delete_tag_article, params, many=True).unwrap()
    # 如果一个标签已经不再关联任何文章，则该标签也会被删除。
    for tag in tags:
        if count_articles_by_tag(conn, tag) == 0:
            conn_update(conn, stmt.Delete_tag, (tag,)).unwrap()
