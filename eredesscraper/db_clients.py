import datetime
from pathlib import Path

import influxdb_client
import pandas as pd
import typer
from influxdb_client import WritePrecision
from influxdb_client.client.exceptions import InfluxDBError
from influxdb_client.client.write_api import SYNCHRONOUS
from pytz import UTC

from eredesscraper.utils import readings2df
from eredesscraper.backend import db_path


class Sink2InfluxDB:
    """
    The `Sink2InfluxDB` class represents a client for connecting to and interacting with an InfluxDB database.

    Args:
    -----
    token: str
        The authentication token for accessing the InfluxDB database.
    org: str
        The organization name associated with the InfluxDB database.
    bucket: str
        The name of the bucket in the InfluxDB database where the data will be stored.
    host: str, optional
        The host URL of the InfluxDB server. Default is "http://localhost".
    port: int, optional
        The port number of the InfluxDB server. Default is 8086.
    quiet: bool, optional
        If True, suppresses the output messages. Default is False.

    Attributes:
    -----------
    client: influxdb_client.InfluxDBClient
        The InfluxDB client object used for connecting to the database.
    last_insert: datetime
        The timestamp of the last data point inserted into the database.
    data: pd.DataFrame
        The data frame holding the most recent data not present in the database.
    debug: bool
        If True, enables debug mode for the InfluxDB client.

    Methods:
    --------
    connect() -> None:
        Connects to the InfluxDB database using the specified host, port, token, and org.

    load(source_data: Path, cpe_code: str, delta: bool = False) -> None:
        Loads the data parsed as a pandas DataFrame into the InfluxDB database.

    get_last_insert(cpe_code: str) -> datetime:
        Returns the timestamp of the latest data point present in the InfluxDB database.

    delta(source_data: Path, cpe_code: str) -> pd.DataFrame:
        Filters the source data to keep only the most recent data not present in the InfluxDB database.

    """
    def __init__(self,
                 token,
                 org,
                 bucket,
                 host: str = "http://localhost",
                 port: int = 8086,
                 quiet: bool = False):
        self.__bucket = bucket
        self.__host = host
        self.__port = port
        self.__url = str(self.__host) + ':' + str(self.__port)
        self.__token = token
        self.__org = org
        self.__quiet = quiet
        self.client = None
        self.last_insert = None
        self.data = None
        self.debug = False

    # define a setter method for the host property
    @property
    def host(self):
        return self.__host

    @host.setter
    def host(self, value):
        if isinstance(value, str):
            self.__host = value
        else:
            raise TypeError("Expected a string value")

    # define a setter method for the port property
    @property
    def port(self):
        return self.__port

    @port.setter
    def port(self, value):
        if isinstance(value, str):
            self.__port = value
        else:
            raise TypeError("Expected a string value")

    # define a setter method for the token property
    @property
    def token(self):
        return self.__token

    @token.setter
    def token(self, value):
        if isinstance(value, str):
            self.__token = value
        else:
            raise TypeError("Expected a string value")

    # define a setter method for the org property
    @property
    def org(self):
        return self.__org

    @org.setter
    def org(self, value):
        if isinstance(value, str):
            self.__org = value
        else:
            raise TypeError("Expected a string value")

    def connect(self) -> None:
        """
        Connects to the InfluxDB database using the provided URL, token, and organization.

        Raises:
            InfluxDBError: If there is an error connecting to the InfluxDB database.

        Returns:
            None
        """
        try:
            self.client = influxdb_client.InfluxDBClient(url=self.__url,
                                                            token=self.__token,
                                                            org=self.__org,
                                                            debug=self.debug,
                                                            enable_gzip=False)
        except InfluxDBError:
            if not self.__quiet:
                typer.echo("💥\tError connecting to the InfluxDB database")
        finally:
            if not self.__quiet:
                typer.echo(f"🔗\tConnected to the InfluxDB database at {self.__url}")

        return None

    def load(self, source_data: Path, cpe_code: str, delta: bool = False) -> None:
        """
        The ``load`` method loads the data parsed as a pandas DataFrame into the InfluxDB database.

        Args:
        -----
        source_data: Path
            Specify the source data to be loaded into the database
        cpe_code: str
            Specify the CPE code of the data point to be loaded
        delta: bool
            Specify whether to load the entire file or only the most recent data points (default: False).
            This is useful when the source data is a monthly file and the data points are updated daily.
            Otherwise, it will not fill the gaps with missing data points (e.g. missing data points between the most
            recent data point in the DB and previous data points not present in the DB).

        Returns:
        --------
            None
        """
        if delta:
            records = self.delta(source_data, cpe_code=cpe_code)
        else:
            records = readings2df(source_data, cpe_code=cpe_code)

        self.client.write_api(write_options=SYNCHRONOUS).write(bucket=self.__bucket,
                                                               org=self.__org,
                                                               record=records,
                                                               data_frame_measurement_name='kW',
                                                               data_frame_tag_columns=['cpe'],
                                                               data_frame_field_columns=['consumption'],
                                                               data_frame_timestamp='date_time',
                                                               data_frame_write_precision=WritePrecision.S)

        self.client.close()

        return None

    def get_last_insert(self, cpe_code: str) -> datetime:
        """
        Retrieves the timestamp of the last insert for a given CPE code.

        Args:
            cpe_code (str): The CPE code to retrieve the last insert for.

        Returns:
            datetime: The timestamp of the last insert.

        """
        query = (f'''import "date"
    from(bucket: "{self.__bucket}")
      |> range(start: 1989-05-11T01:10:00Z, stop: now())
      |> filter(fn: (r) => r["_measurement"] == "kW")
      |> filter(fn: (r) => r["_field"] == "consumption")
      |> filter(fn: (r) => r["cpe"] == "{cpe_code}")
      |> last() |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")''')

        result = self.client.query_api().query_data_frame(org=self.__org, query=query)

        if result.empty:
            last_insert = datetime.datetime(
                1989,
                5,
                11,
                0,
                0,
                0,
                tzinfo=UTC
            )
        else:
            last_insert = result['_time'].iloc[0]
            last_insert = last_insert.tz_convert(UTC)

        return last_insert

    def delta(self, source_data: Path, cpe_code: str) -> pd.DataFrame:
        """
        Calculates the delta between the source data and the data already present in the DB bucket.

        Args:
            source_data (Path): The path to the source data file.
            cpe_code (str): The CPE code.

        Returns:
            pd.DataFrame: The filtered DataFrame containing the delta between the source data and the data in the DB bucket.
        """

        # get the source data into a pandas DataFrame
        df = readings2df(source_data, cpe_code=cpe_code)

        # filter out the data points that are already present in the DB bucket
        df = df[df.index > self.get_last_insert(cpe_code=cpe_code)]

        self.data = df
        return df


class Sink2DuckDB:
    """
    The `Sink2DuckDB` class represents a client for connecting to and interacting with a DuckDB database.

    Args:
    -----
    db_path: Path
        The path to the DuckDB database file.
    quiet: bool, optional
        If True, suppresses the output messages. Default is False.

    Attributes:
    -----------
    db: str
        The name of the DuckDB database.
    table: str
        The name of the table in the DuckDB database where the data will be stored.
    db_path: Path
        The path to the DuckDB database file.
    conn: duckdb.DuckDBPyConnection
        The DuckDB connection object used for connecting to the database.
    last_insert: datetime
        The timestamp of the last data point inserted into the database.
    data: pd.DataFrame
        The data frame holding the most recent data not present in the database.

    Methods:
    --------
    connect() -> None:
        Connects to the DuckDB database using the specified path.

    load(source_data: Path, cpe_code: str, delta: bool = False) -> None:
        Loads the data parsed as a pandas DataFrame into the DuckDB database.

    get_last_insert(cpe_code: str) -> datetime:
        Returns the timestamp of the latest data point present in the DuckDB database.

    delta(source_data: Path, cpe_code: str) -> pd.DataFrame:
        Filters the source data to keep only the most recent data not present in the DuckDB database.

    """
    def __init__(self, db: str = "ers_readings", table: str = "readings", db_path: Path = db_path, quiet: bool = False):
        self.__db_path = db_path
        self.__quiet = quiet
        self.db = db
        self.table = table
        self.conn = None
        self.last_insert = None
        self.data = None

    # define a setter method for the db_path property
    @property
    def db_path(self):
        return self.__db_path

    @db_path.setter
    def db_path(self, value):
        if isinstance(value, Path):
            self.__db_path = value
        else:
            raise TypeError("Expected a Path object")

    def connect(self) -> None:
        """
        Connects to the DuckDB database using the specified path.

        Returns:
            None
        """
        import duckdb

        self.conn = duckdb.connect(str(self.__db_path))
        self.conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self.db}")
        self.conn.execute(f"USE {self.db}")
        self.conn.execute(f"CREATE TABLE IF NOT EXISTS {self.table} (date_time TIMESTAMP, consumption DOUBLE, cpe VARCHAR)")

        if not self.__quiet:
            typer.echo(f"🔗\tConnected to the DuckDB database at {self.__db_path}")

        return None

    def load(self, source_data: Path, cpe_code: str, delta: bool = False) -> None:
        """
        Loads the data parsed as a pandas DataFrame into the DuckDB database.

        Args:
        -----
        source_data: Path
            Specify the source data to be loaded into the database
        cpe_code: str
            Specify the CPE code of the data point to be loaded
        delta: bool
            Specify whether to load the entire file or only the most recent data points (default: False).
            This is useful when the source data is a monthly file and the data points are updated daily.
            Otherwise, it will not fill the gaps with missing data points (e.g. missing data points between the most
            recent data point in the DB and previous data points not present in the DB).

        Returns:
        --------
            None
        """
        if delta:
            records = self.delta(source_data, cpe_code=cpe_code)
        else:
            records = readings2df(source_data, cpe_code=cpe_code, ts2idx=False)

        self.conn.register("df", records)
        self.conn.execute(f"INSERT INTO readings SELECT * FROM df")

        self.conn.close()

        return None
    
    def get_last_insert(self, cpe_code: str) -> datetime:
        """
        Retrieves the timestamp of the last insert for a given CPE code.

        Args:
            cpe_code (str): The CPE code to retrieve the last insert for.

        Returns:
            datetime: The timestamp of the last insert.

        """
        query = f"SELECT MAX(date_time) FROM readings WHERE cpe = '{cpe_code}'"

        result = self.conn.execute(query).fetchall()

        if result[0][0] is None:
            last_insert = datetime.datetime(
                1989,
                5,
                11,
                0,
                0,
                0,
                tzinfo=UTC
            )
        else:
            last_insert = result[0][0]

        return last_insert
    
    def delta(self, source_data: Path, cpe_code: str) -> pd.DataFrame:
        """
        Calculates the delta between the source data and the data already present in the DB bucket.

        Args:
            source_data (Path): The path to the source data file.
            cpe_code (str): The CPE code.

        Returns:
            pd.DataFrame: The filtered DataFrame containing the delta between the source data and the data in the DB bucket.
        """

        # get the source data into a pandas DataFrame
        df = readings2df(source_data, cpe_code=cpe_code)

        # filter out the data points that are already present in the DB bucket
        df = df[df.index > self.get_last_insert(cpe_code=cpe_code)]

        self.data = df
        return df