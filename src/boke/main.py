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

    print(f"\n           [boke] {__file__}" f"\n        [version] {__version__}")

    with db.connect() as conn:
        util.show_cfg(conn)

    print("           [repo] https://github.com/ahui2016/boke")
    print()
    ctx.exit()


def set_author(ctx: click.Context, _, value):
    if not value or ctx.resilient_parsing:
        return
    check_init(ctx)

    with db.connect() as conn:
        db.set_author(conn, value)

    print(f"[Author] {value}")
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
    "--set-author",
    help="Update the default author.",
    expose_value=False,
    callback=set_author,
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

    match util.get_md_file_title(filename):
        case Err(e):
            print(e)
        case Ok(title):
            if db.execute(db.exists, stmt.Article_title, (title,)):
                print(f"Error. Title Exists (文章标题已存在):\n{title}")
                print(f"\n(提示：文章标题不可重复，请修改文件 {filename} 的第一行)")
                ctx.exit()
            gui.PostForm.exec(filename, title)


@cli.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "theme",
    "-theme",
    type=click.Choice(["simple", "water", "mvp", "unchanged"]),
    default="unchanged",
    help="Set the CSS style theme.",
)
@click.option(
    "ignore_assets",
    "-ia",
    "--ignore-assets",
    is_flag=True,
    default=False,
    help="Do not copy assets (e.g. CSS, LICENSE)",
)
@click.option(
    "force_all",
    "-all",
    "--force-all",
    is_flag=True,
    default=False,
    help="Force to re-generate all articles.",
)
@click.pass_context
def gen(ctx: click.Context, theme: str, ignore_assets: bool, force_all: bool):
    """Generate your articles to HTML/RSS.

    生成 HTML 与 RSS 静态文件
    """
    check_init(ctx)

    if (not os.listdir(db.output_dir)) and (theme == 'unchanged'):
        print("Error: Missing option '-theme'.")
        ctx.exit()

    with db.connect() as conn:
        generate_all(conn, theme.lower(), ignore_assets, force_all)


@cli.command(context_settings=CONTEXT_SETTINGS)
@click.argument("filename", nargs=1, type=click.Path(exists=True))
@click.option("date_only", "--date-only", is_flag=True, help="Set the article's update date to now.")
@click.pass_context
def update(ctx: click.Context, filename:os.PathLike, date_only: bool):
    """Update an article. (更新文章)

    Examples:
    
    boke update --date-only ./posted/aaa.md
    """
    check_init(ctx)

    article_id = Path(filename).stem

    if date_only:
        with db.connect() as conn:
            util.update_article_date(conn, article_id)
        ctx.exit()
    
    match util.get_md_file_title(filename):
        case Err(e):
            print(e)
        case Ok(title):
            if util.check_title_when_update(article_id, title, filename).is_err():
                ctx.exit()
            gui.UpdateForm.exec(filename, title)
