from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4
from pathlib import Path

from fastapi import Query
from pydantic import BaseModel, Field

from eredesscraper.meta import supported_workflows, supported_databases

class ERSSession():
    """
    Represents an ERSSession object.

    Attributes:
        session_id (str): The ID of the session.
        workflow (str): The workflow associated with the session.
        databases (list): A list of databases associated with the session.
        source_data (Path | None): The path to the source data, or None if not available.
        staging_area (Path | None): The path to the staging area, or None if not available.
        status (str): The status of the session.
        timestamp (datetime): The timestamp of the session.

    Methods:
        __str__(): Returns a string representation of the ERSSession object.
        __repr__(): Returns a string representation that can be used to recreate the ERSSession object.
        __eq__(other): Checks if the ERSSession object is equal to another ERSSession object.
        __ne__(other): Checks if the ERSSession object is not equal to another ERSSession object.
        __lt__(other): Checks if the ERSSession object is less than another ERSSession object.
        __le__(other): Checks if the ERSSession object is less than or equal to another ERSSession object.
        __gt__(other): Checks if the ERSSession object is greater than another ERSSession object.
        __ge__(other): Checks if the ERSSession object is greater than or equal to another ERSSession object.
        __hash__(): Returns the hash value of the ERSSession object.
    """

    def __init__(self, session_id: str, workflow: str, databases: list, source_data: Path | None, status: str,
                 timestamp: datetime):
        self.session_id = session_id
        self.workflow = workflow
        self.databases = databases
        self.source_data = source_data
        self.staging_area = source_data.parent if source_data else None
        self.status = status
        self.timestamp = timestamp

    def __str__(self):
        return f"Session ID: {self.session_id}\nWorkflow: {self.workflow}\nDatabases: {self.databases}\nSource Data: {self.source_data}\nStaging Area: {self.staging_area}\nStatus: {self.status}\nTimestamp: {self.timestamp}\n"

    def __repr__(self):
        return f"ERSSession(session_id={self.session_id}, workflow={self.workflow}, databases={self.databases}, source_data={self.source_data}, staging_area={self.staging_area}, status={self.status}, timestamp={self.timestamp})"

    def __eq__(self, other):
        if not isinstance(other, ERSSession):
            return NotImplemented
        return self.session_id == other.session_id and self.workflow == other.workflow and self.databases == other.databases and self.source_data == other.source_data and self.staging_area == other.staging_area and self.status == other.status and self.timestamp == other.timestamp

    def __ne__(self, other):
        if not isinstance(other, ERSSession):
            return NotImplemented
        return self.session_id != other.session_id or self.workflow != other.workflow or self.databases != other.databases or self.source_data != other.source_data or self.staging_area != other.staging_area or self.status != other.status or self.timestamp != other.timestamp

    def __lt__(self, other):
        if not isinstance(other, ERSSession):
            return NotImplemented
        return self.timestamp < other.timestamp

    def __le__(self, other):
        if not isinstance(other, ERSSession):
            return NotImplemented
        return self.timestamp <= other.timestamp

    def __gt__(self, other):
        if not isinstance(other, ERSSession):
            return NotImplemented
        return self.timestamp > other.timestamp

    def __ge__(self, other):
        if not isinstance(other, ERSSession):
            return NotImplemented
        return self.timestamp >= other.timestamp

    def __hash__(self):
        return hash((self.session_id, self.workflow, self.databases, self.source_data, self.staging_area, self.status,
                     self.timestamp))
    

class WorkflowAsyncResponse(BaseModel):
    """
    A Pydantic model representing an asynchronous response to a workflow request.

    Attributes:
        task_id (UUID): The unique identifier of the task.
        status (str): The status of the workflow that was requested.
        detail (str): Additional information about the async request.
    """
    task_id: UUID = Field(examples=[uuid4()])
    status: str = Field(examples=["queued", "running", "completed", "failed"])
    detail: str = Field(examples=["Workflow queued successfully"])


class WorkflowResponse(BaseModel):
    task_id: UUID = Field(examples=[uuid4()])
    workflow: str = Field(examples=supported_workflows)
    databases: list = Field(examples=[supported_databases])
    source_data: Path | None = Field(examples=["/path/to/source/data"])
    staging_area: Path | None = Field(examples=["/path/to/staging/area"])
    status: str = Field(examples=["queued", "running", "completed", "failed"])
    timestamp: datetime = Field(examples=[datetime.now()])


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
    workflow: str = Query("current", description=f"Specify one of the supported workflows: {supported_workflows}", examples=supported_workflows)
    db: Optional[list[str]] = Query(None, description=f"Specify one of the supported databases: {supported_databases}", examples=[supported_databases])
    month: Optional[int] = Query(None, description="Specify the month to load (1-12). [Required for `select` workflow]", examples=[1, 12])
    year: Optional[int] = Query(None, description="Specify the year to load (YYYY). [Required for `select` workflow]", examples=[2024])
    delta: Optional[bool] = Query(False, description="Load only the most recent data points", examples=[False, True])
    download: Optional[bool] = Query(False, description="If set, keeps the source data file after loading", examples=[False, True])


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
    task_id: UUID = Field(examples=[uuid4()])
    workflow: str = Field(examples=supported_workflows)
    db: Optional[list] = Field(examples=[supported_databases])
    month: Optional[int] = Field(examples=[1, 12])
    year: Optional[int] = Field(examples=[2024])
    delta: Optional[bool] = Field(examples=[False, True])
    download: Optional[bool] = Field(examples=[False, True])


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
    task_id: UUID = Field(examples=[uuid4()])
    status: str = Field(examples=["queued", "running", "completed", "failed"])
    file: Optional[bytes] = Field(examples=["/path/to/file"])
    created: Optional[datetime] = Field(examples=[datetime.now()])
    updated: Optional[datetime] = Field(examples=[datetime.now() + timedelta(minutes=5)])
    error_message: Optional[str] = Field(examples=["Error message"])


class ConfigLoadRequest(BaseModel):
    """
    A Pydantic model representing a request to load a configuration from a YAML string.

    Attributes:
        config (str): The configuration in YAML format.
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
