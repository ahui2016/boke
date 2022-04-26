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
tmplfile: Final = dict(
    base="base.html",
    index="index.html",
    cat="cat.html",
    article="article.html",
    tag="tag.html",
)


def copy_static_files() -> None:
    static_files = db.templates_dir.glob("*")
    for src in static_files:
        if src.name not in tmplfile.values() and src.is_file():
            dst = db.output_dir.joinpath(src.name)
            print(f"copy static file to {dst}")
            shutil.copyfile(src, dst)


def copy_theme(theme: str) -> None:
    filename = theme + ".css"
    print(f"Theme: {filename}")
    src = db.templates_dir.joinpath(model.Themes_folder_name, filename)
    dst = db.output_dir.joinpath("theme.css")
    shutil.copyfile(src, dst)


def render_write_index(
    blog: model.BlogConfig,
    cats: list[model.Category],
    tags: list[model.Tag],
    articles: list,
) -> None:
    tmpl = jinja_env.get_template(tmplfile["index"])
    html = tmpl.render(
        dict(blog=blog, cats=cats, tags=tags, articles=articles, parent_dir="")
    )
    output = db.output_dir.joinpath(tmplfile["index"])
    print(f"render and write {output}")
    output.write_text(html, encoding="utf-8")


def render_write_cat(
    blog: model.BlogConfig, cat: model.Category, articles: list[model.Article]
) -> None:
    tmpl = jinja_env.get_template(tmplfile["cat"])
    html = tmpl.render(
        dict(blog=blog, cat=cat, articles=articles, parent_dir="")
    )
    output = db.output_dir.joinpath(cat.id + model.html_suffix)
    print(f"render and write ({cat.name}) {output}")
    output.write_text(html, encoding="utf-8")


def render_write_tag(
    blog: model.BlogConfig, tag: model.Tag, articles: list[model.Article]
) -> None:
    tmpl = jinja_env.get_template(tmplfile["tag"])
    html = tmpl.render(
        dict(blog=blog, tag=tag, articles=articles, parent_dir="")
    )
    output = db.output_dir.joinpath(tag.id + model.html_suffix)
    print(f"render and write ({tag.name}) {output}")
    output.write_text(html, encoding="utf-8")


def render_write_article(
    blog: model.BlogConfig,
    cat: model.Category,
    tags: list[model.Tag],
    article: model.Article,
) -> None:
    src_file = db.posted_file_path(article.id, article.published)
    dst_dir = db.output_dir.joinpath(article.published[:4])
    dst_dir.mkdir(exist_ok=True)
    dst_file = dst_dir.joinpath(article.id + model.html_suffix)

    art = asdict(article)
    art["content"] = md_render(src_file.read_text(encoding="utf-8"))

    tmpl = jinja_env.get_template(tmplfile["article"])
    html = tmpl.render(
        dict(blog=blog, cat=cat, tags=tags, art=art, parent_dir="../")
    )
    print(f"render and write {dst_file}")
    dst_file.write_text(html, encoding="utf-8")


def set_cat_name(
    categories: list[model.Category], articles: list[model.Article]
) -> list:
    cats = {}
    for cat in categories:
        cats[cat.id] = cat.name

    arts = []
    for i, _ in enumerate(articles):
        cat = cats[articles[i].cat_id]
        art = asdict(articles[i])
        art["cat_name"] = cat
        arts.append(art)

    return arts


def generate_html(conn: Conn, cfg: model.BlogConfig, force_all: bool) -> None:
    """如果 force_all is True, 就强制重新生成全部文章。
    如果 force_all is False, 则只生成新文章与有更新的文章。
    """
    tags = db.get_all_tags(conn)
    for tag in tags:
        articles = db.get_articles_by_tag(conn, tag.name)
        render_write_tag(cfg, tag, articles)

    cat_list = db.get_all_cats(conn)
    for cat in cat_list:
        articles = db.get_articles_by_cat(conn, cat.id)
        render_write_cat(cfg, cat, articles)
        cat.notes = ""  # 后续不需要用到 cat.notes
        for article in articles:
            if force_all is True or article.updated > article.last_pub:
                render_write_article(cfg, cat, tags, article)
                db.update_last_pub(conn, article.id)

    articles = db.get_recent_articles(conn, cfg.home_recent_max)
    arts = set_cat_name(cat_list, articles)

    render_write_index(cfg, cat_list, tags, arts)


def generate_all(
    conn: Conn, theme: str, ignore_assets: bool, force_all: bool
) -> None:
    cfg = db.get_cfg(conn).unwrap()
    if theme != "unchanged":
        copy_theme(theme)
    generate_html(conn, cfg, force_all)
    if not ignore_assets:
        copy_static_files()
    print("OK. (完成)")
