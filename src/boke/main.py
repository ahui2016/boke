import click
from result import Err, Ok
from . import db
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
def haha(ctx: click.Context, filename: str):
    """Try GUI"""
    check_init(ctx)

    match util.get_md_file_title(filename):
        case Err(e):
            print(e)
        case Ok(title):
            gui.PostForm.exec(filename, title)
