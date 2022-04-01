from dataclasses import asdict
import json
import os
from pathlib import Path
from typing import Any, Iterable
from result import Err, Ok, Result
import sqlite3
from . import stmt
from . import model

Conn = sqlite3.Connection
BlogConfig = model.BlogConfig

NoResultError = "database-no-result"
OK = Ok("OK.")

cwd = Path.cwd().resolve()
db_path = cwd.joinpath(model.DB_filename)
drafts_dir = cwd.joinpath(model.Drafts_folder_name)
posted_dir = cwd.joinpath(model.Posted_folder_name)
output_dir = cwd.joinpath(model.Output_folder_name)
templates_dir = cwd.joinpath(model.Templates_folder_name)


def connect() -> Conn:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def connUpdate(
    conn: Conn, query: str, param: Iterable[Any], many: bool = False
) -> Result[int, str]:
    if many:
        n = conn.executemany(query, param).rowcount
    else:
        n = conn.execute(query, param).rowcount
    if n <= 0:
        return Err("sqlite row affected = 0")
    return Ok(n)


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
