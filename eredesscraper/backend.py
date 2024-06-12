from pathlib import Path
import duckdb
from importlib.resources import files
from eredesscraper.models import TaskstatusRecord, WorkflowRequestRecord

db_path = Path.home() / ".ers" / "ers.db"


class DuckDB:
    """
    Represents a connection to a DuckDB database.

    Args:
        db_path (str): The path to the DuckDB database file.

    Attributes:
        db_path (str): The path to the DuckDB database file.
        conn: The connection object to the DuckDB database.

    Methods:
        __init__: Initializes a DuckDB object.
        __del__: Closes the connection when the object is destroyed.
        query: Executes the given SQL query on the database connection.
        insert: Inserts a new row into the specified table with the given data.
        update: Updates records in the specified table based on the given set and where clauses.
        insert_workflow_request: Inserts a workflow request record into the 'workflowrequests' table.
        insert_taskstatus: Inserts a task status record into the 'taskstatus' table.
        update_taskstatus: Updates the task status record in the database.
        get_taskstatus: Retrieves the task status from the database based on the given task ID.
        destroy: Closes the connection and deletes the database file.
    """

    def __init__(self, db_path: str = db_path.absolute().as_posix()):
        """
        Initializes a DuckDB object.

        Args:
            db_path (str): The path to the DuckDB database file.

        Returns:
            None
        """
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)

        self.init_script = files("eredesscraper").joinpath("ddb_init.sql").read_text()

        self.conn.execute(self.init_script)

        wf = self.conn.execute("SELECT * FROM information_schema.tables WHERE table_name = 'workflowrequests'").fetchone()
        ts = self.conn.execute("SELECT * FROM information_schema.tables WHERE table_name = 'taskstatus'").fetchone()

        assert wf is not None, "Database initialization failed"
        assert ts is not None, "Database initialization failed"

    def __del__(self):
        """
        Closes the connection when the object is destroyed.

        This method is automatically called when the object is garbage collected.
        It ensures that the connection to the database is properly closed.
        """
        self.conn.close()

    def query(self, query: str, values: list = None):
            """
            Executes the given SQL query on the database connection.

            Args:
                query (str): The SQL query to execute.
                values (list, optional): The values to be used in the query (if any). Defaults to None.

            Returns:
                result: The result of the query execution.
            """
            result = self.conn.execute(query, values) if values else self.conn.execute(query)

            return result

    def insert(self, table: str, data: dict):
        """
        Insert a new row into the specified table with the given data.

        Args:
            table (str): The name of the table to insert into.
            data (dict): A dictionary containing the column names as keys and the corresponding values.

        Returns:
            None
        """
        num_values = '?, ' * (len(data.keys()) - 1) + '?'
        keys = ', '.join(data.keys())
        values = list(data.values())
        sql = f"INSERT INTO {table} ({keys}) VALUES ({num_values})"
        self.conn.execute(sql, values)

    def update(self, table: str, set_clause: str, where_clause: str, values: list):
        """
        Update records in the specified table based on the given set and where clauses.

        Args:
            table (str): The name of the table to update.
            set_clause (str): The SET clause of the SQL statement.
            where_clause (str): The WHERE clause of the SQL statement.
            values (list): The values to be used in the SQL statement.

        Returns:
            None
        """
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        self.conn.execute(sql, values)

    def insert_workflow_request(self, record: WorkflowRequestRecord):
        """
        Inserts a workflow request record into the 'workflowrequests' table.

        Args:
            record (WorkflowRequestRecord): The workflow request record to be inserted.

        Returns:
            bool: True if the record was successfully inserted, False otherwise.
        """

        record = {k: v for k, v in record.model_dump().items() if v is not None}

        self.insert("workflowrequests", record)
        return True

    def insert_taskstatus(self, record: TaskstatusRecord):
        """
        Inserts a task status record into the 'taskstatus' table.

        Args:
            record (TaskstatusRecord): The task status record to be inserted.

        Returns:
            bool: True if the record was successfully inserted, False otherwise.
        """

        record = {k: v for k, v in record.model_dump().items() if v is not None}

        self.insert("taskstatus", record)
        return True

    def update_taskstatus(self, record: TaskstatusRecord):
        """
        Update the task status record in the database.

        Args:
            record (TaskstatusRecord): The task status record to be updated.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        record_dict = record.model_dump()

        set_clause = ', '.join(f"{k} = ?" for k, v in record_dict.items() if k != 'task_id' and v is not None)

        where_clause = f"task_id = '{record_dict['task_id']}'"

        values = [v for k, v in record_dict.items() if k != 'task_id' and v is not None]

        self.update("taskstatus", set_clause, where_clause, values)

        return True
    
    def get_taskstatus(self, task_id: str):
            """
            Retrieves the task status from the database based on the given task ID.

            Args:
                task_id (str): The ID of the task.

            Returns:
                result: The task status retrieved from the database.
            """
            result = self.query(f"SELECT * FROM taskstatus WHERE task_id = ?", [task_id])
            return result
    
    def destroy(self):
            """
            Closes the connection and deletes the database file.

            Returns:
                bool: True if the operation is successful, False otherwise.
            """
            self.conn.close()
            db_path.unlink(missing_ok=True)
            return True
