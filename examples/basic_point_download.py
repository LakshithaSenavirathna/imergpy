import os

import imergpy


excel_path, records = imergpy.get_precipitation(
    lat=6.9271,
    lon=79.8612,
    start_datetime="2024-05-20 14:30",
    end_datetime="2024-05-20 15:00",
    username=os.environ["EARTHDATA_USERNAME"],
    password=os.environ["EARTHDATA_PASSWORD"],
    run_type="final",
    freq="hhr",
)

print(excel_path)
print(records[:1])
