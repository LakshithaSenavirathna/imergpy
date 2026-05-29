# imergpy

`imergpy` is a Python package and local web interface for downloading NASA GPM IMERG precipitation data through NASA Earthdata/GES DISC. It can extract point rainfall time series and compute grid-cell average rainfall for selected countries or square areas.

## Quick Start

Install and open:

```bash
pip install imergpy
imergpy
```

Your browser should open automatically. Enter your NASA Earthdata username/password in the local page and choose a point, country, or square area.

## Features

- Local web UI launched with the `imergpy` command
- Python API for scripted workflows
- Point, country, and square-area selection in the web map
- Grid-cell average precipitation for country and square-area selections
- Half-hourly, daily, and monthly IMERG products
- Early, Late, and Final IMERG run types where available
- Excel export with separate `Start Time` and `End Time` columns
- Basic rainfall plotting and statistics utilities

## Web UI

```bash
imergpy
```

If the command is not available on Windows:

```bash
python -m imergpy.cli
```

If port `5000` is busy:

```powershell
$env:IMERGPY_PORT = "5001"
python -m imergpy.cli
```

## Python API Example

```python
import os
import imergpy

excel_path, records = imergpy.get_precipitation(
    lat=6.9271,
    lon=79.8612,
    start_datetime="2025-01",
    end_datetime="2025-01",
    username=os.environ["EARTHDATA_USERNAME"],
    password=os.environ["EARTHDATA_PASSWORD"],
    run_type="final",
    freq="monthly",
    interp_method="nearest",
)

print(excel_path)
```

Accepted date formats:

- `YYYY-MM`
- `YYYY-MM-DD`
- `YYYY-MM-DD HH:MM`

## NASA Earthdata Credentials

You need a free NASA Earthdata account. After creating the account, authorize GES DISC under Earthdata authorized applications.

Do not write credentials into scripts. Use environment variables:

```powershell
$env:EARTHDATA_USERNAME = "your_username"
$env:EARTHDATA_PASSWORD = "your_password"
```

## Legal And Data Use Notice

`imergpy` is an independent open-source tool. It is not developed, endorsed, or certified by NASA, GES DISC, or the GPM mission team.

Users are responsible for:

- creating and using their own NASA Earthdata account,
- accepting and following NASA/GES DISC data access terms,
- citing NASA GPM IMERG data correctly in reports, papers, and products,
- checking data quality, latency, and suitability before operational or scientific use,
- keeping Earthdata usernames, passwords, and tokens private.

This software is provided under the MIT License without warranty.

## Development

For local development:

```bash
git clone https://github.com/LakshithaSenavirathna/imergpy.git
cd imergpy
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Build package files:

```bash
python -m build
```

Publishing instructions are in [`PUBLISHING.md`](PUBLISHING.md).

## License

MIT License. Developed by Lakshitha S. Senavirathna.
