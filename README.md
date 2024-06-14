# E-REDES Scraper
## Description
This is a web scraper that collects data from the E-REDES website and can upload it to a database.
Since there is no exposed programatic interface to the data, this web scraper was developed as approach to collect it.
A high-level of the process is:
1. The scraper collects the data from the E-REDES website.
2. A file with the energy consumption readings is downloaded.
3. [ Optional ] The file is parsed and the data is uploaded to the selected database. 
4. [ Optional ] A feature supporting only the insertion of "deltas" is available.

> This package supports E-REDES website available at time of writing 14/06/2023. 
> The entrypoint for the scraper is the page https://balcaodigital.e-redes.pt/consumptions/history.

## Installation
The package can be installed using pip:
```bash
pip install eredesscraper
```

## Configuration
Usage is based on a YAML configuration file.  
`config.yml` holds the credentials for the E-REDES website and 
the database connection. Currently, **only InfluxDB is supported** as a database sink.  

### Template `config.yml`:
```yaml
eredes:
  # eredes credentials
  nif: <my-eredes-nif>
  pwd: <my-eredes-password>
  # CPE to monitor. e.g. PT00############04TW (where # is a digit). CPE can be found in your bill details
  cpe: PT00############04TW


influxdb:
  # url to InfluxDB.  e.g. http://localhost or https://influxdb.my-domain.com
  host: http://localhost
  # default port is 8086
  port: 8086
  bucket: <my-influx-bucket>
  org: <my-influx-org>
  # access token with write access
  token: <token>
```

## Usage
### CLI:
```bash
ers config load "/path/to/config.yml"

# get current month readings
ers run -d influxdb

# get only deltas from last month readings 
ers run -w previous -d influxdb --delta

# get readings from May 2023
ers run -w select -d influxdb -m 5 -y 2023

# start an API server
ers server -H "localhost" -p 8778 --reload -S <path/to/database>
```

### API:

For more details refer to the OpenAPI documentation or the UI endpoints available at `http://<host>:<port>/docs` and `http://<host>:<port>/redoc`

```bash
# main methods:

# load an ers configuration 
# different options to load available:
# - directly in the request body,
# - download remote file,
# - upload local file
curl -X 'POST' \
  'http://localhost:8778/config/upload' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@my-config.yml'


# run sync workflow
curl -X 'POST' \
  'http://localhost:8778/run' \
  -H 'Content-Type: application/json' \
  -d '{
  "workflow": "current"
}'

# run async workflow
curl -X 'POST' \
  'http://localhost:8778/run_async' \
  -H 'Content-Type: application/json' \
  -d '{
  "workflow": "select",
  "db": [
    "influxdb"
  ],
  "month": 5,
  "year": 2023,
  "delta": true,
  "download": true
}'

# get task status (`task_id` returned in /run_async response body)
curl -X 'GET' \
  'http://localhost:8778/status/<task_id>'

# download the file retrieved by the workflow
curl -X 'GET' \
  'http://localhost:8778/download/<task_id>'
```

### Python:

```python
from eredesscraper.workflows import switchboard
from pathlib import Path

# get deltas from current month readings
switchboard(config_path=Path("./config.yml"),
            name="current",
            db=list("influxdb"),
            delta=True,
            keep=True)

# get readings from May 2023
switchboard(config_path=Path("./config.yml"),
            name="select",
            db=list("influxdb"),
            month=5,
            year=2023)
```

## Features
### Available workflows:
- `current`: Collects the current month consumption.
- `previous`: Collects the previous month consumption data.
- `select`: Collects the consumption data from an arbitrary month parsed by the user.

### Available databases:
- `influxdb`: Loads the data in an InfluxDB database. (https://docs.influxdata.com/influxdb/v2/get-started/)

## Troubleshooting
Since this is a web scraper, it is subject to changes in the E-REDES website.
The scraper might stop working due to changes in the website structure, blocking mechanisms, etc...

### Tips:
- Check if the playwright browser is being blocked by the website. Usually, CAPTCHA mechanisms are the cause of this.
  - Try to run the scraper with the `-H` flag. This will open a browser window and you can see what is happening.
  - Try using `xvfb-run` to run the scraper. (ex: `xvfb-run ers run -w current -d influxdb`)
- Check the logs for any errors or hints on what might be causing the issue. (by default in the `~/.ers` folder).
  - Running the CLI with the `--debug` flag will debug info to the terminal.
- Check if you are running the API with the `-r/--reload` flag. This is known to break the application.

## Roadmap
- [X] ~~Add workflow for retrieving previous month data.~~
- [X] ~~Add workflow for retrieving data form an arbitrary month.~~
- [X] ~~Build CLI~~.
- [X] ~~Build API~~
- [ ] ~~Containerize app~~.
- [ ] Documentation.
- [X] ~~Add CI/CD~~.
- [ ] Add logging.
- [X] ~~Add tests~~ (limited coverage).
- [ ] Add runtime support for multiple CPEs.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
See [LICENSE](LICENSE) file.
