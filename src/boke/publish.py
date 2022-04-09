from dataclasses import asdict
import shutil
import jinja2
import sqlite3
import mistune
from typing import Final
from . import model
from . import db


Conn = sqlite3.Connection
atom_entries_limit: Final = 10  # RSS 最多包含多少条信息

loader: Final = jinja2.FileSystemLoader(db.templates_dir)
jinja_env: Final = jinja2.Environment(
    loader=loader, autoescape=jinja2.select_autoescape()
)
md_render: Final = mistune.create_markdown(
    plugins=["strikethrough", "footnotes", "table", "url"]
)

# 发布时，除了 template_files 之外, templates 文件夹里的全部文件都会被复制到 ouput 文件夹。
template_files: Final = [model.index_html, model.article_html]


def copy_static_files() -> None:
    static_files = db.templates_dir.glob("*")
    for src in static_files:
        if src.name not in template_files and src.is_file():
            dst = db.output_dir.joinpath(src.name)
            print(f"copy static file to {dst}")
            shutil.copyfile(src, dst)


def render_write_index(blog: model.BlogConfig, cats: list[model.ArticlesInCat]) -> None:
    tmpl = jinja_env.get_template(model.index_html)
    html = tmpl.render(dict(blog=blog, cats=cats))
    output = db.output_dir.joinpath(model.index_html)
    print(f"render and write {output}")
    output.write_text(html, encoding="utf-8")


def render_write_article(
    blog: model.BlogConfig, cat: str, article: model.Article
) -> None:
    src_file = db.posted_dir.joinpath(
        article.published[:4], article.id + model.md_suffix
    )
    dst_dir = db.output_dir.joinpath(article.published[:4])
    dst_dir.mkdir(exist_ok=True)
    dst_file = dst_dir.joinpath(article.id + model.html_suffix)

    art = asdict(article)
    art["content"] = md_render(src_file.read_text(encoding="utf-8"))

    tmpl = jinja_env.get_template(model.article_html)
    html = tmpl.render(dict(art=art))
    print(f"render and write {dst_file}")
    dst_file.write_text(html, encoding="utf-8")


def publish_html(conn: Conn, cfg: model.BlogConfig, force_all:bool) -> None:
    """如果 force_all is True, 就强制重新生成全部文章。
       如果 force_all is False, 则只生成新文章与有更新的文章。
    """
    cats: list[model.ArticlesInCat] = []
    cat_list = db.get_all_cats(conn)
    for cat in cat_list:
        articles = db.get_articles_by_cat(conn, cat.id)
        cats.append(model.ArticlesInCat(cat=cat, articles=articles))
        for article in articles:
            if force_all is True or article.updated > article.last_pub:
                render_write_article(cfg, cat.name, article)
                db.update_last_pub(conn, article.id)

    render_write_index(cfg, cats)


def publish_all(conn: Conn, force_all:bool) -> None:
    cfg = db.get_cfg(conn).unwrap()
    publish_html(conn, cfg, force_all)
    copy_static_files()
    print("OK. (完成)")
