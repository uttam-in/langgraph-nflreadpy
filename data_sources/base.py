"""
Abstract base class for NFL data sources.

This module defines the interface that all data source implementations must follow,
ensuring consistent data retrieval across different sources (Kaggle, nflreadpy, ESPN).
"""

from abc import ABC, abstractmethod
from typing import List, Optional

import pandas as pd


class DataSource(ABC):
    """
    Abstract base class for NFL player statistics data sources.
    
    All data source implementations (Kaggle, nflreadpy, ESPN) must inherit
    from this class and implement the get_player_stats method.
    """
    
    def __init__(self):
        """Initialize the data source."""
        self.name = self.__class__.__name__
    
    @abstractmethod
    def get_player_stats(
        self,
        player_name: str,
        season: Optional[int] = None,
        week: Optional[int] = None,
        stats: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Retrieve player statistics from the data source.
        
        Args:
            player_name: Name of the player to retrieve stats for
            season: NFL season year (e.g., 2023). If None, retrieve all available seasons
            week: Specific week number. If None, retrieve season totals or all weeks
            stats: List of specific statistics to retrieve. If None, retrieve all available stats
            
        Returns:
            DataFrame containing the requested player statistics
            
        Raises:
            ValueError: If player not found or invalid parameters
            ConnectionError: If data source is unavailable
            Exception: For other data retrieval errors
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the data source is currently available.
        
        Returns:
            True if the data source can be accessed, False otherwise
        """
        pass
    
    def normalize_player_name(self, name: str) -> str:
        """
        Normalize player name for consistent lookups.
        
        Uses the validators module for comprehensive normalization if available,
        otherwise falls back to basic normalization.
        
        Args:
            name: Raw player name
            
        Returns:
            Normalized player name (title case, stripped whitespace)
        """
        try:
            from validators import normalize_player_name as normalize_name
            return normalize_name(name, strict=False)
        except ImportError:
            # Fallback to basic normalization if validators module not available
            return name.strip().title()
