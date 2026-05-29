import pandas as pd


PRECIP_COLUMNS = [
    "Precipitation_mm_per_half_hour",
    "Precipitation_mm_per_day",
    "Precipitation_mm_per_month",
    "Precipitation_mm",
    "Precipitation_mm_hr",
]


def _find_column(df, candidates, label):
    for column in candidates:
        if column in df.columns:
            return column
    raise ValueError(f"Could not find {label}. Expected one of: {', '.join(candidates)}")


def _time_column(df):
    return _find_column(df, ["Start_Time", "Time"], "time column")


def _precip_column(df):
    return _find_column(df, PRECIP_COLUMNS, "precipitation column")

def add_accumulation(df):
    """
    Takes a DataFrame with half-hourly IMERG data and adds:
    1. 'Absolute_Precip_mm': Total mm fallen in that 30 min interval (Rate * 0.5)
    2. 'Cumulative_Precip_mm': Running total of rainfall over the period.
    """
    df = df.copy()
    precip_col = _precip_column(df)

    if precip_col == "Precipitation_mm_hr":
        df['Absolute_Precip_mm'] = df[precip_col] * 0.5
    else:
        df['Absolute_Precip_mm'] = df[precip_col]
    df['Cumulative_Precip_mm'] = df['Absolute_Precip_mm'].cumsum()
    return df

def resample_data(df, freq='D'):
    """
    Resamples the half-hourly data to Daily ('D') or Monthly ('M') totals.
    Args:
        df: Pandas DataFrame from IMERG excel
        freq: 'D' for Daily, 'M' for Monthly
    Returns:
        Resampled DataFrame
    """
    df = df.copy()
    if 'Absolute_Precip_mm' not in df.columns:
        df = add_accumulation(df)
        
    time_col = _time_column(df)
    df[time_col] = pd.to_datetime(df[time_col])
    df.set_index(time_col, inplace=True)
    
    # Resample and sum the absolute precipitation
    resampled = df[['Absolute_Precip_mm']].resample(freq).sum()
    resampled.rename(columns={'Absolute_Precip_mm': 'Total_Precip_mm'}, inplace=True)
    
    return resampled.reset_index()

def calculate_statistics(df):
    """
    Calculates extreme event statistics and thresholds for the given data.
    """
    if 'Absolute_Precip_mm' not in df.columns:
        df = add_accumulation(df)
        
    # Get daily totals for threshold analysis
    daily_df = resample_data(df, freq='D')
    
    stats = {
        "Total_Rainfall_mm": float(df['Absolute_Precip_mm'].sum()),
        "Max_Interval_Precip_mm": float(df['Absolute_Precip_mm'].max()),
        "Max_Daily_Rainfall_mm": float(daily_df['Total_Precip_mm'].max()),
        "Total_Days_Analyzed": int(len(daily_df)),
        "Dry_Days_(<1mm)": int(len(daily_df[daily_df['Total_Precip_mm'] < 1.0])),
        "Wet_Days_(>=1mm)": int(len(daily_df[daily_df['Total_Precip_mm'] >= 1.0])),
        "Heavy_Rain_Days_(>25mm)": int(len(daily_df[daily_df['Total_Precip_mm'] > 25.0])),
        "Extreme_Rain_Days_(>50mm)": int(len(daily_df[daily_df['Total_Precip_mm'] > 50.0]))
    }
    
    return stats
