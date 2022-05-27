import os
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

# 发布时，除了 tmplfile 之外, templates 文件夹里的全部文件都会被复制到 ouput 文件夹。
tmplfile: Final = dict(
    base="base.html",
    index="index.html",
    year="year.html",
    cat="cat.html",
    article="article.html",
    tag="tag.html",
    rss=model.atom_xml,
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


def render_write_rss(blog: model.BlogConfig, entries: list) -> None:
    tmpl = jinja_env.get_template(tmplfile["rss"])
    rss = tmpl.render(dict(blog=blog, entries=entries))
    output = db.output_dir.joinpath(model.atom_xml)
    print(f"render and write {output}")
    output.write_text(rss, encoding="utf-8")


def render_write_index(
    blog: model.BlogConfig,
    cats: list[model.Category],
    tags: list[model.Tag],
    year_count: list[tuple[str, int]],
    articles: list,
) -> None:
    tmpl = jinja_env.get_template(tmplfile["index"])
    html = tmpl.render(
        dict(
            blog=blog,
            cats=cats,
            tags=tags,
            year_count=year_count,
            articles=articles,
            parent_dir="",
        )
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
    output = db.output_dir.joinpath(
        model.cat_id_prefix + cat.id + model.html_suffix
    )
    print(f"render and write ({cat.name}) {output}")
    output.write_text(html, encoding="utf-8")


def render_write_tag(
    blog: model.BlogConfig, tag: model.Tag, articles: list[model.Article]
) -> None:
    tmpl = jinja_env.get_template(tmplfile["tag"])
    html = tmpl.render(
        dict(blog=blog, tag=tag, articles=articles, parent_dir="")
    )
    output = db.output_dir.joinpath(
        model.tag_id_prefix + tag.id + model.html_suffix
    )
    print(f"render and write ({tag.name}) {output}")
    output.write_text(html, encoding="utf-8")


def remove_hidden_article(article: model.Article) -> None:
    dst_dir = db.output_dir.joinpath(article.published[:4])
    dst_file = dst_dir.joinpath(article.id + model.html_suffix)
    if dst_file.exists():
        print(f"REMOVE {dst_file}")
        os.remove(dst_file)


def remove_empty_item(item_id: str, item_name: str) -> None:
    f = db.output_dir.joinpath(item_id + model.html_suffix)
    if f.exists():
        print(f"REMOVE ({item_name}) {f}")
        os.remove(f)


def render_write_article(
    blog: model.BlogConfig,
    cat: model.Category,
    article: model.Article,
) -> None:
    src_file = db.posted_file_path(article.id, article.published)
    dst_dir = db.output_dir.joinpath(article.published[:4])
    dst_dir.mkdir(exist_ok=True)
    dst_file = dst_dir.joinpath(article.id + model.html_suffix)

    cat.notes = ""
    art = asdict(article)
    art["content"] = md_render(src_file.read_text(encoding="utf-8"))
    tags = db.execute(db.get_tags_by_article, article.id)

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


def set_art_content(articles: list[model.Article]) -> list:
    arts = []
    for i, art in enumerate(articles):
        art_file = db.posted_file_path(art.id, art.published)
        content = art_file.read_text(encoding="utf-8")
        if len(content) > model.ContentSizeLimit:
            content = content[: model.ContentSizeLimit] + "..."
        art_dict = asdict(art)
        art_dict["content"] = content
        arts.append(art_dict)
    return arts


def articles_in_years(
    articles: list[model.Article],
) -> dict[str, list[model.Article]]:
    arts: dict[str, list[model.Article]] = {}
    for art in articles:
        yyyy = art.published[:4]
        if yyyy in arts:
            arts[yyyy].append(art)
        else:
            arts[yyyy] = [art]

    for yyyy in arts:
        arts[yyyy].sort(key=lambda x: x.published, reverse=True)

    return arts


def render_write_year(
    blog: model.BlogConfig, articles: list[model.Article]
) -> None:
    year = articles[0].published[:4]
    tmpl = jinja_env.get_template(tmplfile["year"])
    html = tmpl.render(
        dict(blog=blog, year=year, articles=articles, parent_dir="")
    )
    output = db.output_dir.joinpath(f"year_{year}.html")
    print(f"render and write ({year}) {output}")
    output.write_text(html, encoding="utf-8")


def generate_html(conn: Conn, cfg: model.BlogConfig, force_all: bool) -> None:
    """如果 force_all is True, 就强制重新生成全部文章。
    如果 force_all is False, 则只生成新文章与有更新的文章。
    """
    tags = db.get_all_tags(conn)
    tags_has_arts = []
    for tag in tags:
        articles = db.get_articles_by_tag(conn, tag.name)
        if len(articles) > 0:
            render_write_tag(cfg, tag, articles)
            tags_has_arts.append(tag)
        else:
            remove_empty_item(tag.id, tag.name)

    public_arts = []
    cat_list = db.get_all_cats(conn)
    cats_has_arts = []
    for cat in cat_list:
        articles = db.get_articles_by_cat(conn, cat.id)
        arts = []

        # 区分隐藏文章与公开文章
        for article in articles:
            if article.hidden:
                remove_hidden_article(article)
            else:
                arts.append(article)
                public_arts.append(article)

        # 区分是否生成文章
        for art in arts:
            if force_all is True or art.updated > art.last_pub:
                render_write_article(cfg, cat, art)
                db.update_last_pub(conn, art.id)

        # 区分是否生成类别
        if len(arts) > 0:
            render_write_cat(cfg, cat, arts)
            cats_has_arts.append(cat)
        else:
            remove_empty_item(cat.id, cat.name)

    art_dict = articles_in_years(public_arts)
    for yyyy in art_dict:
        render_write_year(cfg, art_dict[yyyy])

    year_count: list[tuple[str, int]] = []
    for yyyy in art_dict:
        year_count.append((yyyy, len(art_dict[yyyy])))

    year_count.sort(key=lambda x: x[0], reverse=True)

    articles = db.get_recent_articles(conn, cfg.home_recent_max)
    recent_arts = set_cat_name(cat_list, articles)
    render_write_index(
        cfg, cats_has_arts, tags_has_arts, year_count, recent_arts
    )


def generate_rss(conn: Conn, cfg: model.BlogConfig, force: bool) -> None:
    if not force and cfg.feed_last_pub > cfg.updated:
        return

    articles = db.get_recent_articles(conn, model.FeedItemsLimit)
    arts = set_art_content(articles)
    render_write_rss(cfg, arts)
    cfg.feed_last_pub = model.now()
    db.update_cfg(conn, cfg)


def generate_all(
    conn: Conn, theme: str, copy_assets: bool, force_all: bool
) -> None:
    folder_is_empty = not os.listdir(db.output_dir)
    if folder_is_empty or copy_assets:
        copy_static_files()

    if folder_is_empty:
        force_all = True

    cfg = db.get_cfg(conn).unwrap()
    if theme != "unchanged":
        copy_theme(theme)
    generate_html(conn, cfg, force_all)
    generate_rss(conn, cfg, force_all)

    print("OK. (完成)")
