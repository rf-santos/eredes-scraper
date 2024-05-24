from pathlib import Path

import requests
import yaml
import json
from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.responses import FileResponse
from fastapi.openapi.utils import get_openapi
from uuid import uuid4
from typer import get_app_dir
from datetime import datetime

from eredesscraper._version import get_version
from eredesscraper.meta import supported_workflows, supported_databases
from eredesscraper.utils import parse_config, flatten_config, struct_config, infer_type, file2blob
from eredesscraper.workflows import switchboard
from eredesscraper.models import WorkflowRequestRecord, TaskstatusRecord, RunWorkflowRequest, ConfigSetRequest, \
    ConfigLoadRequest
from eredesscraper.backend import DuckDB, db_path

appdir = get_app_dir(app_name="ers")
config_path = Path(appdir) / "cache" / "config.yml"
openapi_url = Path(__file__).parent.parent / "schemas" / "openapi.json"

app = FastAPI(
    title="E-REDES Scraper API",
    description="An API to interact with the E-REDES Scraper application",
    version=get_version()
)


def get_db(db_path: str = db_path):
    ddb = DuckDB(db_path=db_path)

    return ddb


def run_workflow_task(task_id: uuid4, config_path: Path, name: str, db: list, month: int, year: int, delta: bool,
                      keep: bool, ddb: DuckDB = None):
    
    ts = TaskstatusRecord(task_id=task_id,
                          status="running",
                          file=None,
                          created=None,
                          updated=datetime.now())
    
    ddb.update_taskstatus(ts)

    try:
        result = switchboard(
            config_path=config_path,
            name=name,
            db=db,
            month=month,
            year=year,
            delta=delta,
            keep=keep,
            quiet=True,
            uuid=task_id

        )

        ts.status = "completed"
        ts.file = file2blob(result.source_data) if result.source_data else None
        ts.updated=datetime.now()

        ddb.update_taskstatus(ts)

    except Exception as e:
        
        ts.status = f"failed: {str(e)}"
        ts.updated=datetime.now()

        ddb.update_taskstatus(ts)

@app.get("/version", summary="Show the current version")
def get_version_api():
    return {"version": get_version()}


@app.get("/info", summary="Get information about the available workflows and databases")
def get_info():
    return {"workflows": supported_workflows, "databases": supported_databases}


@app.post("/run", summary="Run the scraper workflow")
def run_workflow(request: RunWorkflowRequest, ddb=Depends(get_db)):
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="Config file not found. Please load it first.")

    task_id = uuid4().__str__()

    wf = WorkflowRequestRecord(task_id=task_id,
                               workflow=request.workflow,
                               db=request.db or [],
                               month=request.month,
                               year=request.year,
                               delta=request.delta,
                               download=request.download)

    ddb.insert_workflow_request(wf)

    ts = TaskstatusRecord(task_id=task_id,
                          status="running",
                          file=None,
                          created=datetime.now(),
                          updated=None)

    ddb.insert_taskstatus(ts)

    try:
        result = switchboard(
            config_path=config_path.resolve(),
            name=request.workflow,
            db=request.db or [],
            month=request.month,
            year=request.year,
            delta=request.delta,
            keep=True if request.download else False,
            quiet=True,
            uuid=task_id
        )
    except Exception as e:
        ts = TaskstatusRecord(task_id=task_id,
                              status=f"failed: {str(e)}",
                              file=None,
                              created=None,
                              updated=datetime.now())

        ddb.update_taskstatus(ts)

        raise HTTPException(status_code=500, detail=str(e))

    ts.status = "completed"
    ts.created = None
    ts.updated = datetime.now()
    ts.file = file2blob(result.source_data) if result.source_data else None

    ddb.update_taskstatus(ts)

    ddb.__del__()

    if result.source_data and request.download:
        return FileResponse(result.source_data, media_type="application/octet-stream",
                            filename=result.source_data.name)
    else:
        return dict(result.__dict__)


@app.post("/run_async", summary="Run the scraper workflow asynchronously")
def run_workflow_async(background_tasks: BackgroundTasks, request: RunWorkflowRequest, ddb=Depends(get_db)):
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="Config file not found. Please load it first.")

    task_id = uuid4()

    wf = WorkflowRequestRecord(task_id=task_id,
                               workflow=request.workflow,
                               db=request.db or [],
                               month=request.month,
                               year=request.year,
                               delta=request.delta,
                               download=request.download)
    
    ddb.insert_workflow_request(wf)

    ts = TaskstatusRecord(task_id=task_id,
                          status="queued",
                          file=None,
                          created=datetime.now(),
                          updated=None)
    
    ddb.insert_taskstatus(ts)

    try:
        background_tasks.add_task(
            run_workflow_task,
            task_id=task_id,
            config_path=config_path.resolve(),
            name=request.workflow,
            db=request.db or [],
            month=request.month,
            year=request.year,
            delta=request.delta,
            keep=True if request.download else False,
            ddb=ddb
        )

        return {"task_id": task_id, "status": ts.status, "detail": "Workflow queued successfully"}


    except Exception as e:
        ts.status = f"failed: {str(e)}"
        ts.created = None
        ts.updated = datetime.now()

        ddb.update_taskstatus(ts)

        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{task_id}", summary="Get the status of a task")
def get_status(task_id: str, ddb=Depends(get_db)):
    
    record = ddb.get_taskstatus(task_id).fetchone()    

    if record is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    ts = TaskstatusRecord(task_id=record[0],
                          status=record[1],
                          file=record[2],
                          created=record[3],
                          updated=record[4])

    return dict(ts.model_dump())

@app.get("/download/{task_id}", summary="Get the file extracted from async run")
def get_file(task_id: str, ddb=Depends(get_db)):
    
    record = ddb.get_taskstatus(task_id).fetchone()

    if record is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    ts = TaskstatusRecord(task_id=record[0],
                            status=record[1],
                            file=record[2],
                            created=record[3],
                            updated=record[4])
    
    
    filename = f"{ts.created.strftime('%Y-%m-%d')}_{ts.task_id.split('-')[0]}_readings.xlsx"
    
    return FileResponse(ts.file, media_type="application/octet-stream", filename=filename)
    

@app.post("/config/load", summary="Loads a local config file into the program")
def load_config(request: ConfigLoadRequest):
    try:
        config_path = Path(request.config).resolve()

        Path.mkdir(Path(appdir) / "cache", parents=True, exist_ok=True)

        cache = Path(appdir) / "cache"

        with open(config_path, "r") as f:
            tmp_config = yaml.safe_load(f)

        with open(cache / "config.yml", "w") as f:
            yaml.dump(tmp_config, f)

        return {"detail": "Config file loaded successfully"}

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found. Please check the path and try again.")


@app.post("/config/remote", summary="Loads a remote config file from a URL into the program")
async def load_config_from_url(url: str):
    try:
        Path.mkdir(Path(appdir) / "cache", parents=True, exist_ok=True)

        cache = Path(appdir) / "cache"

        response = requests.get(url)

        if response.status_code == 200:
            tmp_config = yaml.safe_load(response.text)

            with open(cache / "config.yml", "w") as f:
                yaml.dump(tmp_config, f)

            return {"detail": "Config file loaded successfully from URL"}
        else:
            raise HTTPException(status_code=404,
                                detail="File not found at provided URL. Please check the URL and try again.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/config/upload", summary="Uploads a config file into the program")
async def upload_config(file: UploadFile = File(...)):
    try:
        Path.mkdir(Path(appdir) / "cache", parents=True, exist_ok=True)

        cache = Path(appdir) / "cache"

        contents = await file.read()
        tmp_config = yaml.safe_load(contents)

        with open(cache / "config.yml", "w") as f:
            yaml.dump(tmp_config, f)

        return {"detail": "Config file uploaded successfully"}

    except FileNotFoundError:
        return {"detail": "File not found"}


@app.get("/config/show", summary="Show the current configuration")
def show_config():
    try:
        config = parse_config(config_path)
        return config
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No config file found. Please load a config file first.")


@app.post("/config/set", summary="Set a configuration value")
def set_config(request: ConfigSetRequest):
    value = infer_type(request.value)

    try:
        config = flatten_config(parse_config(config_path))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No config file found. Please load a config file first.")

    if request.key not in config:
        raise HTTPException(status_code=404, detail=f"Unsupported key {request.key} not found in config file.")

    config[request.key] = value

    with open(config_path, "w") as f:
        yaml.dump(struct_config(config), f)

    return {"detail": f"Key {request.key} set to {value}"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="E-REDES Scraper API",
        version=get_version(),
        description="An API to interact with the E-REDES Scraper application",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://raw.githubusercontent.com/rf-santos/eredes-scraper/master/static/logo.jpeg"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

with open(openapi_url, "w") as f:
    json.dump(app.openapi(), f, indent=2)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)