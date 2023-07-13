import typer

from .c1 import cli as c1_cli


cli = typer.Typer()
cli.add_typer( c1_cli, name='1c' )

