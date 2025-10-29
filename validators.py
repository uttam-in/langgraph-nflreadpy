"""
Data validation and normalization for NFL Player Performance Chatbot.

This module provides comprehensive validation and normalization functions for:
- Player names (handling spelling variations)
- Statistical data types
- Time periods (seasons, weeks)
- Cross-source data consistency

Requirements addressed:
- 6.4: Handle common variations in player name spelling and team references
- 4.3: Normalize data formats across different sources
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from difflib import SequenceMatcher

import pandas as pd


# Valid NFL seasons range (based on available data)
MIN_SEASON = 1999
MAX_SEASON = datetime.now().year if datetime.now().month >= 9 else datetime.now().year - 1

# Valid week numbers
MIN_WEEK = 1
MAX_WEEK = 18  # Including playoffs

# Common player name variations and corrections
PLAYER_NAME_CORRECTIONS = {
    # Common misspellings
    "patrick mahomes": "Patrick Mahomes",
    "pat mahomes": "Patrick Mahomes",
    "mahommes": "Patrick Mahomes",
    "josh allen": "Josh Allen",
    "joe burrow": "Joe Burrow",
    "joey burrow": "Joe Burrow",
    "lamar jackson": "Lamar Jackson",
    "justin jefferson": "Justin Jefferson",
    "tyreek hill": "Tyreek Hill",
    "tyreke hill": "Tyreek Hill",
    "travis kelce": "Travis Kelce",
    "travis kelcie": "Travis Kelce",
    "ceedee lamb": "CeeDee Lamb",
    "cd lamb": "CeeDee Lamb",
    "aj brown": "A.J. Brown",
    "jalen hurts": "Jalen Hurts",
    "christian mccaffrey": "Christian McCaffrey",
    "cmc": "Christian McCaffrey",
    "stefon diggs": "Stefon Diggs",
    "stephen diggs": "Stefon Diggs",
    # Add more as needed
}

# Standardized statistical field names
VALID_STAT_FIELDS = {
    # Passing stats
    "completions", "attempts", "passing_yards", "passing_touchdowns",
    "interceptions", "sacks", "sack_yards", "completion_rate",
    "yards_per_attempt", "passer_rating", "qbr",
    
    # Rushing stats
    "rushing_attempts", "rushing_yards", "rushing_touchdowns",
    "yards_per_carry", "longest_rush", "rushing_first_downs",
    
    # Receiving stats
    "targets", "receptions", "receiving_yards", "receiving_touchdowns",
    "yards_per_reception", "longest_reception", "drops",
    
    # Advanced metrics
    "epa", "success_rate", "cpoe", "air_yards", "yac",
    "fantasy_points", "games_played",
    
    # Team/position info
    "team", "position", "season", "week"
}

# Data type specifications for each stat field
STAT_DATA_TYPES = {
    # Integer fields
    "completions": int,
    "attempts": int,
    "passing_yards": int,
    "passing_touchdowns": int,
    "interceptions": int,
    "sacks": int,
    "sack_yards": int,
    "rushing_attempts": int,
    "rushing_yards": int,
    "rushing_touchdowns": int,
    "targets": int,
    "receptions": int,
    "receiving_yards": int,
    "receiving_touchdowns": int,
    "games_played": int,
    "season": int,
    "week": int,
    
    # Float fields
    "completion_rate": float,
    "yards_per_attempt": float,
    "yards_per_carry": float,
    "yards_per_reception": float,
    "passer_rating": float,
    "qbr": float,
    "epa": float,
    "success_rate": float,
    "cpoe": float,
    "air_yards": float,
    "yac": float,
    "fantasy_points": float,
    
    # String fields
    "player_name": str,
    "team": str,
    "position": str,
}


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def normalize_player_name(name: str, strict: bool = False) -> str:
    """
    Normalize player name to handle spelling variations.
    
    Handles:
    - Case normalization (Title Case)
    - Whitespace trimming
    - Common misspellings
    - Punctuation variations (e.g., "A.J." vs "AJ")
    
    Args:
        name: Raw player name
        strict: If True, raise error for invalid names
        
    Returns:
        Normalized player name
        
    Raises:
        ValidationError: If strict=True and name is invalid
        
    Requirements: 6.4
    """
    if not name or not isinstance(name, str):
        if strict:
            raise ValidationError(f"Invalid player name: {name}")
        return ""
    
    # Strip whitespace and convert to lowercase for lookup
    name_clean = name.strip().lower()
    
    # Check for known corrections
    if name_clean in PLAYER_NAME_CORRECTIONS:
        return PLAYER_NAME_CORRECTIONS[name_clean]
    
    # Apply standard normalization
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', name_clean)
    
    # Handle common punctuation patterns
    # Convert "AJ" to "A.J.", "DJ" to "D.J.", etc.
    normalized = re.sub(r'\b([a-z])([a-z])\b', r'\1.\2.', normalized)
    
    # Convert to Title Case
    normalized = normalized.title()
    
    # Handle special cases like "McCaffrey", "O'Brien"
    normalized = re.sub(r"Mc([a-z])", lambda m: f"Mc{m.group(1).upper()}", normalized)
    normalized = re.sub(r"O'([a-z])", lambda m: f"O'{m.group(1).upper()}", normalized)
    
    return normalized


def find_similar_player_names(
    name: str,
    available_names: List[str],
    threshold: float = 0.8
) -> List[Tuple[str, float]]:
    """
    Find similar player names using fuzzy matching.
    
    Useful for suggesting corrections when exact match fails.
    
    Args:
        name: Player name to match
        available_names: List of valid player names
        threshold: Similarity threshold (0.0 to 1.0)
        
    Returns:
        List of (name, similarity_score) tuples, sorted by score
        
    Requirements: 6.4
    """
    normalized_input = normalize_player_name(name)
    matches = []
    
    for available_name in available_names:
        similarity = SequenceMatcher(
            None,
            normalized_input.lower(),
            available_name.lower()
        ).ratio()
        
        if similarity >= threshold:
            matches.append((available_name, similarity))
    
    # Sort by similarity score (descending)
    matches.sort(key=lambda x: x[1], reverse=True)
    
    return matches


def validate_season(season: Union[int, str], strict: bool = True) -> int:
    """
    Validate and normalize NFL season year.
    
    Args:
        season: Season year (e.g., 2023, "2023")
        strict: If True, raise error for invalid seasons
        
    Returns:
        Validated season as integer
        
    Raises:
        ValidationError: If season is invalid and strict=True
        
    Requirements: 6.4
    """
    try:
        season_int = int(season)
    except (ValueError, TypeError):
        if strict:
            raise ValidationError(f"Invalid season format: {season}")
        return MAX_SEASON
    
    if season_int < MIN_SEASON or season_int > MAX_SEASON:
        if strict:
            raise ValidationError(
                f"Season {season_int} out of valid range ({MIN_SEASON}-{MAX_SEASON})"
            )
        # Clamp to valid range
        season_int = max(MIN_SEASON, min(MAX_SEASON, season_int))
    
    return season_int


def validate_week(week: Union[int, str], strict: bool = True) -> int:
    """
    Validate and normalize NFL week number.
    
    Args:
        week: Week number (1-18)
        strict: If True, raise error for invalid weeks
        
    Returns:
        Validated week as integer
        
    Raises:
        ValidationError: If week is invalid and strict=True
        
    Requirements: 6.4
    """
    try:
        week_int = int(week)
    except (ValueError, TypeError):
        if strict:
            raise ValidationError(f"Invalid week format: {week}")
        return 1
    
    if week_int < MIN_WEEK or week_int > MAX_WEEK:
        if strict:
            raise ValidationError(
                f"Week {week_int} out of valid range ({MIN_WEEK}-{MAX_WEEK})"
            )
        # Clamp to valid range
        week_int = max(MIN_WEEK, min(MAX_WEEK, week_int))
    
    return week_int


def validate_time_period(
    season: Optional[Union[int, str]] = None,
    start_week: Optional[Union[int, str]] = None,
    end_week: Optional[Union[int, str]] = None,
    strict: bool = True
) -> Dict[str, Optional[int]]:
    """
    Validate complete time period specification.
    
    Args:
        season: Season year
        start_week: Starting week number
        end_week: Ending week number
        strict: If True, raise error for invalid values
        
    Returns:
        Dictionary with validated season, start_week, end_week
        
    Raises:
        ValidationError: If time period is invalid and strict=True
        
    Requirements: 6.4
    """
    result = {
        "season": None,
        "start_week": None,
        "end_week": None
    }
    
    # Validate season
    if season is not None:
        result["season"] = validate_season(season, strict)
    
    # Validate weeks
    if start_week is not None:
        result["start_week"] = validate_week(start_week, strict)
    
    if end_week is not None:
        result["end_week"] = validate_week(end_week, strict)
    
    # Validate week range
    if (result["start_week"] is not None and 
        result["end_week"] is not None and 
        result["start_week"] > result["end_week"]):
        if strict:
            raise ValidationError(
                f"Invalid week range: {result['start_week']} to {result['end_week']}"
            )
        # Swap them
        result["start_week"], result["end_week"] = result["end_week"], result["start_week"]
    
    return result


def validate_stat_value(
    stat_name: str,
    value: Any,
    strict: bool = False
) -> Optional[Union[int, float, str]]:
    """
    Validate and convert statistical value to correct data type.
    
    Args:
        stat_name: Name of the statistical field
        value: Raw value to validate
        strict: If True, raise error for invalid values
        
    Returns:
        Validated and type-converted value, or None if invalid
        
    Raises:
        ValidationError: If value is invalid and strict=True
        
    Requirements: 4.3
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    
    # Get expected data type
    expected_type = STAT_DATA_TYPES.get(stat_name)
    
    if expected_type is None:
        # Unknown stat field
        if strict:
            raise ValidationError(f"Unknown statistical field: {stat_name}")
        return value
    
    # Try to convert to expected type
    try:
        if expected_type == int:
            return int(float(value))  # Handle "123.0" strings
        elif expected_type == float:
            return float(value)
        elif expected_type == str:
            return str(value).strip()
        else:
            return value
    except (ValueError, TypeError) as e:
        if strict:
            raise ValidationError(
                f"Invalid value for {stat_name}: {value} (expected {expected_type.__name__})"
            )
        return None


def normalize_stat_names(stats: List[str]) -> List[str]:
    """
    Normalize statistical field names to standardized format.
    
    Args:
        stats: List of stat names in various formats
        
    Returns:
        List of normalized stat names
        
    Requirements: 4.3
    """
    normalized = []
    
    for stat in stats:
        # Convert to lowercase and replace spaces with underscores
        stat_clean = stat.lower().strip().replace(' ', '_').replace('-', '_')
        
        # Remove any non-alphanumeric characters except underscores
        stat_clean = re.sub(r'[^a-z0-9_]', '', stat_clean)
        
        # Check if it's a valid stat field
        if stat_clean in VALID_STAT_FIELDS:
            normalized.append(stat_clean)
        else:
            # Try to find close match
            for valid_stat in VALID_STAT_FIELDS:
                if stat_clean in valid_stat or valid_stat in stat_clean:
                    normalized.append(valid_stat)
                    break
            else:
                # Keep original if no match found
                normalized.append(stat_clean)
    
    return normalized


def normalize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize DataFrame column names to standardized format.
    
    Handles different naming conventions from various data sources.
    
    Args:
        df: DataFrame with potentially inconsistent column names
        
    Returns:
        DataFrame with normalized column names
        
    Requirements: 4.3
    """
    if df.empty:
        return df
    
    # Create column mapping
    column_mapping = {}
    
    for col in df.columns:
        # Normalize column name
        normalized = col.lower().strip().replace(' ', '_').replace('-', '_')
        normalized = re.sub(r'[^a-z0-9_]', '', normalized)
        
        # Map common variations
        if normalized in ['pass_yds', 'passyds', 'pass_yards']:
            normalized = 'passing_yards'
        elif normalized in ['pass_td', 'passtd', 'pass_touchdowns']:
            normalized = 'passing_touchdowns'
        elif normalized in ['rush_yds', 'rushyds', 'rush_yards']:
            normalized = 'rushing_yards'
        elif normalized in ['rush_td', 'rushtd', 'rush_touchdowns']:
            normalized = 'rushing_touchdowns'
        elif normalized in ['rec_yds', 'recyds', 'rec_yards']:
            normalized = 'receiving_yards'
        elif normalized in ['rec_td', 'rectd', 'rec_touchdowns']:
            normalized = 'receiving_touchdowns'
        elif normalized in ['comp', 'comps']:
            normalized = 'completions'
        elif normalized in ['att', 'atts']:
            normalized = 'attempts'
        elif normalized in ['int', 'ints']:
            normalized = 'interceptions'
        elif normalized in ['rec', 'recs']:
            normalized = 'receptions'
        elif normalized in ['tgt', 'tgts']:
            normalized = 'targets'
        elif normalized in ['player', 'name', 'playername']:
            normalized = 'player_name'
        
        column_mapping[col] = normalized
    
    # Rename columns
    df_normalized = df.rename(columns=column_mapping)
    
    return df_normalized


def validate_dataframe_schema(
    df: pd.DataFrame,
    required_columns: Optional[List[str]] = None,
    strict: bool = False
) -> Tuple[bool, List[str]]:
    """
    Validate DataFrame schema and data types.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        strict: If True, raise error for missing columns
        
    Returns:
        Tuple of (is_valid, list_of_issues)
        
    Raises:
        ValidationError: If schema is invalid and strict=True
        
    Requirements: 4.3
    """
    issues = []
    
    if df.empty:
        issues.append("DataFrame is empty")
        if strict:
            raise ValidationError("DataFrame is empty")
        return False, issues
    
    # Check required columns
    if required_columns:
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            issues.append(f"Missing required columns: {missing_columns}")
            if strict:
                raise ValidationError(f"Missing required columns: {missing_columns}")
    
    # Validate data types for known columns
    for col in df.columns:
        if col in STAT_DATA_TYPES:
            expected_type = STAT_DATA_TYPES[col]
            
            # Check if column can be converted to expected type
            try:
                if expected_type == int:
                    pd.to_numeric(df[col], errors='coerce')
                elif expected_type == float:
                    pd.to_numeric(df[col], errors='coerce')
                # String columns are generally fine
            except Exception as e:
                issues.append(f"Column {col} has invalid data type: {e}")
    
    is_valid = len(issues) == 0
    return is_valid, issues


def normalize_dataframe_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize values in DataFrame for cross-source consistency.
    
    Handles:
    - Data type conversions
    - Missing value standardization
    - Player name normalization
    - Statistical value validation
    
    Args:
        df: DataFrame with potentially inconsistent values
        
    Returns:
        DataFrame with normalized values
        
    Requirements: 4.3
    """
    if df.empty:
        return df
    
    df_normalized = df.copy()
    
    # Normalize player names if present
    if 'player_name' in df_normalized.columns:
        df_normalized['player_name'] = df_normalized['player_name'].apply(
            lambda x: normalize_player_name(x) if pd.notna(x) else None
        )
    
    # Normalize each column based on its data type
    for col in df_normalized.columns:
        if col in STAT_DATA_TYPES:
            expected_type = STAT_DATA_TYPES[col]
            
            if expected_type in [int, float]:
                # Convert to numeric, coercing errors to NaN
                df_normalized[col] = pd.to_numeric(df_normalized[col], errors='coerce')
                
                # Convert to int if specified (but keep NaN as NaN)
                if expected_type == int:
                    # Only convert non-null values
                    mask = df_normalized[col].notna()
                    df_normalized.loc[mask, col] = df_normalized.loc[mask, col].astype(int)
            
            elif expected_type == str:
                # Convert to string, handling None/NaN
                df_normalized[col] = df_normalized[col].apply(
                    lambda x: str(x).strip() if pd.notna(x) else None
                )
    
    return df_normalized


def validate_and_normalize_player_stats(
    df: pd.DataFrame,
    strict: bool = False
) -> pd.DataFrame:
    """
    Complete validation and normalization pipeline for player statistics DataFrame.
    
    Combines all normalization steps:
    1. Normalize column names
    2. Validate schema
    3. Normalize values
    
    Args:
        df: Raw DataFrame from data source
        strict: If True, raise errors for validation failures
        
    Returns:
        Fully normalized and validated DataFrame
        
    Raises:
        ValidationError: If validation fails and strict=True
        
    Requirements: 4.3, 6.4
    """
    # Step 1: Normalize column names
    df_normalized = normalize_dataframe_columns(df)
    
    # Step 2: Validate schema
    required_cols = ['player_name']  # Minimum requirement
    is_valid, issues = validate_dataframe_schema(df_normalized, required_cols, strict)
    
    if not is_valid and not strict:
        # Log issues but continue
        print(f"DataFrame validation issues: {issues}")
    
    # Step 3: Normalize values
    df_normalized = normalize_dataframe_values(df_normalized)
    
    return df_normalized
