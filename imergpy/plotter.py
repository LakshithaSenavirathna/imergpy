import pandas as pd
import matplotlib.pyplot as plt
import os
from .analyzer import _precip_column, _time_column

def plot_from_excel(excel_path, save_png=True):
    """
    Reads the IMERG data from an Excel file and plots a time series.
    
    Args:
        excel_path (str): Path to the generated Excel file.
        save_png (bool): If True, saves the plot as a PNG image alongside the Excel file.
    """
    try:
        # Read the Excel file
        df = pd.read_excel(excel_path)
        
        time_col = _time_column(df)
        precip_col = _precip_column(df)
        df[time_col] = pd.to_datetime(df[time_col])
        
        df = df.sort_values(time_col)
        ylabel = precip_col.replace("Precipitation_", "").replace("_", " ")
        
        plt.figure(figsize=(10, 6))
        plt.plot(df[time_col], df[precip_col], marker='o', linestyle='-', color='b', label='Precipitation')
        
        lat = df['Requested_Lat'].iloc[0]
        lon = df['Requested_Lon'].iloc[0]
        plt.title(f'IMERG Precipitation\nLat: {lat}, Lon: {lon}')
        plt.xlabel('Time (UTC)')
        plt.ylabel(f'Precipitation ({ylabel})')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save or display
        if save_png:
            png_path = os.path.splitext(excel_path)[0] + '.png'
            plt.savefig(png_path, dpi=300)
            print(f"Plot saved successfully to: {png_path}")
        else:
            plt.show()
            
        # Close plot to free memory
        plt.close()
        
    except Exception as e:
        raise Exception(f"Failed to plot time series: {str(e)}")
