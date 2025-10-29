"""
Retriever Node for NFL Player Performance Chatbot.

This module implements the Retriever Node that fetches player statistics
from appropriate data sources based on the parsed query.

All data retrieved is automatically validated and normalized using the
validators module to ensure consistency across different data sources.

Requirements addressed:
- 4.3: Route queries to appropriate data sources based on time period
- 7.1: Implement fallback logic when primary data source fails
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from data_sources.base import DataSource
from data_sources.kaggle_source import KaggleDataSource
from data_sources.nflreadpy_source import NFLReadPyDataSource
from data_sources.espn_source import ESPNDataSource
from models.models import ChatbotState
from error_handler import (
    handle_data_source_error,
    ChatbotError,
    ErrorType,
    log_error,
    attempt_recovery
)

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


class DataSourceRouter:
    """
    Routes data retrieval requests to appropriate data sources.
    
    Implements priority-based routing with fallback logic:
    - Historical data (1999-2023): Kaggle dataset
    - Current season: nflreadpy (primary), ESPN (fallback)
    """
    
    def __init__(
        self,
        kaggle_path: Optional[str] = None,
        nflreadpy_cache_ttl: int = 24,
        espn_timeout: int = 10,
        current_season: Optional[int] = None
    ):
        """
        Initialize the data source router.
        
        Args:
            kaggle_path: Path to Kaggle dataset
            nflreadpy_cache_ttl: Cache TTL for nflreadpy in hours
            espn_timeout: Timeout for ESPN API requests in seconds
        """
        self.kaggle_source = KaggleDataSource(data_path=kaggle_path)
        self.nflreadpy_source = NFLReadPyDataSource(cache_ttl_hours=nflreadpy_cache_ttl)
        self.espn_source = ESPNDataSource(timeout=espn_timeout)
        
        # Define routing rules based on season
        inferred_year = datetime.now().year
        if datetime.now().month < 3:
            inferred_year -= 1
        self.current_season = current_season or inferred_year
        self.kaggle_max_season = 2023
    
    def get_primary_source(self, season: Optional[int]) -> DataSource:
        """
        Determine primary data source based on season.
        
        Args:
            season: NFL season year
            
        Returns:
            Primary data source for the season
        """
        if season is None or season >= self.current_season:
            # Current season - use nflreadpy
            return self.nflreadpy_source
        elif season <= self.kaggle_max_season:
            # Historical data - use Kaggle
            return self.kaggle_source
        else:
            # Gap between Kaggle and current - try nflreadpy first
            return self.nflreadpy_source
    
    def get_fallback_sources(self, season: Optional[int]) -> List[DataSource]:
        """
        Get ordered list of fallback data sources.
        
        Args:
            season: NFL season year
            
        Returns:
            List of fallback data sources in priority order
        """
        if season is None or season >= self.current_season:
            # Current season fallbacks
            return [self.espn_source, self.kaggle_source]
        elif season <= self.kaggle_max_season:
            # Historical fallbacks
            return [self.nflreadpy_source, self.espn_source]
        else:
            # Gap year fallbacks
            return [self.espn_source, self.kaggle_source]
    
    def retrieve_with_fallback(
        self,
        player_name: str,
        season: Optional[int] = None,
        week: Optional[int] = None,
        stats: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Retrieve player stats with automatic fallback.
        
        Args:
            player_name: Name of the player
            season: NFL season year
            week: Specific week number
            stats: List of statistics to retrieve
            
        Returns:
            DataFrame with player statistics
            
        Raises:
            ChatbotError: If all data sources fail
            
        Requirements:
            - 7.1: Implements fallback logic when primary data source fails
            - 7.3: Logs errors with sufficient detail
        """
        # Try primary source
        primary_source = self.get_primary_source(season)
        last_error = None
        
        try:
            logger.info(
                f"Attempting to retrieve {player_name} stats from "
                f"{primary_source.name} (season={season}, week={week})"
            )
            result = primary_source.get_player_stats(
                player_name=player_name,
                season=season,
                week=week,
                stats=stats
            )
            
            if not result.empty:
                logger.info(f"Successfully retrieved data from {primary_source.name}")
                return result
            else:
                logger.warning(f"Primary source {primary_source.name} returned no data")
            
        except Exception as e:
            last_error = e
            log_error(
                e,
                context={
                    "source": primary_source.name,
                    "player": player_name,
                    "season": season,
                    "week": week
                },
                level="warning"
            )
        
        # Try fallback sources
        fallback_sources = self.get_fallback_sources(season)
        
        for source in fallback_sources:
            try:
                if not source.is_available():
                    logger.info(f"Skipping unavailable source: {source.name}")
                    continue
                
                logger.info(
                    f"Attempting fallback to {source.name} for {player_name}"
                )
                result = source.get_player_stats(
                    player_name=player_name,
                    season=season,
                    week=week,
                    stats=stats
                )
                
                if not result.empty:
                    logger.info(f"Successfully retrieved data from fallback {source.name}")
                    return result
                else:
                    logger.warning(f"Fallback source {source.name} returned no data")
                
            except Exception as e:
                last_error = e
                log_error(
                    e,
                    context={
                        "source": source.name,
                        "player": player_name,
                        "season": season,
                        "week": week
                    },
                    level="warning"
                )
                continue
        
        # All sources failed - raise appropriate error
        if last_error:
            raise ChatbotError(
                error_type=ErrorType.DATA_RETRIEVAL_FAILED,
                message=f"Unable to retrieve stats for '{player_name}' from any data source",
                details={
                    "player_name": player_name,
                    "season": season,
                    "week": week,
                    "last_error": str(last_error)
                },
                recoverable=True
            )
        else:
            raise ChatbotError(
                error_type=ErrorType.NO_DATA_FOUND,
                message=f"No statistics found for '{player_name}'",
                details={
                    "player_name": player_name,
                    "season": season,
                    "week": week
                },
                recoverable=True
            )


def apply_filters(
    df: pd.DataFrame,
    filters: Dict
) -> pd.DataFrame:
    """
    Apply query filters to DataFrame using Pandas operations.
    
    Args:
        df: DataFrame with player statistics
        filters: Dictionary of filters from parsed query
            
    Returns:
        Filtered DataFrame
    """
    result = df.copy()
    
    # Apply opponent filter
    if filters.get('opponent'):
        opponent = filters['opponent']
        if 'opponent' in result.columns:
            result = result[result['opponent'].str.contains(opponent, case=False, na=False)]
    
    # Apply home/away filter
    if filters.get('home_away'):
        home_away = filters['home_away'].lower()
        if 'home_away' in result.columns:
            result = result[result['home_away'].str.lower() == home_away]
    
    # Apply min value filter
    if filters.get('min_value') is not None:
        min_val = filters['min_value']
        # Apply to numeric columns
        numeric_cols = result.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            if col not in ['season', 'week', 'games_played']:
                result = result[result[col] >= min_val]
    
    # Apply max value filter
    if filters.get('max_value') is not None:
        max_val = filters['max_value']
        # Apply to numeric columns
        numeric_cols = result.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            if col not in ['season', 'week', 'games_played']:
                result = result[result[col] <= max_val]
    
    return result


def normalize_data_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize data formats across different sources.
    
    Ensures consistent column names, data types, and structure
    regardless of which data source provided the data.
    
    Args:
        df: DataFrame from any data source
        
    Returns:
        Normalized DataFrame
    """
    result = df.copy()
    
    # Standardize column names
    column_mapping = {
        'player': 'player_name',
        'year': 'season',
        'tm': 'team',
        'pos': 'position',
        'pass_yds': 'passing_yards',
        'pass_td': 'passing_touchdowns',
        'rush_yds': 'rushing_yards',
        'rush_td': 'rushing_touchdowns',
        'rec_yds': 'receiving_yards',
        'rec_td': 'receiving_touchdowns',
        'rec': 'receptions',
        'tgt': 'targets',
        'att': 'attempts',
        'cmp': 'completions',
        'int': 'interceptions',
    }
    
    result = result.rename(columns=column_mapping)
    
    # Ensure numeric columns are proper type
    numeric_columns = [
        'passing_yards', 'passing_touchdowns', 'completions', 'attempts',
        'interceptions', 'rushing_yards', 'rushing_touchdowns', 'rushing_attempts',
        'receiving_yards', 'receiving_touchdowns', 'receptions', 'targets',
        'season', 'week', 'games_played'
    ]
    
    for col in numeric_columns:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors='coerce')
    
    # Fill NaN values with 0 for statistics
    stat_columns = [col for col in numeric_columns if col not in ['season', 'week']]
    for col in stat_columns:
        if col in result.columns:
            result[col] = result[col].fillna(0)
    
    return result


def aggregate_data(
    df: pd.DataFrame,
    aggregation: Optional[str],
    group_by: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Aggregate data based on query requirements.
    
    Args:
        df: DataFrame with player statistics
        aggregation: Type of aggregation ('sum', 'average', 'max', 'min')
        group_by: Columns to group by before aggregation
        
    Returns:
        Aggregated DataFrame
    """
    if aggregation is None or df.empty:
        return df
    
    # Default grouping by player if not specified
    if group_by is None:
        group_by = ['player_name']
    
    # Ensure group_by columns exist
    group_by = [col for col in group_by if col in df.columns]
    if not group_by:
        return df
    
    # Select numeric columns for aggregation
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    # Exclude grouping columns
    agg_cols = [col for col in numeric_cols if col not in group_by]
    
    if not agg_cols:
        return df
    
    # Perform aggregation
    agg_func_map = {
        'sum': 'sum',
        'average': 'mean',
        'avg': 'mean',
        'mean': 'mean',
        'max': 'max',
        'maximum': 'max',
        'min': 'min',
        'minimum': 'min'
    }
    
    agg_func = agg_func_map.get(aggregation.lower(), 'sum')
    
    try:
        result = df.groupby(group_by)[agg_cols].agg(agg_func).reset_index()
        return result
    except Exception as e:
        logger.warning(f"Aggregation failed: {e}. Returning original data.")
        return df


async def retrieve_data(state: ChatbotState) -> ChatbotState:
    """
    Retrieve player statistics based on parsed query.
    
    This is the main entry point for the Retriever Node in the LangGraph workflow.
    
    Args:
        state: Current chatbot state with parsed_query
        
    Returns:
        Updated state with retrieved_data field populated
        
    Requirements:
        - 4.3: Routes to appropriate data source based on time period
        - 7.1: Implements fallback logic when primary source fails
        - 4.4: Uses caching to improve performance
    """
    try:
        parsed_query = state.get("parsed_query", {})
        
        if not parsed_query:
            state["error"] = "No parsed query available"
            return state
        
        # Skip retrieval if clarification is needed
        if parsed_query.get("needs_clarification"):
            return state
        
        # Extract query parameters
        players = parsed_query.get("players", [])
        statistics = parsed_query.get("statistics", [])
        time_period = parsed_query.get("time_period", {})
        filters = parsed_query.get("filters", {})
        aggregation = parsed_query.get("aggregation")
        
        if not players:
            raise ChatbotError(
                error_type=ErrorType.VALIDATION_ERROR,
                message="No players specified in query",
                details={"parsed_query": parsed_query},
                recoverable=True
            )
        
        # Check query cache first
        cache = _get_cache()
        query_params = {
            "players": players,
            "statistics": statistics,
            "season": time_period.get("season"),
            "week": time_period.get("week"),
            "filters": filters,
            "aggregation": aggregation
        }
        
        cached_result = cache.get_query_result(query_params)
        if cached_result is not None:
            logger.info(f"Returning cached query result for {len(players)} player(s)")
            state["retrieved_data"] = cached_result
            return state
        
        # Initialize router
        router = DataSourceRouter()
        
        # Retrieve data for each player
        all_data = []
        
        for player in players:
            try:
                # Extract time period parameters
                season = time_period.get("season")
                week = time_period.get("week")
                if week is None:
                    specific_weeks = time_period.get("specific_weeks")
                    if specific_weeks:
                        week = specific_weeks[0]
                
                # Retrieve data with fallback
                player_data = router.retrieve_with_fallback(
                    player_name=player,
                    season=season,
                    week=week,
                    stats=statistics if statistics else None
                )
                
                # Normalize data format
                player_data = normalize_data_format(player_data)
                
                # Apply filters
                if filters:
                    player_data = apply_filters(player_data, filters)
                
                all_data.append(player_data)
                
            except Exception as e:
                logger.error(f"Failed to retrieve data for {player}: {e}")
                # Continue with other players
                continue
        
        if not all_data:
            raise ChatbotError(
                error_type=ErrorType.NO_DATA_FOUND,
                message=f"No statistics found for the requested player(s)",
                details={
                    "players": players,
                    "season": time_period.get("season"),
                    "week": time_period.get("week")
                },
                recoverable=True
            )
        
        # Combine all player data
        combined_data = pd.concat(all_data, ignore_index=True)
        
        # Apply aggregation if requested
        if aggregation:
            combined_data = aggregate_data(
                combined_data,
                aggregation,
                group_by=['player_name', 'team', 'position']
            )
        
        # Cache the query result
        cache.set_query_result(query_params, combined_data)
        
        # Store retrieved data in state
        state["retrieved_data"] = combined_data
        
        logger.info(
            f"Successfully retrieved {len(combined_data)} records for "
            f"{len(players)} player(s)"
        )
        
        return state
        
    except ChatbotError:
        # Re-raise ChatbotError to be handled by workflow
        raise
    except Exception as e:
        # Wrap unexpected errors in ChatbotError
        raise ChatbotError(
            error_type=ErrorType.DATA_RETRIEVAL_FAILED,
            message=f"Error retrieving data: {str(e)}",
            details={
                "parsed_query": parsed_query,
                "error": str(e)
            },
            recoverable=True
        )


# Synchronous version for non-async contexts
def retrieve_data_sync(state: ChatbotState) -> ChatbotState:
    """
    Synchronous version of retrieve_data for compatibility.
    
    Args:
        state: Current chatbot state
        
    Returns:
        Updated state with retrieved data
    """
    import asyncio
    
    # Run async function in sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(retrieve_data(state))
