import uvicorn

from eredesscraper.utils import db_conn
from eredesscraper.backend import db_path


def start_api_server(port: int = 8778, host: str = "localhost", reload: bool = True, debug: bool = False):

    db_active = db_conn(db_path.absolute().as_posix())

    assert db_active, "Database connection failed. Please check the connection and try again."

    uvicorn.run("eredesscraper.api:app", host=host, port=port, log_level="debug" if debug else "info", reload=reload)


if __name__ == "__main__":
    start_api_server()
