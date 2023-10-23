# E-REDES Scraper
## Description
This is a web scraper that collects data from the E-REDES website and stores it in a database.
Since there is no exposed interface to the data, the web scraper is the only approach available to collect it.
A high-level of the process is:
1. The scraper collects the data from the E-REDES website.
2. A file with the energy consumption readings is downloaded.
3. The file is parsed and the data is compared to the data in the database to determine if there are new readings.
4. If there are new readings, they are stored in the database.

> :information_source: This package supports E-REDES website available at time of writing 23/10/2023. 
> The entrypoint for the scraper is the page https://balcaodigital.e-redes.pt/login.

## Installation
The package can be installed using pip:
```bash
pip install EredesScraper
```

## Configuration
Usage is based on a YAML configuration file.  
A `config.yml` is used to specify the credentials for the E-REDES website and 
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
### Example usage:
```python
from EredesScraper.workflows import run

run(workflow="current_month_consumption",
    db="influxdb",
    config_path="./config.yml")
```

### Available workflows:
- `current_month_consumption`: Collects the current month consumption data from the E-REDES website.

### Available databases:
- `influxdb`: Stores the data in an InfluxDB database. (https://docs.influxdata.com/influxdb/v2/get-started/)

## Roadmap
- [ ] Add support for other workflows.
- [ ] Add support for other databases.
- [ ] Build CLI.
- [ ] Add tests.
- [ ] Add CI/CD.
- [ ] Add logging.
- [ ] Add support for multiple CPEs.
- [ ] Add support for multiple accounts.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
See [LICENSE](LICENSE) file.