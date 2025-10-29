"""
ESPN API data source implementation.

This module provides access to NFL statistics via ESPN's unofficial API,
with HTTP client, JSON parsing, retry logic, and rate limiting.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import urljoin

import pandas as pd
import requests

from data_sources.base import DataSource

logger = logging.getLogger(__name__)


class ESPNDataSource(DataSource):
    """
    Data source implementation using ESPN's unofficial API.
    
    Provides supplementary access to NFL statistics with HTTP client,
    retry logic, and rate limiting to avoid overwhelming the API.
    """
    
    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/"
    
    def __init__(
        self,
        timeout: int = 10,
        max_retries: int = 3,
        rate_limit_delay: float = 0.5
    ):
        """
        Initialize the ESPN data source.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            rate_limit_delay: Delay between requests in seconds
        """
        super().__init__()
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = None
        self._cache: Dict[str, Dict] = {}
        self.cache_ttl = timedelta(hours=1)  # Shorter TTL for ESPN data
        
        # Initialize session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; NFL-Chatbot/1.0)',
            'Accept': 'application/json'
        })
    
    def _rate_limit(self):
        """Implement rate limiting between requests."""
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - elapsed)
        
        self._last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make HTTP request to ESPN API with retry logic.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            ConnectionError: If request fails after all retries
        """
        url = urljoin(self.BASE_URL, endpoint)
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                self._rate_limit()
                
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                return response.json()
                
            except requests.exceptions.Timeout as e:
                last_error = e
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries})")
                
            except requests.exceptions.HTTPError as e:
                last_error = e
                if response.status_code == 429:  # Too Many Requests
                    logger.warning("Rate limit hit, increasing delay")
                    time.sleep(self.rate_limit_delay * (attempt + 2))
                elif response.status_code >= 500:
                    logger.warning(f"Server error {response.status_code} (attempt {attempt + 1})")
                else:
                    # Client error, don't retry
                    raise ConnectionError(f"HTTP {response.status_code}: {e}")
                
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
            
            if attempt < self.max_retries - 1:
                time.sleep(1.0 * (attempt + 1))  # Exponential backoff
        
        raise ConnectionError(
            f"Failed to fetch data from ESPN API after {self.max_retries} attempts: {last_error}"
        )
    
    def _get_cache_key(
        self,
        player_name: str,
        season: Optional[int],
        week: Optional[int]
    ) -> str:
        """Generate cache key for player stats request."""
        return f"espn_{player_name}_{season}_{week}"
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cached data is still valid based on TTL."""
        if 'timestamp' not in cache_entry:
            return False
        
        cache_time = cache_entry['timestamp']
        return datetime.now() - cache_time < self.cache_ttl
    
    def _parse_player_stats(self, player_data: Dict) -> Dict:
        """
        Parse ESPN API player data into standardized format.
        
        Args:
            player_data: Raw player data from ESPN API
            
        Returns:
            Dictionary with standardized stat names
        """
        stats = {}
        
        # Extract basic info
        stats['player_name'] = player_data.get('athlete', {}).get('displayName', '')
        stats['team'] = player_data.get('team', {}).get('abbreviation', '')
        stats['position'] = player_data.get('position', {}).get('abbreviation', '')
        
        # Parse statistics
        stat_categories = player_data.get('statistics', [])
        for category in stat_categories:
            category_name = category.get('name', '').lower()
            stat_values = category.get('stats', {})
            
            # Map ESPN stat names to our standardized names
            stat_mapping = {
                'passingYards': 'passing_yards',
                'passingTouchdowns': 'passing_touchdowns',
                'completions': 'completions',
                'attempts': 'attempts',
                'interceptions': 'interceptions',
                'rushingYards': 'rushing_yards',
                'rushingTouchdowns': 'rushing_touchdowns',
                'rushingAttempts': 'rushing_attempts',
                'receivingYards': 'receiving_yards',
                'receivingTouchdowns': 'receiving_touchdowns',
                'receptions': 'receptions',
                'targets': 'targets'
            }
            
            for espn_name, our_name in stat_mapping.items():
                if espn_name in stat_values:
                    stats[our_name] = stat_values[espn_name]
        
        return stats
    
    def get_player_stats(
        self,
        player_name: str,
        season: Optional[int] = None,
        week: Optional[int] = None,
        stats: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Retrieve player statistics from ESPN API.
        
        Args:
            player_name: Name of the player
            season: NFL season year (defaults to current season)
            week: Specific week number
            stats: List of specific statistics to retrieve
            
        Returns:
            DataFrame containing the requested player statistics
            
        Raises:
            ValueError: If player not found
            ConnectionError: If ESPN API is unavailable
            Exception: For data retrieval errors
        """
        try:
            # Normalize player name
            normalized_name = self.normalize_player_name(player_name)
            
            # Use current season if not specified
            if season is None:
                season = datetime.now().year
            
            # Check cache first
            cache_key = self._get_cache_key(normalized_name, season, week)
            if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
                logger.info(f"Returning cached ESPN data for {cache_key}")
                cached_df = self._cache[cache_key]['data']
                
                # Filter by requested stats if specified
                if stats is not None and not cached_df.empty:
                    key_columns = ['player_name', 'team', 'position']
                    available_key_cols = [col for col in key_columns if col in cached_df.columns]
                    available_stats = [col for col in stats if col in cached_df.columns]
                    columns_to_select = list(set(available_key_cols + available_stats))
                    return cached_df[columns_to_select]
                
                return cached_df
            
            # Search for player
            # Note: ESPN API structure may vary - this is a generic implementation
            # In practice, you'd need to use specific ESPN endpoints
            search_params = {
                'query': player_name,
                'season': season
            }
            
            try:
                # Attempt to fetch player data
                # This is a placeholder - actual ESPN API endpoints may differ
                player_data = self._make_request('athletes', params=search_params)
                
                # Parse the response
                if not player_data or 'athletes' not in player_data:
                    raise ValueError(f"Player '{player_name}' not found in ESPN data")
                
                # Find matching player
                matching_player = None
                for athlete in player_data.get('athletes', []):
                    athlete_name = athlete.get('displayName', '').strip().title()
                    if athlete_name == normalized_name:
                        matching_player = athlete
                        break
                
                if matching_player is None:
                    raise ValueError(f"Player '{player_name}' not found in ESPN data")
                
                # Fetch player statistics
                player_id = matching_player.get('id')
                stats_endpoint = f'athletes/{player_id}/statistics'
                stats_params = {'season': season}
                if week is not None:
                    stats_params['week'] = week
                
                stats_data = self._make_request(stats_endpoint, params=stats_params)
                
                # Parse statistics
                parsed_stats = self._parse_player_stats(stats_data)
                parsed_stats['season'] = season
                if week is not None:
                    parsed_stats['week'] = week
                
                # Convert to DataFrame
                result = pd.DataFrame([parsed_stats])
                
                # Cache the result
                self._cache[cache_key] = {
                    'data': result,
                    'timestamp': datetime.now()
                }
                
                # Filter by requested stats if specified
                if stats is not None and not result.empty:
                    key_columns = ['player_name', 'team', 'position', 'season', 'week']
                    available_key_cols = [col for col in key_columns if col in result.columns]
                    available_stats = [col for col in stats if col in result.columns]
                    columns_to_select = list(set(available_key_cols + available_stats))
                    result = result[columns_to_select]
                
                return result
                
            except ConnectionError:
                raise
            except Exception as e:
                # ESPN API structure might be different, provide helpful error
                logger.error(f"ESPN API parsing error: {e}")
                raise ValueError(
                    f"Unable to retrieve data for '{player_name}' from ESPN API. "
                    "The API structure may have changed or the player may not be available."
                )
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving player stats from ESPN: {e}")
            raise Exception(f"Failed to retrieve player stats: {str(e)}")
    
    def is_available(self) -> bool:
        """
        Check if ESPN API is available.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Make a lightweight request to check availability
            self._make_request('scoreboard')
            return True
        except Exception as e:
            logger.error(f"ESPN API availability check failed: {e}")
            return False
    
    def clear_cache(self):
        """Clear all cached data."""
        self._cache.clear()
        logger.info("ESPN cache cleared")
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
        logger.info("ESPN HTTP session closed")
