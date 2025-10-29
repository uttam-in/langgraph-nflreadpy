"""
Kaggle dataset data source implementation.

This module provides access to the Kaggle NFL Player Stats dataset (1999-2023)
using Pandas for efficient data loading and querying.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from data_sources.base import DataSource

logger = logging.getLogger(__name__)

# Import cache manager (lazy import to avoid circular dependencies)
_cache_manager = None


def _get_cache():
    """Lazy import of cache manager."""
    global _cache_manager
    if _cache_manager is None:
        from cache_manager import get_cache_manager
        _cache_manager = get_cache_manager()
    return _cache_manager


class KaggleDataSource(DataSource):
    """
    Data source implementation for Kaggle NFL Player Stats dataset.
    
    Loads CSV files into memory and provides indexed access to historical
    player statistics from 1999 to 2023.
    """
    
    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize the Kaggle data source.
        
        Args:
            data_path: Path to the Kaggle dataset directory or CSV file.
                      If None, looks for data in ./data/kaggle/
        """
        super().__init__()
        self.data_path = data_path or os.path.join("data", "kaggle")
        self._data_cache: Optional[pd.DataFrame] = None
        self._is_loaded = False
        
    def _load_data(self) -> pd.DataFrame:
        """
        Load Kaggle dataset into memory.
        
        Returns:
            DataFrame containing all player statistics
            
        Raises:
            FileNotFoundError: If dataset file not found
            Exception: For other loading errors
        """
        # Check instance cache first
        if self._data_cache is not None:
            return self._data_cache
        
        # Check global cache manager
        cache = _get_cache()
        cached_data = cache.get_kaggle_data()
        if cached_data is not None:
            logger.info("Using Kaggle dataset from global cache")
            self._data_cache = cached_data
            self._is_loaded = True
            return cached_data
        
        try:
            # Check if data_path is a file or directory
            path = Path(self.data_path)
            
            if path.is_file():
                csv_file = path
            elif path.is_dir():
                # Look for common CSV filenames
                possible_files = [
                    "nfl_player_stats.csv",
                    "player_stats.csv",
                    "stats.csv"
                ]
                csv_file = None
                for filename in possible_files:
                    candidate = path / filename
                    if candidate.exists():
                        csv_file = candidate
                        break
                
                if csv_file is None:
                    # Try to find any CSV file in the directory
                    csv_files = list(path.glob("*.csv"))
                    if csv_files:
                        csv_file = csv_files[0]
                    else:
                        raise FileNotFoundError(
                            f"No CSV files found in {self.data_path}"
                        )
            else:
                raise FileNotFoundError(
                    f"Data path does not exist: {self.data_path}"
                )
            
            logger.info(f"Loading Kaggle dataset from {csv_file}")
            df = pd.read_csv(csv_file)
            
            # Use validators to normalize the DataFrame
            from validators import validate_and_normalize_player_stats
            df = validate_and_normalize_player_stats(df, strict=False)
            
            # Create indexed version for faster lookups
            if 'player_name' in df.columns:
                df['player_name_normalized'] = df['player_name']
            
            self._data_cache = df
            self._is_loaded = True
            logger.info(f"Loaded {len(df)} records from Kaggle dataset")
            
            # Store in global cache manager
            cache = _get_cache()
            cache.set_kaggle_data(df)
            
            return df
            
        except FileNotFoundError as e:
            logger.error(f"Kaggle dataset not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading Kaggle dataset: {e}")
            raise Exception(f"Failed to load Kaggle dataset: {str(e)}")
    
    def get_player_stats(
        self,
        player_name: str,
        season: Optional[int] = None,
        week: Optional[int] = None,
        stats: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Retrieve player statistics from Kaggle dataset.
        
        Args:
            player_name: Name of the player
            season: NFL season year (1999-2023)
            week: Specific week number
            stats: List of specific statistics to retrieve
            
        Returns:
            DataFrame containing the requested player statistics
            
        Raises:
            ValueError: If player not found or season out of range
            Exception: For data retrieval errors
        """
        try:
            df = self._load_data()
            
            # Normalize player name for lookup
            normalized_name = self.normalize_player_name(player_name)
            
            # Filter by player name
            if 'player_name_normalized' in df.columns:
                result = df[df['player_name_normalized'] == normalized_name].copy()
            elif 'player_name' in df.columns:
                result = df[df['player_name'].str.strip().str.title() == normalized_name].copy()
            else:
                raise ValueError("Dataset does not contain player_name column")
            
            if result.empty:
                raise ValueError(f"Player '{player_name}' not found in Kaggle dataset")
            
            # Filter by season if specified
            if season is not None:
                # Use validators to validate season
                from validators import validate_season
                try:
                    validated_season = validate_season(season, strict=True)
                except Exception as e:
                    raise ValueError(
                        f"Season {season} out of range for Kaggle dataset (1999-2023)"
                    )
                
                if 'season' in result.columns:
                    result = result[result['season'] == validated_season]
                elif 'year' in result.columns:
                    result = result[result['year'] == validated_season]
            
            # Filter by week if specified
            if week is not None:
                # Use validators to validate week
                from validators import validate_week
                try:
                    validated_week = validate_week(week, strict=True)
                except Exception as e:
                    raise ValueError(f"Invalid week: {week}")
                
                if 'week' in result.columns:
                    result = result[result['week'] == validated_week]
            
            # Select specific stats if requested
            if stats is not None:
                # Ensure player_name and other key columns are included
                key_columns = ['player_name', 'team', 'position', 'season', 'week']
                available_key_cols = [col for col in key_columns if col in result.columns]
                
                # Add requested stats that exist in the dataframe
                available_stats = [col for col in stats if col in result.columns]
                
                columns_to_select = list(set(available_key_cols + available_stats))
                result = result[columns_to_select]
            
            if result.empty:
                logger.warning(
                    f"No data found for {player_name} "
                    f"(season={season}, week={week})"
                )
            
            return result
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving player stats: {e}")
            raise Exception(f"Failed to retrieve player stats: {str(e)}")
    
    def is_available(self) -> bool:
        """
        Check if the Kaggle dataset is available.
        
        Returns:
            True if dataset can be loaded, False otherwise
        """
        try:
            if self._is_loaded:
                return True
            
            path = Path(self.data_path)
            if path.is_file():
                return path.exists()
            elif path.is_dir():
                # Check if directory contains any CSV files
                return len(list(path.glob("*.csv"))) > 0
            return False
            
        except Exception as e:
            logger.error(f"Error checking Kaggle data availability: {e}")
            return False
    
    def get_available_seasons(self) -> List[int]:
        """
        Get list of available seasons in the dataset.
        
        Returns:
            List of season years
        """
        try:
            df = self._load_data()
            if 'season' in df.columns:
                return sorted(df['season'].unique().tolist())
            elif 'year' in df.columns:
                return sorted(df['year'].unique().tolist())
            return []
        except Exception as e:
            logger.error(f"Error getting available seasons: {e}")
            return []
    
    def search_players(self, partial_name: str) -> List[str]:
        """
        Search for players by partial name match.
        
        Args:
            partial_name: Partial player name to search for
            
        Returns:
            List of matching player names
        """
        try:
            df = self._load_data()
            if 'player_name' in df.columns:
                matches = df[
                    df['player_name'].str.contains(partial_name, case=False, na=False)
                ]['player_name'].unique().tolist()
                return sorted(matches)
            return []
        except Exception as e:
            logger.error(f"Error searching players: {e}")
            return []
