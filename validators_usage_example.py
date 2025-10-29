"""
Example usage of the validators module.

This script demonstrates how to use the validation and normalization
functions in the NFL Player Performance Chatbot.
"""

import pandas as pd
from validators import (
    normalize_player_name,
    find_similar_player_names,
    validate_season,
    validate_week,
    validate_time_period,
    validate_stat_value,
    normalize_stat_names,
    normalize_dataframe_columns,
    validate_and_normalize_player_stats,
    ValidationError
)


def example_player_name_normalization():
    """Example: Normalizing player names."""
    print("=" * 60)
    print("Example 1: Player Name Normalization")
    print("=" * 60)
    
    # Handle various input formats
    names = [
        "patrick mahomes",
        "JOSH ALLEN",
        "  joe burrow  ",
        "cmc",  # Nickname
        "aj brown",
        "tyreke hill"  # Common misspelling
    ]
    
    print("\nNormalizing player names:")
    for name in names:
        normalized = normalize_player_name(name)
        print(f"  '{name}' -> '{normalized}'")


def example_fuzzy_matching():
    """Example: Finding similar player names."""
    print("\n" + "=" * 60)
    print("Example 2: Fuzzy Player Name Matching")
    print("=" * 60)
    
    # Simulate available players in database
    available_players = [
        "Patrick Mahomes",
        "Josh Allen",
        "Joe Burrow",
        "Lamar Jackson",
        "Justin Jefferson",
        "Tyreek Hill"
    ]
    
    # User input with typo
    user_input = "patrick mahommes"
    
    print(f"\nUser searched for: '{user_input}'")
    print("Finding similar names...")
    
    matches = find_similar_player_names(user_input, available_players, threshold=0.7)
    
    if matches:
        print("\nDid you mean:")
        for name, score in matches[:3]:  # Top 3 matches
            print(f"  - {name} (similarity: {score:.2%})")
    else:
        print("No similar names found")


def example_time_period_validation():
    """Example: Validating time periods."""
    print("\n" + "=" * 60)
    print("Example 3: Time Period Validation")
    print("=" * 60)
    
    # Valid time period
    print("\nValidating time period: Season 2023, Weeks 1-17")
    try:
        result = validate_time_period(season=2023, start_week=1, end_week=17)
        print(f"  ✓ Valid: {result}")
    except ValidationError as e:
        print(f"  ✗ Error: {e}")
    
    # Invalid season (too old)
    print("\nValidating time period: Season 1990 (too old)")
    try:
        result = validate_time_period(season=1990, strict=True)
        print(f"  ✓ Valid: {result}")
    except ValidationError as e:
        print(f"  ✗ Error: {e}")
    
    # Invalid week range (swapped)
    print("\nValidating time period: Weeks 10-5 (reversed)")
    result = validate_time_period(start_week=10, end_week=5, strict=False)
    print(f"  ✓ Auto-corrected: {result}")


def example_dataframe_normalization():
    """Example: Normalizing a DataFrame from a data source."""
    print("\n" + "=" * 60)
    print("Example 4: DataFrame Normalization")
    print("=" * 60)
    
    # Simulate data from different sources with inconsistent formats
    print("\nOriginal DataFrame (inconsistent format):")
    df_raw = pd.DataFrame({
        "Player": ["patrick mahomes", "JOSH ALLEN", "joe burrow"],
        "Pass Yds": ["350", "300", "280"],  # String values
        "Pass TD": [3, 2, 2],
        "Comp": [25.0, 22.0, 20.0],  # Float instead of int
        "Att": [35, 30, 28],
        "Season": [2023, 2023, 2023]
    })
    print(df_raw)
    
    # Normalize the DataFrame
    print("\nNormalized DataFrame:")
    df_normalized = validate_and_normalize_player_stats(df_raw, strict=False)
    print(df_normalized)
    
    print("\nChanges made:")
    print("  - Column names standardized (Pass Yds -> passing_yards)")
    print("  - Player names normalized (patrick mahomes -> Patrick Mahomes)")
    print("  - Data types corrected (string '350' -> int 350)")
    print("  - Consistent formatting across all fields")


def example_stat_validation():
    """Example: Validating statistical values."""
    print("\n" + "=" * 60)
    print("Example 5: Statistical Value Validation")
    print("=" * 60)
    
    # Test various stat values
    test_cases = [
        ("passing_yards", 350, "Valid integer stat"),
        ("passing_yards", "350", "String that should be int"),
        ("completion_rate", 65.5, "Valid float stat"),
        ("completion_rate", "65.5", "String that should be float"),
        ("passing_yards", None, "None value"),
        ("unknown_stat", 100, "Unknown stat field"),
    ]
    
    print("\nValidating statistical values:")
    for stat_name, value, description in test_cases:
        try:
            result = validate_stat_value(stat_name, value, strict=False)
            print(f"  ✓ {description}: {stat_name}={value} -> {result} ({type(result).__name__})")
        except ValidationError as e:
            print(f"  ✗ {description}: {e}")


def example_cross_source_consistency():
    """Example: Ensuring consistency across different data sources."""
    print("\n" + "=" * 60)
    print("Example 6: Cross-Source Data Consistency")
    print("=" * 60)
    
    # Simulate data from different sources with different naming conventions
    print("\nData from Source 1 (Kaggle):")
    df_kaggle = pd.DataFrame({
        "player": ["Patrick Mahomes"],
        "pass_yds": [350],
        "pass_td": [3],
        "season": [2023]
    })
    print(df_kaggle)
    
    print("\nData from Source 2 (ESPN):")
    df_espn = pd.DataFrame({
        "Player Name": ["Patrick Mahomes"],
        "Passing Yards": [350],
        "Passing Touchdowns": [3],
        "Year": [2023]
    })
    print(df_espn)
    
    # Normalize both
    print("\nAfter normalization:")
    df_kaggle_norm = validate_and_normalize_player_stats(df_kaggle, strict=False)
    df_espn_norm = validate_and_normalize_player_stats(df_espn, strict=False)
    
    print("\nSource 1 (normalized):")
    print(df_kaggle_norm)
    print("\nSource 2 (normalized):")
    print(df_espn_norm)
    
    print("\n✓ Both sources now have consistent column names and formats!")


def example_error_handling():
    """Example: Handling validation errors."""
    print("\n" + "=" * 60)
    print("Example 7: Error Handling")
    print("=" * 60)
    
    print("\nStrict mode (raises errors):")
    try:
        validate_season(1990, strict=True)
    except ValidationError as e:
        print(f"  ✗ ValidationError: {e}")
    
    print("\nNon-strict mode (auto-corrects):")
    result = validate_season(1990, strict=False)
    print(f"  ✓ Auto-corrected to: {result}")
    
    print("\nHandling invalid player names:")
    try:
        result = normalize_player_name("", strict=True)
    except ValidationError as e:
        print(f"  ✗ ValidationError: {e}")
    
    result = normalize_player_name("", strict=False)
    print(f"  ✓ Non-strict mode returns: '{result}'")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("NFL PLAYER CHATBOT - VALIDATORS USAGE EXAMPLES")
    print("=" * 60)
    
    example_player_name_normalization()
    example_fuzzy_matching()
    example_time_period_validation()
    example_dataframe_normalization()
    example_stat_validation()
    example_cross_source_consistency()
    example_error_handling()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
