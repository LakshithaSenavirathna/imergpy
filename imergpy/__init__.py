# imergpy package
from .core import get_precipitation
from .plotter import plot_from_excel
from .analyzer import add_accumulation, resample_data, calculate_statistics

__all__ = [
    "get_precipitation", 
    "plot_from_excel", 
    "add_accumulation",
    "resample_data",
    "calculate_statistics"
]
