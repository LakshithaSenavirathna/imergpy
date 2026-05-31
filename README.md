# imergpy

`imergpy` is a Python package and local web interface for downloading NASA GPM IMERG precipitation data through NASA Earthdata/GES DISC. It can extract point rainfall time series and compute grid-cell average rainfall for selected countries or square areas.

<div style="border: 2px solid #39ff14; background: #071b0b; color: #eaffea; padding: 16px; border-radius: 10px; box-shadow: 0 0 22px rgba(57,255,20,0.45);">

<h2 style="margin-top: 0;">Download NASA Rainfall Data With 2 Lines</h2>

<ul>
  <li>Download NASA IMERG satellite rainfall as a time series.</li>
  <li>Excel file is saved automatically.</li>
  <li>Use Point, Country Average, or Square Region Average.</li>
  <li>Available from 1998-01-01 to today, depending on NASA product availability.</li>
  <li>Supports half-hourly, daily, and monthly data.</li>
  <li>No Linux or advanced technical knowledge needed.</li>
</ul>

</div>

## Two-Line Python Download

After installation, download point rainfall with:

```python
import imergpy
excel_path, records = imergpy.get_precipitation(6.9271, 79.8612, "2025-11-27 00:00", "2025-11-27 23:30", "EARTHDATA_USERNAME", "EARTHDATA_PASSWORD", run_type="late", freq="hhr")
```

Replace `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` with your NASA Earthdata login. The result is saved as an Excel file.

## Quick Start(MacOS/Windows/Linux)

Install:

```bash
pip install imergpy
```

Open the web app:

```bash
python -m imergpy.cli
```

Your browser should open automatically. Enter your NASA Earthdata username/password in the local page and choose a point, country, or square area.

## Two Ways To Use

- Method 1: Use Python code.
- Method 2: Use the local web interface.
- Both methods save Excel output automatically.

## Features

- Local web UI launched with `python -m imergpy.cli`
- Python API for scripted workflows
- Point, country, and square-area selection in the web map
- Grid-cell average precipitation for country and square-area selections
- Half-hourly, daily, and monthly IMERG products
- Early, Late, and Final IMERG run types where available
- Excel export with separate `Start Time` and `End Time` columns
- Basic rainfall plotting and statistics utilities

## Web UI

```bash
python -m imergpy.cli
```

## Python API Example

```python
import imergpy

excel_path, records = imergpy.get_precipitation(
    lat=6.9271,
    lon=79.8612,
    start_datetime="2025-11-27 00:00",
    end_datetime="2025-11-27 23:30",
    username="EARTHDATA_USERNAME",
    password="EARTHDATA_PASSWORD",
    run_type="late",
    freq="hhr",
    interp_method="nearest",
)

print(excel_path)
```

## Example Files

- `examples/point_download.py`
- `examples/country_japan_average.py`
- `examples/square_area_average.py`

Accepted date formats:

- `YYYY-MM`
- `YYYY-MM-DD`
- `YYYY-MM-DD HH:MM`

## NASA Earthdata Credentials

You need a free NASA Earthdata account. After creating the account, authorize GES DISC under Earthdata authorized applications.

For the easiest first test, replace `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` directly in the examples above. For shared scripts, keep credentials private and avoid uploading passwords to GitHub.

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

## Upgrade

To upgrade to a newer `imergpy` version:

```bash
pip install --upgrade imergpy
```

## License

MIT License. Developed by Lakshitha S. Senavirathna.
