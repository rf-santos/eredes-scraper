# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-06-13

### 💥 Breaking issues
  - Selenium-based web scraper replaced by non-Selenium scraper.
  - Implemented an API (FastAPI): Run `ers server [OPTIONS]` to use it.
  - The API uses DuckDB to persist usage data.
  - The `select` workflow requires a `year` and `month` argument.
  - Removed docker support (issues bypassing bot detection)

### 👍 Improvements
  - EredesScraper class now uses playwright instead of selenium for browser automation.
  - Function `parse_monthly_consumptions` renamed to `parse_readings_influx`.
  - Method delta migrated from db_clients.InfluxDB class to main application workflow.
  - Added new utility functions.

### ⚙ Minor updates:
  - Updated dependencies.
  - Code clean up, refactor, and improvements.
  - New tests added.
  - Removed unused or unnecessary codes.

### 🐞 Fixes:
  - Several bug fixes and error handling improved.

## [0.1.9] - 2024-01-20

### 💥 Breaking issues
- A website update broke the workflows that targeted previous months. The issue was fixed 🥳

### 👍 Improvements
- The `previous_month` and `select_month` workflows were changed to `previous` and `select`, respectively.
- The `select` workflow now requires a `year` argument.

## [0.1.8] - 2023-12-12

### 💥 Breaking issues
- File downloaded from E-REDES had an extra column, and `parse_readings_influx` function was failing. It is now more resilient to future column additions.

### 👍 Improvements
- Standerdized all dates to UTC before loading data.
- Removed `influxdb` as a default value in the `ers` CLI
- Started working on containerization
- Updated tests & documentation

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
