import click
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
        click.echo("请先使用 'boke init' 命令进行初始化")
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
def init_command():
    """Initialize your blog.

    初始化博客。请在一个空文件夹内执行 'boke init'。
    """
    util.init_blog("", "")


@cli.command(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def haha(ctx: click.Context):
    """Try GUI"""
    check_init(ctx)
    gui.hello()
