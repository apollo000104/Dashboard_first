import typer
import yaml
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

from modules.db import psql
from modules.cronjob import cronjob_kyiv_detailed as ck


cli = typer.Typer()

@cli.command()
def update(
    db_config_path: Path = typer.Option( 'configs/local.yaml', help='Path to db config file'),
    start_date: Optional [ str ] = typer.Option( pd.to_datetime('2023-01-01').date() , help='Start timestamp' ),
    end_date: Optional [ str ] = typer.Option(datetime.now().date() , help='Start timestamp' ),
    doc_number: Optional [ str ] = typer.Option(None , help='Document number' ),
    phone: Optional [ str ] = typer.Option(None , help='Customer phone' ),
    vin: Optional [ str ] = typer.Option(None , help='Customer VIN' ),

):
    with open( db_config_path, 'r' ) as f:
        db_config = yaml.safe_load( f )

    db = psql.PostgreSQLDB(
        host=db_config[ 'host' ],
        port=db_config[ 'port' ],
        type=db_config[ 'type' ],
        db=db_config[ 'db' ],
        credentials=db_config[ 'credentials' ],
    )

    adapter = ck.CronjobKyiv()
    adapter.update(
        db,
        start_date,
        end_date,
        doc_number,
        phone,
        vin
    )