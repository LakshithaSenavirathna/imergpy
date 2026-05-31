import imergpy


square_bbox = [6.8, 79.7, 7.2, 80.1]  # [min_lat, min_lon, max_lat, max_lon]

excel_path, records = imergpy.get_precipitation(
    lat=7.0,
    lon=79.9,
    start_datetime="2025-11-27 00:00",
    end_datetime="2025-11-27 23:30",
    username="EARTHDATA_USERNAME",
    password="EARTHDATA_PASSWORD",
    run_type="late",
    freq="hhr",
    interp_method="nearest",
    selection_mode="square",
    bbox=square_bbox,
    region_name="square_area",
)

print(excel_path)
print("Rows:", len(records))
