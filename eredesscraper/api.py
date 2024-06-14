import io
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from importlib.resources import files

import requests
import yaml
from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse, StreamingResponse
from typer import get_app_dir

from eredesscraper._version import get_version
from eredesscraper.backend import DuckDB
from eredesscraper.meta import supported_workflows, supported_databases
from eredesscraper.models import WorkflowRequestRecord, TaskstatusRecord, RunWorkflowRequest, ConfigSetRequest, \
    ConfigLoadRequest, Config, WorkflowAsyncResponse, WorkflowResponse
from eredesscraper.utils import parse_config, flatten_config, struct_config, infer_type, file2blob
from eredesscraper.workflows import switchboard

appdir = get_app_dir(app_name="ers")
config_path = Path(appdir) / "cache" / "config.yml"
openapi_spec = files("eredesscraper").joinpath("openapi.json")
openapi_url = Path(str(openapi_spec))

app = FastAPI(
    title="E-REDES Scraper API",
    description="An API to interact with the E-REDES Scraper application",
    version=get_version()
)


def get_db():
    ddb = DuckDB()

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
        ts.updated = datetime.now()

        ddb.update_taskstatus(ts)

    except Exception as e:

        ts.status = f"failed: {str(e)}"
        ts.updated = datetime.now()

        ddb.update_taskstatus(ts)


@app.get("/version", summary="Show the current version")
def get_version_api():
    return {"version": get_version()}


@app.get("/info", summary="Get information about the available workflows and databases")
def get_info():
    return {"workflows": supported_workflows, "databases": supported_databases}


@app.post("/run", summary="Run the scraper workflow")
def run_workflow(request: RunWorkflowRequest, ddb=Depends(get_db), response_model=WorkflowResponse):
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
        return response_model(
            task_id=task_id,
            workflow=request.workflow,
            databases=request.db,
            source_data=result.source_data,
            staging_area=result.staging_area,
            status=ts.status,
            timestamp=datetime.now(),
        )


@app.post("/run_async", summary="Run the scraper workflow asynchronously")
def run_workflow_async(background_tasks: BackgroundTasks, request: RunWorkflowRequest, ddb=Depends(get_db), response_model=WorkflowAsyncResponse):
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

        return response_model(**{"task_id": task_id, "status": ts.status, "detail": "Workflow queued successfully"})


    except Exception as e:
        ts.status = f"failed: {str(e)}"
        ts.created = None
        ts.updated = datetime.now()

        ddb.update_taskstatus(ts)

        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{task_id}", summary="Get the status of a task", response_model=TaskstatusRecord)
def get_status(task_id: str, ddb=Depends(get_db)):
    record = ddb.get_taskstatus(task_id).fetchone()

    if record is None:
        raise HTTPException(status_code=404, detail="Task not found")

    ts = TaskstatusRecord(task_id=record[0],
                          status=record[1],
                          file="File found. Download file with the `download` API method" if record[2] else None,
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
    filename = f"{ts.created.strftime('%Y-%m-%d')}_{ts.task_id.hex.split('-')[0]}_readings.xlsx"

    return StreamingResponse(io.BytesIO(ts.file), media_type="application/octet-stream",
                             headers={"Content-Disposition": f"attachment; filename={filename}"})


@app.post("/config/load", summary="Loads a YAML string as a config file into the program")
def load_config(request: ConfigLoadRequest):
    try:

        tmp_config = yaml.safe_load(request.config)

        assert Config(**tmp_config), "Config file schema is not valid"

        with open(config_path, "w") as f:
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

            # assert tmp_config schema is the same as the Config model
            try:
                Config(**tmp_config)
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

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
        "url": "https://raw.githubusercontent.com/rf-santos/eredes-scraper/master/static/logo_small.jpeg"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

with open(openapi_url, "w") as f:
    json.dump(app.openapi(), f, indent=2)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
