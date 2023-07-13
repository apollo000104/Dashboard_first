import functools
import os
import json
import pandas as pd
import pydantic
import threading
import typing_extensions
import yaml
from typing import Union, Optional


_db_registry = {}

_dbs = {}


def register_db( cls ):
    assert "DB" in cls.__name__
    db_name = cls.__name__
    if db_name in _db_registry:
        raise Exception( f"Duplicate db {db_name}" )
    else:
        _db_registry[ db_name ] = cls
    return cls


def get_db( type, **kwargs ):
    if type in _db_registry:
        db_type = _db_registry[ type ]
    else:
        raise Exception( f"Unknown db {type}" )
    db = db_type( type=type, **kwargs )
    return db


class DBConfig( pydantic.BaseModel ):
    type: typing_extensions.Literal[ 'PostgreSQLDB', 'MongoDB', 'BigQueryDB' ]
    host: Optional[ str ]
    port: Optional[ int ]
    credentials: Union[ str, dict ]
    db: str
    args: dict = {}


def _acquire_write_lock( func ):
    @functools.wraps( func )
    def wrapper( self, *args, **kwargs ):
        try:
            self.conn_lock.acquire()
            result = func( self, *args, **kwargs )
            self.conn_lock.release()
            return result
        except Exception as e:
            self.conn_lock.release()
            raise e

    return wrapper


class BaseDB:
    def __init__( self, **kwargs ):
        self.config = DBConfig( **kwargs )

        # three ways to load the credentials: Vault, file, or env
        self.credentials = {}
        if 'env' in self.config.credentials:
            env_config = self.config.credentials[ 'env' ]
            self.credentials[ 'user' ] = os.environ[ env_config[ 'username' ] ]
            self.credentials[ 'password' ] = os.environ[
                env_config[ 'password' ] ]
        elif 'file' in self.config.credentials:
            file_config = self.config.credentials[ 'file' ]
            self.credentials = json.load( open( file_config[ 'path' ] ) )
        elif 'user' in self.config.credentials and 'password' in self.config.credentials:
            self.credentials[ 'user' ] = self.config.credentials[ 'user' ]
            self.credentials[ 'password' ] = self.config.credentials[
                'password' ]
        else:
            raise Exception( 'No credentials provided or unknown format' )

        self.conn_lock = threading.Lock()

    @_acquire_write_lock
    def execute( self, query: str ) -> list[ dict ]:
        raise NotImplementedError

    @_acquire_write_lock
    def insert_dataframe(
        self, collection: str, df: pd.DataFrame, batch_size: int = 10000
    ):
        raise NotImplementedError

    @_acquire_write_lock
    def shell( self, filename: Optional[ str ] = None ):
        raise NotImplementedError


def get_dbs( db_config_path: str ) -> dict[ str, BaseDB ]:
    global _dbs
    if not _dbs:
        with open( db_config_path ) as f:
            db_config = yaml.safe_load( f )
            for db_name in db_config:
                db = get_db( **db_config[ db_name ] )
                _dbs[ db_name ] = db
    return _dbs
