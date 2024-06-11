from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import Query

from eredesscraper.meta import supported_workflows, supported_databases


class RunWorkflowRequest(BaseModel):
    """
    A Pydantic model representing a request to run a workflow.

    Attributes:
        workflow (str): The workflow to run. Default is "current".
        db (list, optional): The databases to use. Default is None.
        month (int, optional): The month to load. Required for `select` workflow. Default is None.
        year (int, optional): The year to load. Required for `select` workflow. Default is None.
        delta (bool, optional): If True, load only the most recent data points. Default is False.
        download (bool, optional): If True, keeps the source data file after loading. Default is False.
    """
    workflow: str = Query("current", description=f"Specify one of the supported workflows: {supported_workflows}")
    db: Optional[list] = Query(None, description=f"Specify one of the supported databases: {supported_databases}")
    month: Optional[int] = Query(None, description="Specify the month to load (1-12). [Required for `select` workflow]")
    year: Optional[int] = Query(None, description="Specify the year to load (YYYY). [Required for `select` workflow]")
    delta: Optional[bool] = Query(False, description="Load only the most recent data points")
    download: Optional[bool] = Query(False, description="If set, keeps the source data file after loading")


class WorkflowRequestRecord(BaseModel):
    """
    A Pydantic model representing a record of a workflow request.

    Attributes:
        task_id (UUID): The unique identifier of the task.
        workflow (str): The workflow that was requested.
        db (str, optional): The database that was used. Default is None.
        month (int, optional): The month that was loaded. Default is None.
        year (int, optional): The year that was loaded. Default is None.
        delta (bool, optional): If True, only the most recent data points were loaded. Default is False.
        download (bool, optional): If True, the source data file was kept after loading. Default is False.
    """
    task_id: UUID
    workflow: str
    db: Optional[list]
    month: Optional[int]
    year: Optional[int]
    delta: Optional[bool]
    download: Optional[bool]


class TaskstatusRecord(BaseModel):
    """
    A Pydantic model representing a record of a task status.

    Attributes:
        task_id (UUID): A UUID4. The unique identifier of the task.
        status (str): The status of the task.
        file (str, optional): The file associated with the task. Default is None.
        created (datetime, optional): The creation time of the task. Default is None.
        updated (datetime, optional): The last update time of the task. Default is None.
    """
    task_id: UUID
    status: str
    file: Optional[bytes]
    created: Optional[datetime]
    updated: Optional[datetime]


class ConfigLoadRequest(BaseModel):
    """
    A Pydantic model representing a request to load a configuration.

    Attributes:
        config (str): The configuration to load.
    """
    config: str


class ConfigSetRequest(BaseModel):
    """
    A Pydantic model representing a request to set a configuration.

    Attributes:
        key (str): The key of the configuration to set.
        value (str): The value to set for the configuration.
    """
    key: str
    value: str


class Eredes(BaseModel):
    """
    Represents an Eredes object.

    Attributes:
        nif (int): The NIF (Número de Identificação Fiscal) of the Eredes.
        pwd (str): The password associated with the Eredes.
        cpe (str): The CPE (Customer Premises Equipment) of the Eredes.
    """
    nif: int
    pwd: str
    cpe: str


class InfluxDB(BaseModel):
    """
    Represents a connection to an InfluxDB database.

    Attributes:
        host (str): The hostname or IP address of the InfluxDB server.
        port (int): The port number of the InfluxDB server.
        bucket (str): The name of the bucket in the InfluxDB database.
        org (str): The name of the organization in the InfluxDB database.
        token (str): The authentication token for accessing the InfluxDB database.
    """
    host: str
    port: int
    bucket: str
    org: str
    token: str


class Config(BaseModel):
    """
    Represents the configuration settings for the application.
    
    Attributes:
        eredes (Eredes): The Eredes configuration.
        influxdb (InfluxDB): The InfluxDB configuration.
    """
    eredes: Eredes
    influxdb: InfluxDB
