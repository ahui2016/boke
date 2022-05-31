import os
import re
from pathlib import Path
import shutil
import sqlite3
from result import Err, Ok, Result
from . import stmt
from . import db
from . import model
from .model import Tag, BlogConfig
from .generate import render_tags


Conn = sqlite3.Connection


def show_cfg(conn: Conn, cfg: BlogConfig | None = None) -> None:
    if not cfg:
        cfg = db.get_cfg(conn).unwrap()
    print(
        f"\n    [Root Folder] {db.cwd}"
        f"\n    [Blog's name] {cfg.name}"
        f"\n         [Author] {cfg.author}"
        f"\n        [Website] {cfg.website}"
        f"\n      [feed_link] {cfg.feed_link}"
        f"\n[home_recent_max] {cfg.home_recent_max}"
    )
    print()


def dir_not_empty(path=".") -> bool:
    return True if os.listdir(path) else False


def copy_tmpl_files() -> None:
    src_folder = Path(__file__).parent.joinpath(model.Templates_folder_name)
    if not src_folder.exists():
        src_folder = Path(__file__).parent.parent.joinpath(
            model.Templates_folder_name
        )
    print(src_folder)
    shutil.copytree(src_folder, db.templates_dir)


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
        print("\nboke init: Failed.")
        print()
        return

    with db.connect() as conn:
        conn.executescript(stmt.Create_tables)
        feed_uuid = model.feed_uuid(blog_name)
        db.init_cfg(conn, BlogConfig(blog_name, author, feed_uuid))
        db.drafts_dir.mkdir()
        db.posted_dir.mkdir()
        db.output_dir.mkdir()
        copy_tmpl_files()
        show_cfg(conn)


def get_first_line(filename: Path) -> Result[str, str]:
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                return Ok(line)
    return Err(f"Cannot get title from {filename}")


def get_md_file_title(filename: Path) -> Result[str, str]:
    match get_first_line(filename):
        case Err(e):
            return Err(e)
        case Ok(first_line):
            return model.get_md_title(first_line, model.ArticleTitleLimit)


def post_article(
    conn: Conn, src_file: Path, article: model.Article, tags: list[str]
) -> None:
    db.insert_article(conn, article, tags)
    db.update_cfg_now(conn)
    dst_dir = db.posted_dir.joinpath(article.published[:4])
    dst_dir.mkdir(exist_ok=True)
    dst = dst_dir.joinpath(article.id + model.md_suffix)
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
        f"   [hidden] {article.hidden}\n"
    )
    if tags:
        tags_preview = "  #".join(tags)
        print(f"     [Tags] #{tags_preview}")
        print()


def show_article_info_by_id(conn: Conn, article_id: str) -> None:
    article = db.get_article(conn, article_id)
    cat = db.get_cat(conn, article.cat_id).unwrap()
    tags = db.get_tag_names(conn, article_id)
    cfg = db.get_cfg(conn).unwrap()
    show_article_info(article, cat.name, tags, cfg)


def update_article_date(article_id: str) -> None:
    with db.connect() as conn:
        db.update_article_date(conn, article_id)
        show_article_info_by_id(conn, article_id)


def check_title_when_update(
    article_id: str, title: str, filename: Path
) -> Result[str, str]:
    with db.connect() as conn:
        row = conn.execute(stmt.Get_article_id_by_title, (title,)).fetchone()
        if row and row[0] != article_id:
            print("Error. Title Exists (文章标题已存在):")
            print(f"[id: {row[0]}] {title}")
            print(f"\n(提示：文章标题不可重复，请修改文件 {filename} 的第一行)")
            return Err("")
    return Ok()


def not_in_drafts(draft: Path) -> bool:
    in_drafts = db.drafts_dir.joinpath(draft.name)
    if not in_drafts.exists() or not draft.samefile(in_drafts):
        print(f"The file is not in 'drafts': {draft}")
        print("(提示: 'boke post' 命令只能用来发布 drafts 文件夹里的文件。)")
        return True
    return False


def not_in_posted(src_file: Path, article_id: str, published: str) -> bool:
    other = db.posted_file_path(article_id, published)
    if not other.exists() or not src_file.samefile(other):
        print(f"The file is not in 'posted': {src_file}")
        print("(提示: 'boke update' 命令只能用来更新 posted 文件夹里的文件。)")
        return True
    return False


def get_tags_by_names(conn: Conn, names: list[str]) -> list[Tag]:
    tags = []
    for name in names:
        tag_id = db.fetchone(conn, stmt.Get_tag_id, (name,))
        tags.append(Tag(id=tag_id, name=name))
    return tags


def update_tags(
    conn: Conn, cfg: BlogConfig, article_id: str, new_tags: list[str]
) -> None:
    old_tags = db.get_tag_names(conn, article_id)
    diff_tags = model.tags_diff(new_tags, old_tags)
    db.insert_tags(conn, diff_tags["to_add"], article_id)
    db.delete_tags(conn, article_id, diff_tags["to_del"])
    tags = get_tags_by_names(conn, diff_tags["to_add"] + diff_tags["to_del"])
    render_tags(conn, cfg, tags)


def show_cats(conn: Conn, show_notes: bool) -> None:
    cats = db.get_all_cats(conn)
    if not cats:
        print("There is no category. (尚未添加文章类别)")
        return

    for cat in cats:
        print(f"[id:{cat.id}] {cat.name}")
        if show_notes and cat.notes:
            print("---------")
            print(f"{cat.notes}")
        print()


def show_tags(conn: Conn) -> None:
    tags = db.get_all_tags(conn)
    if not tags:
        print("There is no tag. (尚未添加标签)")
        return

    tag_names = [tag.name for tag in tags]
    print(f"Tags: {', '.join(tag_names)}")


def extract_tags(s: str) -> Result[list[str], str]:
    sep_pattern = re.compile(r"[#;,，；\s]")
    forbid_pattern = re.compile(
        r"[`~!@$%^&*()\-=+\[\]{}\\|:\'\"<>.?/]"
    )

    matched = forbid_pattern.search(s)
    if matched is not None:
        return Err(f"Forbidden character (标签不可包含): {matched.group(0)}")

    tags = sep_pattern.split(s)
    not_empty = [tag for tag in tags if tag]
    return Ok(model.unique_str_list(not_empty))


def get_tag_name(tag_text: str) -> Result[str, str]:
    match extract_tags(tag_text):
        case Err(err):
            return Err(err)
        case Ok(tags):
            if not tags:
                return Err(f"Not Valid (不是有效标签名): {tag_text}")
            return Ok(tags[0])


def rename_tag(conn: Conn, tag_text: str, old_name: str) -> None:
    match get_tag_name(tag_text):
        case Err(e):
            print(e)
        case Ok(new_name):
            match db.rename_tag(conn, new_name, old_name):
                case Err(e):
                    print(e)
                case Ok():
                    print("已更改标签名，请执行 'boke gen -all' 重新生成 HTML 文件。")
