# E-REDES Scraper
## Description
This is a web scraper that collects data from the E-REDES website and can upload it to a database.
Since there is no exposed interface to the data, this web scraper was developed as approach to collect it programatically.
A high-level of the process is:
1. The scraper collects the data from the E-REDES website.
2. A file with the energy consumption readings is downloaded.
3. [ Optional ] The file is parsed and the data is uploaded to the selected database. 
4. [ Optional ] A feature supporting only the insertion of "deltas" is available.

> This package supports E-REDES website available at time of writing 23/10/2023. 
> The entrypoint for the scraper is the page https://balcaodigital.e-redes.pt/login.

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
ers run -w last_month -d influxdb --delta

# get readings from May
ers run -w select_month -d influxdb -m 5
```

### Docker:
```bash
# get readings from May

# docker args
docker run --rm -v config.yml:/config.yml \
  # latest `ers` image
  ghcr.io/rf-santos/eredesscraper:latest \
  # calling `ers` 
  ers run -w current_month -d influxdb
```

### Python:

```python
from eredesscraper.workflows import switchboard
from pathlib import Path

# get deltas from current month readings
switchboard(name="current_month",
            db="influxdb",
            config_path=Path("./config.yml")y
            delta=True)

# get readings from May
switchboard(name="select_month",
            db="influxdb",
            config_path=Path("./config.yml"),
            month=5)
```

## Features
### Available workflows:
- `current_month`: Collects the current month consumption.
- `previous_month`: Collects the previous month consumption data.
- `select_month`: Collects the consumption data from an arbitrary month parsed by the user.

### Available databases:
- `influxdb`: Loads the data in an InfluxDB database. (https://docs.influxdata.com/influxdb/v2/get-started/)

## Roadmap
- [X] ~~Add workflow for retrieving previous month data.~~
- [X] ~~Add workflow for retrieving data form an arbitrary month.~~
- [X] ~~Build CLI~~.
- [ ] Containerize app.
- [ ] Documentation.
- [ ] Add CI/CD.
- [ ] Add logging.
- [ ] Add tests.
- [ ] Add runtime support for multiple CPEs.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
See [LICENSE](LICENSE) file.