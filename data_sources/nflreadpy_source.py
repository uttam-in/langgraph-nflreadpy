"""
nflreadpy data source implementation.

This module provides access to current season NFL statistics using the nflreadpy package,
with caching and retry logic for reliable data retrieval.
"""

import logging
import time
from datetime import datetime, timedelta
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


class NFLReadPyDataSource(DataSource):
    """
    Data source implementation using nflreadpy for current season data.
    
    Provides access to up-to-date NFL statistics with daily caching
    and automatic retry logic for failed requests.
    """
    
    def __init__(self, cache_ttl_hours: int = 24):
        """
        Initialize the nflreadpy data source.
        
        Args:
            cache_ttl_hours: Time-to-live for cached data in hours (default: 24)
        """
        super().__init__()
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self._cache: Dict[str, Dict] = {}
        self._nflreadpy_available = False
        
        # Try to import nflreadpy
        try:
            import nflreadpy as nfl
            self.nfl = nfl
            self._nflreadpy_available = True
            logger.info("nflreadpy module loaded successfully")
        except ImportError:
            logger.warning(
                "nflreadpy not installed. Install with: pip install nflreadpy"
            )
            self.nfl = None
    
    def _get_cache_key(
        self,
        player_name: str,
        season: Optional[int],
        week: Optional[int]
    ) -> str:
        """Generate cache key for player stats request."""
        return f"{player_name}_{season}_{week}"
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cached data is still valid based on TTL."""
        if 'timestamp' not in cache_entry:
            return False
        
        cache_time = cache_entry['timestamp']
        return datetime.now() - cache_time < self.cache_ttl
    
    def _fetch_with_retry(
        self,
        fetch_func,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Execute fetch function with retry logic.
        
        Args:
            fetch_func: Function to execute
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            Result from fetch_func
            
        Raises:
            Exception: If all retries fail
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return fetch_func()
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed: {e}"
                )
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
        
        raise Exception(
            f"Failed after {max_retries} attempts. Last error: {last_error}"
        )
    
    def get_player_stats(
        self,
        player_name: str,
        season: Optional[int] = None,
        week: Optional[int] = None,
        stats: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Retrieve player statistics from nflreadpy.
        
        Args:
            player_name: Name of the player
            season: NFL season year (defaults to current season)
            week: Specific week number
            stats: List of specific statistics to retrieve
            
        Returns:
            DataFrame containing the requested player statistics
            
        Raises:
            ValueError: If player not found
            ConnectionError: If nflreadpy is unavailable
            Exception: For data retrieval errors
        """
        if not self._nflreadpy_available or self.nfl is None:
            raise ConnectionError(
                "nflreadpy is not available. Please install it with: pip install nflreadpy"
            )
        
        try:
            # Normalize player name
            normalized_name = self.normalize_player_name(player_name)
            
            # Use current season if not specified
            if season is None:
                season = datetime.now().year
            
            # Check global cache manager first
            cache = _get_cache()
            cached_df = cache.get_nflreadpy_data(normalized_name, season, week)
            
            if cached_df is not None:
                logger.info(f"Returning cached nflreadpy data for {normalized_name}")
                
                # Filter by requested stats if specified
                if stats is not None and not cached_df.empty:
                    key_columns = ['player_name', 'team', 'position', 'season', 'week']
                    available_key_cols = [col for col in key_columns if col in cached_df.columns]
                    available_stats = [col for col in stats if col in cached_df.columns]
                    columns_to_select = list(set(available_key_cols + available_stats))
                    return cached_df[columns_to_select]
                
                return cached_df
            
            # Fetch data with retry logic
            def fetch_data():
                # Load player stats for the season
                # nflreadpy uses 'seasons' parameter (plural)
                try:
                    # Try to load weekly stats
                    df = self.nfl.load_player_stats(seasons=season)
                    # Convert from polars to pandas if needed
                    if hasattr(df, 'to_pandas'):
                        df = df.to_pandas()
                except AttributeError:
                    # Fallback to alternative method if available
                    try:
                        df = self.nfl.get_player_stats(year=season)
                        if hasattr(df, 'to_pandas'):
                            df = df.to_pandas()
                    except:
                        raise ConnectionError("Unable to fetch data from nflreadpy")
                
                return df
            
            df = self._fetch_with_retry(fetch_data)
            
            # Filter by player name (use player_display_name which has full names)
            if 'player_display_name' in df.columns:
                result = df[
                    df['player_display_name'].str.strip() == normalized_name
                ].copy()
            elif 'player_name' in df.columns:
                result = df[
                    df['player_name'].str.strip() == normalized_name
                ].copy()
            else:
                raise ValueError("Unable to find player name column in nflreadpy data")
            
            if result.empty:
                raise ValueError(
                    f"Player '{player_name}' not found in nflreadpy data for season {season}"
                )
            
            # Filter by week if specified
            if week is not None and 'week' in result.columns:
                result = result[result['week'] == week]
            
            # Cache the result in global cache manager
            cache = _get_cache()
            cache.set_nflreadpy_data(normalized_name, result, season, week)
            
            # Filter by requested stats if specified
            if stats is not None and not result.empty:
                key_columns = ['player_name', 'team', 'position', 'season', 'week']
                available_key_cols = [col for col in key_columns if col in result.columns]
                available_stats = [col for col in stats if col in result.columns]
                columns_to_select = list(set(available_key_cols + available_stats))
                result = result[columns_to_select]
            
            return result
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving player stats from nflreadpy: {e}")
            raise Exception(f"Failed to retrieve player stats: {str(e)}")
    
    def is_available(self) -> bool:
        """
        Check if nflreadpy is available and can fetch data.
        
        Returns:
            True if nflreadpy is available, False otherwise
        """
        if not self._nflreadpy_available or self.nfl is None:
            return False
        
        try:
            # Try a simple operation to verify connectivity
            # This is a lightweight check
            return True
        except Exception as e:
            logger.error(f"nflreadpy availability check failed: {e}")
            return False
    
    def clear_cache(self):
        """Clear all cached data."""
        self._cache.clear()
        # Also clear from global cache manager
        cache = _get_cache()
        cache.clear_nflreadpy_cache()
        logger.info("nflreadpy cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache size and valid entries count
        """
        valid_entries = sum(
            1 for entry in self._cache.values()
            if self._is_cache_valid(entry)
        )
        
        return {
            'total_entries': len(self._cache),
            'valid_entries': valid_entries
        }
