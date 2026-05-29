from datetime import datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
import xarray as xr

from imergpy.processor import extract_area_average, extract_precipitation


def _nc_path():
    tmp_dir = Path(__file__).resolve().parent / ".tmp"
    tmp_dir.mkdir(exist_ok=True)
    return tmp_dir / f"{uuid4().hex}.nc4"


def _write_dataset(path, precip_value):
    ds = xr.Dataset(
        data_vars={
            "precipitation": (
                ("time", "lat", "lon"),
                np.array([[[precip_value]]], dtype=float),
            )
        },
        coords={
            "time": pd.to_datetime(["2025-01-01T00:00:00"]),
            "lat": np.array([6.9]),
            "lon": np.array([79.8]),
        },
    )
    ds.to_netcdf(path)


def test_half_hourly_rate_is_converted_to_interval_total():
    nc_path = _nc_path()
    _write_dataset(nc_path, 10.0)

    result = extract_precipitation(nc_path, 6.9, 79.8, freq="hhr")

    assert result["Precipitation_mm_per_half_hour"] == 5.0
    assert result["Start_Time"].isoformat().startswith("2025-01-01T00:00:00")


def test_monthly_rate_is_converted_to_month_total():
    nc_path = _nc_path()
    _write_dataset(nc_path, 1.0)

    result = extract_precipitation(
        nc_path,
        6.9,
        79.8,
        freq="monthly",
        current_dt=datetime(2025, 1, 1),
    )

    assert result["Precipitation_mm_per_month"] == 24 * 31


def test_area_average_uses_grid_cell_mean():
    nc_path = _nc_path()
    ds = xr.Dataset(
        data_vars={
            "precipitation": (
                ("time", "lat", "lon"),
                np.array([[[1.0, 3.0], [5.0, 7.0]]], dtype=float),
            )
        },
        coords={
            "time": pd.to_datetime(["2025-01-01T00:00:00"]),
            "lat": np.array([6.0, 7.0]),
            "lon": np.array([80.0, 81.0]),
        },
    )
    ds.to_netcdf(nc_path)

    result = extract_area_average(
        nc_path,
        bbox=[5.5, 79.5, 7.5, 81.5],
        freq="daily",
        region_type="square",
        region_name="test_square",
    )

    assert result["Precipitation_mm_per_day"] == 4.0
    assert result["Grid_Cells_Averaged"] == 4


def test_area_average_handles_lon_lat_grid_order():
    nc_path = _nc_path()
    ds = xr.Dataset(
        data_vars={
            "precipitation": (
                ("time", "lon", "lat"),
                np.array([[[1.0, 5.0], [3.0, 7.0]]], dtype=float),
            )
        },
        coords={
            "time": pd.to_datetime(["2025-01-01T00:00:00"]),
            "lat": np.array([6.0, 7.0]),
            "lon": np.array([80.0, 81.0]),
        },
    )
    ds.to_netcdf(nc_path)

    result = extract_area_average(
        nc_path,
        bbox=[5.5, 79.5, 7.5, 81.5],
        freq="daily",
        region_type="country",
        region_name="test_country",
    )

    assert result["Precipitation_mm_per_day"] == 4.0
    assert result["Grid_Cells_Averaged"] == 4
