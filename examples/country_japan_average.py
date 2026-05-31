import imergpy


japan_bbox = [24.0, 122.0, 46.0, 146.0]  # [min_lat, min_lon, max_lat, max_lon]
japan_geometry = {
    "type": "Polygon",
    "coordinates": [
        [
            [122.0, 24.0],
            [146.0, 24.0],
            [146.0, 46.0],
            [122.0, 46.0],
            [122.0, 24.0],
        ]
    ],
}

excel_path, records = imergpy.get_precipitation(
    lat=36.2,
    lon=138.2,
    start_datetime="2025-11-27 00:00",
    end_datetime="2025-11-27 23:30",
    username="EARTHDATA_USERNAME",
    password="EARTHDATA_PASSWORD",
    run_type="late",
    freq="hhr",
    interp_method="nearest",
    selection_mode="country",
    bbox=japan_bbox,
    geometry=japan_geometry,
    region_name="Japan",
)

print(excel_path)
print("Rows:", len(records))
