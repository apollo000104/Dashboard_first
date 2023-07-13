import os
import typing
import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extras
import psycopg2.pool
from tenacity import retry, wait_exponential, stop_after_attempt
from .base import BaseDB, register_db


@register_db
class PostgreSQLDB( BaseDB ):
    def __init__( self, **kwargs ):
        BaseDB.__init__( self, **kwargs )

        # so we can insert these numpy dtypes
        psycopg2.extensions.register_adapter(
            np.int64, psycopg2._psycopg.AsIs
        )
        psycopg2.extensions.register_adapter(
            np.float32, psycopg2._psycopg.AsIs
        )

        self.pool = psycopg2.pool.SimpleConnectionPool(
            1,
            4,
            host=self.config.host,
            port=self.config.port,
            database=self.config.db,
            user=self.credentials[ 'user' ],
            password=self.credentials[ 'password' ],
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5
        )

    @retry( stop=stop_after_attempt( 3 ), wait=wait_exponential() )
    def execute( self, query: str ) -> typing.List[ typing.Dict ]:
        conn = self.pool.getconn()
        results = []
        with conn.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        ) as cursor:
            cursor.execute( query )
            conn.commit()
            if cursor.description is not None and cursor.rowcount > 0:
                results = cursor.fetchall()
        self.pool.putconn( conn )
        return results

    def insert_dataframe(
        self, table: str, df: pd.DataFrame, batch_size: int = 10000
    ):
        df_dict = df.to_dict( 'split' )
        columns = [ f'"{col}"' for col in df_dict[ 'columns' ] ]
        data = df_dict[ 'data' ]

        conn = self.pool.getconn()
        with conn.cursor() as cursor:
            for idx in range( 0, len( data ), batch_size ):
                batch = data[ idx:idx + batch_size ]
                query = f"INSERT INTO {table} ({','.join( columns )}) VALUES %s"
                psycopg2.extras.execute_values( cursor, query, batch )
                conn.commit()
        self.pool.putconn( conn )

    def fetch_dataframe( self, query: str ) -> pd.DataFrame:
        conn = self.pool.getconn()
        with conn.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        ) as cursor:
            cursor.execute( query )
            rows = cursor.fetchall()
            df = pd.DataFrame( rows )
        self.pool.putconn( conn )
        return df

    def shell( self, filename: str = None ):
        if filename is None:
            os.system(
                f"PGPASSWORD={self.credentials['password']} psql -h {self.config.host} -p {self.config.port} -U {self.credentials['user']} -d {self.config.db}"
            )
        else:
            os.system(
                f"PGPASSWORD={self.credentials['password']} psql -h {self.config.host} -p {self.config.port} -U {self.credentials['user']} -d {self.config.db} -f {filename}"
            )
