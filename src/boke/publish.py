import jinja2
import sqlite3
from typing import Final
from . import model
from . import db


Conn = sqlite3.Connection
html_suffix:Final = ".html"
atom_xml:Final = "atom.xml"
atom_entries_limit: Final = 10  # RSS 最多包含多少条信息

index_tmpl:Final = db.templates_dir.joinpath("index.html")

loader = jinja2.FileSystemLoader(db.templates_dir)
jinja_env = jinja2.Environment(loader=loader, autoescape=jinja2.select_autoescape())


def render_write_page() -> None:
    render_write_page(
        dst_dir, tmpl_folder, index_html, index_html, feed, links, entries
    )

def publish_html(conn: Conn, cfg:model.BlogConfig) -> None:
    print("OK.\n")
