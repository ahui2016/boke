import os
from pathlib import Path
import click
from result import Err, Ok

from . import stmt
from . import db
from .generate import generate_all
from . import util
from . import gui
from . import (
    __version__,
    __package_name__,
)

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


def check_init(ctx: click.Context) -> None:
    if not db.db_path.exists():
        click.echo("请先进入已初始化的文件夹，或使用 'boke init' 命令进行初始化")
        ctx.exit()


def show_info(ctx: click.Context, _, value):
    if not value or ctx.resilient_parsing:
        return
    check_init(ctx)

    print(
        f"\n           [boke] {__file__}" f"\n        [version] {__version__}"
    )

    db.execute(util.show_cfg)

    print("           [repo] https://github.com/ahui2016/boke")
    print()
    ctx.exit()


def set_blog_info(ctx: click.Context, _, value):
    if not value or ctx.resilient_parsing:
        return
    check_init(ctx)
    gui.UpdateBlogForm.exec()
    ctx.exit()


@click.group(invoke_without_command=True)
@click.help_option("-h", "--help")
@click.version_option(
    __version__,
    "-v",
    "-V",
    "--version",
    package_name=__package_name__,
    message="%(prog)s version: %(version)s",
)
@click.option(
    "-i",
    "--info",
    is_flag=True,
    help="Show informations about config and more.",
    expose_value=False,
    callback=show_info,
)
@click.option(
    "--blog-info",
    is_flag=True,
    help="Update informations of the blog.",
    expose_value=False,
    callback=set_blog_info,
)
@click.pass_context
def cli(ctx: click.Context):
    """boke: Static blog generator (静态博客生成器)

    https://pypi.org/project/boke/
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit()


# 以上是主命令
############
# 以下是子命令


@cli.command(context_settings=CONTEXT_SETTINGS, name="init")
@click.pass_context
def init_command(ctx: click.Context):
    """Initialize your blog.

    初始化博客。请在一个空文件夹内执行 'boke init'。
    """
    if util.dir_not_empty():
        print(f"Error. Folder Not Empty: {db.cwd}")
        ctx.exit()

    gui.InitBlogForm.exec()


@cli.command(context_settings=CONTEXT_SETTINGS)
@click.argument("filename", nargs=1, type=click.Path(exists=True))
@click.pass_context
def post(ctx: click.Context, filename: os.PathLike):
    """Post an article. (发表文章)

    Example: boke post ./drafts/aaa.md
    """
    check_init(ctx)

    draft = Path(filename)
    if util.not_in_drafts(draft):
        ctx.exit()

    match util.get_md_file_title(draft):
        case Err(e):
            print(e)
        case Ok(title):
            if db.execute(db.exists, stmt.Article_title, (title,)):
                print(f"Error. Title Exists (文章标题已存在):\n{title}")
                print(f"\n(提示：文章标题不可重复，请修改文件 {filename} 的第一行)")
                ctx.exit()
            gui.PostForm.exec(draft, title)


@cli.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "theme",
    "-theme",
    type=click.Choice(["simple", "water", "mvp", "unchanged"]),
    default="unchanged",
    help="Set the CSS style theme.",
)
@click.option(
    "copy_assets",
    "--copy-assets",
    is_flag=True,
    default=False,
    help="Copy all assets (e.g. CSS, LICENSE)",
)
@click.option(
    "force_all",
    "-all",
    "--all-articles",
    is_flag=True,
    default=False,
    help="Force to re-generate all articles.",
)
@click.pass_context
def gen(ctx: click.Context, theme: str, copy_assets: bool, force_all: bool):
    """Generate your articles to HTML/RSS.

    生成 HTML 与 RSS 静态文件
    """
    check_init(ctx)

    if (not os.listdir(db.output_dir)) and (theme == "unchanged"):
        print("Error: Missing option '-theme'.")
        ctx.exit()

    with db.connect() as conn:
        generate_all(conn, theme.lower(), copy_assets, force_all)


@cli.command(context_settings=CONTEXT_SETTINGS)
@click.argument("filename", nargs=1, type=click.Path(exists=True))
@click.option(
    "date_only",
    "--date-only",
    is_flag=True,
    help="Set the article's update date to now.",
)
@click.pass_context
def update(ctx: click.Context, filename: os.PathLike, date_only: bool):
    """Update an article. (更新文章)

    Examples:

    boke update --date-only ./posted/aaa.md
    """
    check_init(ctx)

    art_file = Path(filename)
    article_id = art_file.stem

    id_exists = db.execute(db.exists, stmt.Article_id, (article_id,))
    if not id_exists:
        print(f"Not Found. 找不到 ID: {article_id}")
        print("(提示: 'boke update' 命令只能用来更新 posted 文件夹里的文件。)")
        ctx.exit()

    if date_only:
        with db.connect() as conn:
            util.update_article_date(conn, article_id)
        ctx.exit()

    match util.get_md_file_title(art_file):
        case Err(e):
            print(e)
        case Ok(title):
            if util.check_title_when_update(
                article_id, title, art_file
            ).is_err():
                ctx.exit()
            gui.UpdateForm.exec(art_file, title)


@cli.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "cat_list", "-l", "--list", is_flag=True, help="List out all categories."
)
@click.option(
    "show_notes",
    "-sn",
    "--show-notes",
    is_flag=True,
    help="Show notes of categories.",
)
@click.argument("cat_id", nargs=1, required=False)
@click.option("delete", "--delete", is_flag=True, help="Delete the category.")
@click.pass_context
def cat(
    ctx: click.Context,
    cat_list: bool,
    show_notes: bool,
    cat_id: str,
    delete: bool,
):
    """List out all categories, or modify a category.

    列出全部文章类别，或更改类别信息。

    Examples:

    boke cat -l/--list  (显示文章类别列表)

    boke cat -l -sn     (显示文章类别列表，并且包含类别说明)

    boke cat v5zt       (更改 id:v5zt 的类别的信息)
    """
    check_init(ctx)

    with db.connect() as conn:
        if cat_list:
            util.show_cats(conn, show_notes)
        elif cat_id:
            if len(cat_id) != 4:
                print(f"id 错误（应由 4 个字符组成）: {cat_id}")
                return

            if db.get_cat(conn, cat_id).err():
                print(f"Not Found: {cat_id}")
                print("（提示：可使用命令 'boke cat -l' 查看文章类别的 id）")
                return

            cat = db.get_cat(conn, cat_id).unwrap()

            if delete:
                print(f"{cat.id}: {cat.name}")
                click.confirm("Confirm deletion (确认删除)", abort=True)
                match db.delete_cat(conn, cat.id):
                    case Err(e):
                        print(e)
                    case Ok():
                        print("OK.")
            else:
                gui.CatForm.exec(cat)
        else:
            click.echo(ctx.get_help())


@cli.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "tag_list", "-l", "--list", is_flag=True, help="List out all tags."
)
@click.option("name", "-name", help="Specify a tag.")
@click.option("new_name", "-rename", "--rename-to", help="A new name for the tag.")
@click.option("delete", "-delete", help="Delete the tag.")
@click.pass_context
def tag(
    ctx: click.Context,
    tag_list: bool,
    name: str,
    new_name: str,
    delete: bool,
):
    """List out all tags, or rename a tag.

    列出全部标签，或更改标签名称。

    Examples:

    boke tag -l/--list  (列出全部标签)

    boke tag -name old_name -rename new_name  (标签名从原来的 old_name 改为 new_name)
    """
    check_init(ctx)

    with db.connect() as conn:
        if tag_list:
            util.show_tags(conn)
            ctx.exit()
        elif name and new_name:
            if not db.exists(conn, stmt.Tag_name, (name,)):
                print(f"Not Exist: {name}")
            else:
                print(f"Rename: {name} => {new_name}")
                click.confirm("Confirm rename (确认更改标签名称)", abort=True)
                util.rename_tag(conn, new_name, name)
        elif delete:
            print(f"Delete the tag: {delete}")
        else:
            click.echo(ctx.get_help())
