import shutil
import jinja2
import sqlite3
from typing import Final
from . import model
from . import db


Conn = sqlite3.Connection
html_suffix: Final = ".html"
atom_xml: Final = "atom.xml"
atom_entries_limit: Final = 10  # RSS 最多包含多少条信息

loader: Final = jinja2.FileSystemLoader(db.templates_dir)
jinja_env: Final = jinja2.Environment(
    loader=loader, autoescape=jinja2.select_autoescape()
)

# 发布时，除了 template_files 之外, templates 文件夹里的全部文件都会被复制到 ouput 文件夹。
template_files: Final = ["index.html"]


def copy_static_files() -> None:
    static_files = db.templates_dir.glob("*")
    for src in static_files:
        if src.name not in template_files and src.is_file():
            dst = db.output_dir.joinpath(src.name)
            print(f"copy static file to {dst}")
            shutil.copyfile(src, dst)


def render_write_index(blog: model.BlogConfig, cats: list[model.ArticlesInCat]) -> None:
    filename = "index.html"
    tmpl = jinja_env.get_template(filename)
    html = tmpl.render(dict(blog=blog, cats=cats))
    output = db.output_dir.joinpath(filename)
    print(f"render and write {output}")
    output.write_text(html, encoding="utf-8")


def publish_html(conn: Conn, cfg: model.BlogConfig) -> None:
    cats: list[model.ArticlesInCat] = []
    cat_list = db.get_all_cats(conn)
    print(cat_list)
    for cat in cat_list:
        print(cat.id)
        articles = db.get_articles_by_cat(conn, cat.id)
        print(articles)
        cats.append(model.ArticlesInCat(cat=cat, articles=articles))

    render_write_index(cfg, cats)


def publish_all(conn: Conn) -> None:
    cfg = db.get_cfg(conn).unwrap()
    publish_html(conn, cfg)
    copy_static_files()
    print("OK. (完成)")
