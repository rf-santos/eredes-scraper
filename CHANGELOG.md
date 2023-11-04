# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.7] - 2023-11-04

### Changed
- Nothing changed. Testing CI

## [0.1.6] - 2023-11-04

### Changed
- CI/CD for automatic deployment to PyPI

### Fixed
- Bug with `agent.py` tmp directory creation

## [0.1.5] - 2023-11-03

### Added

- Initial release
- CLI: `ers` command automatically installed
- Python API
- Support for YAML configuration file
- Support for following workflows:
  - `current_month`: Collects the current month consumption.
  - `previous_month`: Collects the previous month consumption data.
  - `select_month`: Collects the consumption data from an arbitrary month parsed by the user.
- Support for following databases:
  - `influxdb`: Loads the data in an InfluxDB database. (https://docs.influxdata.com/influxdb/v2/get-started/)