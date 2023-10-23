import datetime
from pathlib import Path

import influxdb_client
import pandas as pd
from influxdb_client import WritePrecision
from influxdb_client.client.exceptions import InfluxDBError
from influxdb_client.client.write_api import SYNCHRONOUS

from EredesScraper.utils import parse_monthly_consumptions


class InfluxDB:
    def __init__(self,
                 token,
                 org,
                 bucket,
                 host: str = "http://localhost",
                 port: int = 8086):
        self.__bucket = bucket
        self.__host = host
        self.__port = port
        self.__url = str(self.__host) + ':' + str(self.__port)
        self.__token = token
        self.__org = org
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
        The ``connect`` method connects to the InfluxDB database using the specified host, port, token and org.

        :return: None
        :doc-author: Ricardo Filipe dos Santos
        """
        try:
            self.client = influxdb_client.InfluxDBClient(url=self.__url,
                                                         token=self.__token,
                                                         org=self.__org,
                                                         debug=self.debug,
                                                         enable_gzip=False)
        except InfluxDBError:
            print("Error connecting to the InfluxDB database")
        finally:
            print(f"Connected to the InfluxDB database at {self.__url}")

        return None

    def load(self, source_data: Path, cpe_code) -> None:
        """
        The ``load`` method loads the data parsed as a pandas DataFrame into the InfluxDB database.

        :param source_data: Specify the path to the source data .XLSX file to be loaded
        :return: None
        :doc-author: Ricardo Filipe dos Santos
        """

        self.client.write_api(write_options=SYNCHRONOUS).write(bucket=self.__bucket,
                                                               org=self.__org,
                                                               record=self.delta(source_data, cpe_code=cpe_code),
                                                               data_frame_measurement_name='kW',
                                                               data_frame_tag_columns=['cpe'],
                                                               data_frame_field_columns=['consumption'],
                                                               data_frame_timestamp='date_time',
                                                               data_frame_write_precision=WritePrecision.S)

        self.client.close()

        # remove the source_data .XLSX file and staging area
        try:
            source_data.unlink()
            Path.rmdir(Path.cwd() / 'tmp')
        except PermissionError:
            print("Permission denied to remove the staging area for the Scraper")

        print(f"Loaded data from {source_data} into the InfluxDB database")

        return None

    def get_last_insert(self, cpe_code: str) -> datetime:
        """
        The ``get_last_insert`` method returns the ``datetime`` object representing the latest data point present in
        the InfluxDB database. The query filters the data points by the CPE code.

        :param cpe_code: Specify the CPE code of the data point to be returned
        :return: A Datetime object with the latest data point timestamp
        :doc-author: Ricardo Filipe dos Santos
        """

        query = (f'''import "date"
from(bucket: "{self.__bucket}")
  |> range(start: 1989-05-11T01:10:00Z, stop: now())
  |> filter(fn: (r) => r["_measurement"] == "kW")
  |> filter(fn: (r) => r["_field"] == "consumption")
  |> filter(fn: (r) => r["cpe"] == "{cpe_code}")
  |> last() |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")''')

        result = self.client.query_api().query_data_frame(org=self.__org, query=query)

        # test if result is empty
        if result.empty:
            return datetime.datetime(
                1989,
                5,
                11,
                0,
                0,
                0,
                tzinfo=datetime.timezone(datetime.timedelta(hours=1))
            )
        else:
            return result['_time'].iloc[0]

    def delta(self, source_data: Path, cpe_code: str) -> pd.DataFrame:
        """
        The ``delta`` method uses ``parse_monthly_consumptions`` function to get the source data into a pandas
        DataFrame and keep only the values that are more recent than the result of the ``get_last_insert`` method.
        The method returns the filtered DataFrame holding the most recent data not present in the DB bucket.

        :param source_data: Specify the source data to be filtered
        :param cpe_code: Specify the CPE code of the data point to be returned
        :return: A pandas DataFrame with the filtered data
        :doc-author: Ricardo Filipe dos Santos
        """

        # get the source data into a pandas DataFrame
        df = parse_monthly_consumptions(source_data, cpe_code=cpe_code)

        # filter out the data points that are already present in the DB bucket
        df = df[df.index > self.get_last_insert(cpe_code=cpe_code)]

        self.data = df
        return df
