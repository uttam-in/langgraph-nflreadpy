"""
Data source implementations for NFL player statistics.

This package contains data source adapters for:
- Kaggle NFL Player Stats dataset (1999-2023)
- nflreadpy for current season data
- ESPN API as supplementary source
"""

from data_sources.base import DataSource
from data_sources.espn_source import ESPNDataSource
from data_sources.kaggle_source import KaggleDataSource
from data_sources.nflreadpy_source import NFLReadPyDataSource

__all__ = [
    'DataSource',
    'KaggleDataSource',
    'NFLReadPyDataSource',
    'ESPNDataSource',
]
