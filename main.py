#!/usr/bin/env python
"""
cli commands to run different stages.
"""
import dotenv
import sys
from pathlib import Path

sys.path.append( str( Path( __file__ ).absolute().parents[ 0 ] ) )

import typer

dotenv.load_dotenv( '.env' )

from cli import c1

cli = typer.Typer()
cli.add_typer( c1.cli, name='c1' )

if __name__ == '__main__':
    cli()
