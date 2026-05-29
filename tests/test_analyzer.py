import pandas as pd

from imergpy.analyzer import add_accumulation, calculate_statistics, resample_data


def test_add_accumulation_uses_new_half_hour_schema_without_double_scaling():
    df = pd.DataFrame(
        {
            "Start_Time": ["2025-01-01 00:00", "2025-01-01 00:30"],
            "Precipitation_mm_per_half_hour": [2.0, 3.0],
        }
    )

    result = add_accumulation(df)

    assert result["Absolute_Precip_mm"].tolist() == [2.0, 3.0]
    assert result["Cumulative_Precip_mm"].tolist() == [2.0, 5.0]


def test_resample_data_uses_start_time_column():
    df = pd.DataFrame(
        {
            "Start_Time": ["2025-01-01 00:00", "2025-01-01 00:30"],
            "Precipitation_mm_per_half_hour": [2.0, 3.0],
        }
    )

    result = resample_data(df)

    assert result["Total_Precip_mm"].iloc[0] == 5.0


def test_calculate_statistics_with_new_schema():
    df = pd.DataFrame(
        {
            "Start_Time": ["2025-01-01 00:00", "2025-01-02 00:00"],
            "Precipitation_mm_per_day": [0.5, 30.0],
        }
    )

    stats = calculate_statistics(df)

    assert stats["Total_Rainfall_mm"] == 30.5
    assert stats["Dry_Days_(<1mm)"] == 1
    assert stats["Heavy_Rain_Days_(>25mm)"] == 1
