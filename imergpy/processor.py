import xarray as xr
import pandas as pd
import calendar
import numpy as np
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from matplotlib.path import Path


VALID_INTERPOLATION_METHODS = {"nearest", "linear", "cubic"}


def _time_bounds(time_val, freq, current_dt):
    t_start = time_val[0] if getattr(time_val, 'ndim', 0) > 0 else time_val
    if hasattr(t_start, 'tolist'):
        t_start = pd.to_datetime(t_start)

    if freq == "hhr":
        return t_start, t_start + timedelta(minutes=30), "Precipitation_mm_per_half_hour", 0.5
    if freq == "daily":
        return t_start, t_start + timedelta(days=1), "Precipitation_mm_per_day", 1.0
    if freq == "monthly":
        days_in_month = calendar.monthrange(current_dt.year, current_dt.month)[1]
        return t_start, t_start + relativedelta(months=1), "Precipitation_mm_per_month", 24 * days_in_month
    raise ValueError("freq must be 'hhr', 'daily', or 'monthly'.")


def _iter_polygons(geometry):
    if not geometry:
        return []
    if geometry.get("type") == "Polygon":
        return [geometry["coordinates"]]
    if geometry.get("type") == "MultiPolygon":
        return geometry["coordinates"]
    return []


def _geometry_mask(lats, lons, geometry):
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    points = np.column_stack([lon_grid.ravel(), lat_grid.ravel()])
    mask = np.zeros(points.shape[0], dtype=bool)

    for polygon in _iter_polygons(geometry):
        if not polygon:
            continue
        exterior = Path(polygon[0])
        poly_mask = exterior.contains_points(points)
        for hole in polygon[1:]:
            poly_mask &= ~Path(hole).contains_points(points)
        mask |= poly_mask

    return mask.reshape(lat_grid.shape)

def extract_precipitation(nc_path, target_lat, target_lon, method="nearest", freq="hhr", current_dt=None):
    """
    Reads the downloaded NetCDF file, extracts precipitation at the specified point,
    and returns a dictionary with the extracted data and proper units.
    Now includes Start_Time and End_Time.
    """
    if method not in VALID_INTERPOLATION_METHODS:
        raise ValueError("method must be 'nearest', 'linear', or 'cubic'.")
    if freq not in {"hhr", "daily", "monthly"}:
        raise ValueError("freq must be 'hhr', 'daily', or 'monthly'.")
    if freq == "monthly" and current_dt is None:
        raise ValueError("current_dt is required when freq='monthly'.")

    try:
        ds = xr.open_dataset(nc_path)
        
        if method == "nearest":
            point_data = ds.sel(lat=target_lat, lon=target_lon, method="nearest")
            actual_lat = float(point_data['lat'].values.item())
            actual_lon = float(point_data['lon'].values.item())
        else:
            point_data = ds.interp(lat=target_lat, lon=target_lon, method=method)
            actual_lat = target_lat
            actual_lon = target_lon
            
        precip_value = point_data['precipitation'].values
        time_val = point_data['time'].values
        
        t_start, t_end, col_name, scale = _time_bounds(time_val, freq, current_dt)
        val = float(precip_value.item() if hasattr(precip_value, 'item') else precip_value) * scale
        return {
            "Requested_Lat": target_lat,
            "Requested_Lon": target_lon,
            "Actual_Lat": actual_lat,
            "Actual_Lon": actual_lon,
            "Interpolation": method,
            "Start_Time": t_start,
            "End_Time": t_end,
            col_name: val
        }
    except Exception as e:
        raise Exception(f"Failed to process NetCDF: {str(e)}")
    finally:
        if 'ds' in locals():
            ds.close()


def extract_area_average(nc_path, bbox, freq="hhr", current_dt=None, geometry=None, region_name=None, region_type="area"):
    if freq not in {"hhr", "daily", "monthly"}:
        raise ValueError("freq must be 'hhr', 'daily', or 'monthly'.")
    if freq == "monthly" and current_dt is None:
        raise ValueError("current_dt is required when freq='monthly'.")

    try:
        ds = xr.open_dataset(nc_path)
        da = ds["precipitation"]
        if "time" in da.dims:
            da = da.isel(time=0)
        if "lat" in da.dims and "lon" in da.dims:
            da = da.transpose("lat", "lon")

        lats = ds["lat"].values
        lons = ds["lon"].values
        values = np.asarray(da.values, dtype=float)
        while values.ndim > 2:
            values = values[0]
        if values.shape != (len(lats), len(lons)):
            if values.T.shape == (len(lats), len(lons)):
                values = values.T
            else:
                raise ValueError(
                    f"Unexpected precipitation grid shape {values.shape}; expected {(len(lats), len(lons))}."
                )

        mask = np.isfinite(values)
        if geometry:
            geom_mask = _geometry_mask(lats, lons, geometry)
            if geom_mask.any():
                mask &= geom_mask

        if not mask.any():
            raise ValueError("No IMERG grid cells found inside the selected region.")

        mean_rate = float(np.nanmean(np.where(mask, values, np.nan)))
        t_start, t_end, col_name, scale = _time_bounds(ds["time"].values, freq, current_dt)
        min_lat, min_lon, max_lat, max_lon = bbox

        return {
            "Region_Type": region_type,
            "Region_Name": region_name or region_type,
            "Min_Lat": min_lat,
            "Min_Lon": min_lon,
            "Max_Lat": max_lat,
            "Max_Lon": max_lon,
            "Grid_Cells_Averaged": int(mask.sum()),
            "Start_Time": t_start,
            "End_Time": t_end,
            col_name: mean_rate * scale,
        }
    except Exception as e:
        raise Exception(f"Failed to process area NetCDF: {str(e)}")
    finally:
        if 'ds' in locals():
            ds.close()
