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
print("Rows:", len(records))
