import os
import tempfile
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from .downloader import DownloadAuthError, DownloadError, EarthdataDownloader
from .processor import extract_area_average, extract_precipitation


VALID_RUN_TYPES = {"early", "late", "final"}
VALID_FREQUENCIES = {"hhr", "daily", "monthly"}
VALID_INTERPOLATION_METHODS = {"nearest", "linear", "cubic"}


def _parse_datetime(value):
    value = str(value).replace('T', ' ')
    formats = {
        7: "%Y-%m",
        10: "%Y-%m-%d",
        16: "%Y-%m-%d %H:%M",
    }
    try:
        return datetime.strptime(value, formats[len(value)])
    except (KeyError, ValueError) as e:
        raise ValueError(f"Invalid date format: {value}. Use YYYY-MM, YYYY-MM-DD, or YYYY-MM-DD HH:MM.") from e


def _validate_inputs(lat, lon, run_type, freq, interp_method):
    if not -90 <= float(lat) <= 90:
        raise ValueError("lat must be between -90 and 90.")
    if not -180 <= float(lon) <= 180:
        raise ValueError("lon must be between -180 and 180.")
    if run_type not in VALID_RUN_TYPES:
        raise ValueError("run_type must be 'early', 'late', or 'final'.")
    if freq not in VALID_FREQUENCIES:
        raise ValueError("freq must be 'hhr', 'daily', or 'monthly'.")
    if interp_method not in VALID_INTERPOLATION_METHODS:
        raise ValueError("interp_method must be 'nearest', 'linear', or 'cubic'.")
    if freq == "monthly" and run_type != "final":
        raise ValueError("monthly frequency only supports run_type='final'.")


def _excel_dataframe(results):
    df = pd.DataFrame(results)
    preferred_order = [
        "Start_Time",
        "End_Time",
        "Requested_Lat",
        "Requested_Lon",
        "Actual_Lat",
        "Actual_Lon",
        "Interpolation",
        "IMERG_Version",
        "Run_Type",
        "Region_Type",
        "Region_Name",
        "Min_Lat",
        "Min_Lon",
        "Max_Lat",
        "Max_Lon",
        "Grid_Cells_Averaged",
    ]
    precip_cols = [c for c in df.columns if c.startswith("Precipitation_")]
    ordered_cols = [c for c in preferred_order + precip_cols if c in df.columns]
    remaining_cols = [c for c in df.columns if c not in ordered_cols]
    df = df[ordered_cols + remaining_cols]
    return df.rename(columns={"Start_Time": "Start Time", "End_Time": "End Time"})

def get_precipitation(lat, lon, start_datetime, end_datetime, username, password,
                      run_type="early", freq="hhr", interp_method="nearest", out_dir=".",
                      progress_callback=None, selection_mode="point", bbox=None,
                      geometry=None, region_name=None):
    """
    Main function to download IMERG data for a time period and save to Excel.
    Now includes dual Start_Time and End_Time columns.
    """
    if selection_mode == "point":
        _validate_inputs(lat, lon, run_type, freq, interp_method)
    else:
        _validate_inputs(lat, lon, run_type, freq, "nearest")
        if not bbox:
            raise ValueError("bbox is required for country and square-area downloads.")
    dt_start = _parse_datetime(start_datetime)
    dt_end = _parse_datetime(end_datetime)

    if dt_end < dt_start:
        raise ValueError("end_datetime must be after start_datetime")

    downloader = EarthdataDownloader(username, password)
    
    time_stamp_start = dt_start.strftime("%Y%m%d_%H%M")
    time_stamp_end = dt_end.strftime("%Y%m%d_%H%M")
    region_label = region_name or f"{lat}_{lon}"
    region_label = "".join(c if c.isalnum() or c in "._-" else "_" for c in str(region_label))
    excel_filename = f"IMERG_{run_type}_{freq}_{selection_mode}_{region_label}_{time_stamp_start}_to_{time_stamp_end}.xlsx"
    os.makedirs(out_dir, exist_ok=True)
    excel_path = os.path.join(out_dir, excel_filename)
    
    # Snap start time appropriately
    if freq == "hhr":
        minute = 0 if dt_start.minute < 30 else 30
        current_dt = dt_start.replace(minute=minute, second=0, microsecond=0)
    elif freq == "daily":
        current_dt = dt_start.replace(hour=0, minute=0, second=0, microsecond=0)
        dt_end = dt_end.replace(hour=23, minute=59)
    elif freq == "monthly":
        current_dt = dt_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total_steps = 0
    temp_dt = current_dt
    while temp_dt <= dt_end:
        total_steps += 1
        if freq == "hhr": temp_dt += timedelta(minutes=30)
        elif freq == "daily": temp_dt += timedelta(days=1)
        elif freq == "monthly": temp_dt += relativedelta(months=1)
    
    results = []
    failures = []
    step_count = 0
    if progress_callback:
        progress_callback(0)

    while current_dt <= dt_end:
        step_count += 1

        fd, temp_nc_path = tempfile.mkstemp(suffix=".nc4")
        os.close(fd)
        
        try:
            _, version_used = downloader.download_granule(lat, lon, current_dt, temp_nc_path, run_type, freq, bbox=bbox)
            if selection_mode == "point":
                data_dict = extract_precipitation(temp_nc_path, lat, lon, method=interp_method, freq=freq, current_dt=current_dt)
            else:
                data_dict = extract_area_average(
                    temp_nc_path,
                    bbox=bbox,
                    freq=freq,
                    current_dt=current_dt,
                    geometry=geometry,
                    region_name=region_name,
                    region_type=selection_mode,
                )
            data_dict["IMERG_Version"] = version_used
            data_dict["Run_Type"] = run_type
            results.append(data_dict)
        except DownloadAuthError:
            raise
        except DownloadError as e:
            failures.append({"datetime": current_dt.isoformat(), "error": str(e)})
            print(f"  -> Warning: {e}")
        finally:
            if os.path.exists(temp_nc_path):
                os.remove(temp_nc_path)
            if progress_callback:
                progress_callback(int((step_count / total_steps) * 100))
        
        if freq == "hhr": current_dt += timedelta(minutes=30)
        elif freq == "daily": current_dt += timedelta(days=1)
        elif freq == "monthly": current_dt += relativedelta(months=1)
    
    if not results:
        details = "; ".join(f"{f['datetime']}: {f['error']}" for f in failures[:3])
        raise RuntimeError(f"No data could be successfully downloaded. {details}")
        
    df = _excel_dataframe(results)
    df.to_excel(excel_path, index=False)
    
    # JSON-friendly results
    serializable_results = []
    for r in results:
        entry = r.copy()
        for k in ["Start_Time", "End_Time"]:
            if hasattr(entry[k], 'isoformat'): entry[k] = entry[k].isoformat()
            else: entry[k] = str(entry[k])
        serializable_results.append(entry)

    return excel_path, serializable_results
