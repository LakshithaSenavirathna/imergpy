import pytest

from imergpy.core import _excel_dataframe, _parse_datetime, _validate_inputs


def test_parse_supported_datetime_formats():
    assert _parse_datetime("2025-01").month == 1
    assert _parse_datetime("2025-01-15").day == 15
    assert _parse_datetime("2025-01-15T12:30").hour == 12


@pytest.mark.parametrize(
    "lat, lon, run_type, freq, interp_method",
    [
        (91, 80, "early", "hhr", "nearest"),
        (6, 181, "early", "hhr", "nearest"),
        (6, 80, "bad", "hhr", "nearest"),
        (6, 80, "early", "bad", "nearest"),
        (6, 80, "early", "hhr", "bad"),
        (6, 80, "early", "monthly", "nearest"),
    ],
)
def test_validate_inputs_rejects_invalid_values(lat, lon, run_type, freq, interp_method):
    with pytest.raises(ValueError):
        _validate_inputs(lat, lon, run_type, freq, interp_method)


def test_validate_inputs_accepts_valid_monthly_final():
    _validate_inputs(6.9, 79.8, "final", "monthly", "nearest")


def test_excel_dataframe_uses_start_and_end_time_columns_first():
    df = _excel_dataframe(
        [
            {
                "Requested_Lat": 6.9,
                "Requested_Lon": 79.8,
                "Actual_Lat": 6.9,
                "Actual_Lon": 79.8,
                "Interpolation": "nearest",
                "Start_Time": "2025-01-01T00:00:00",
                "End_Time": "2025-01-01T00:30:00",
                "Precipitation_mm_per_half_hour": 2.5,
                "IMERG_Version": "V07C",
                "Run_Type": "early",
            }
        ]
    )

    assert list(df.columns[:2]) == ["Start Time", "End Time"]
    assert "Start_Time" not in df.columns
    assert "End_Time" not in df.columns
