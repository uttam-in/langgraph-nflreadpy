"""
Test script for validators module.
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
    normalize_dataframe_values,
    validate_and_normalize_player_stats,
    ValidationError
)


def test_player_name_normalization():
    """Test player name normalization."""
    print("Testing player name normalization...")
    
    # Test known corrections
    assert normalize_player_name("patrick mahomes") == "Patrick Mahomes"
    assert normalize_player_name("pat mahomes") == "Patrick Mahomes"
    assert normalize_player_name("cmc") == "Christian McCaffrey"
    
    # Test case normalization
    assert normalize_player_name("josh allen") == "Josh Allen"
    assert normalize_player_name("JOSH ALLEN") == "Josh Allen"
    
    # Test whitespace handling
    assert normalize_player_name("  josh allen  ") == "Josh Allen"
    
    # Test special cases
    assert "Mc" in normalize_player_name("christian mccaffrey")
    
    print("✓ Player name normalization tests passed")


def test_fuzzy_matching():
    """Test fuzzy player name matching."""
    print("\nTesting fuzzy player name matching...")
    
    available_names = ["Patrick Mahomes", "Josh Allen", "Joe Burrow", "Lamar Jackson"]
    
    # Test close match
    matches = find_similar_player_names("patrick mahommes", available_names, threshold=0.7)
    assert len(matches) > 0
    assert matches[0][0] == "Patrick Mahomes"
    
    # Test exact match
    matches = find_similar_player_names("Josh Allen", available_names, threshold=0.9)
    assert len(matches) > 0
    assert matches[0][0] == "Josh Allen"
    
    print("✓ Fuzzy matching tests passed")


def test_season_validation():
    """Test season validation."""
    print("\nTesting season validation...")
    
    # Valid season
    assert validate_season(2023) == 2023
    assert validate_season("2023") == 2023
    
    # Invalid season (should raise error in strict mode)
    try:
        validate_season(1990, strict=True)
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass
    
    # Invalid season (should clamp in non-strict mode)
    result = validate_season(1990, strict=False)
    assert result >= 1999
    
    print("✓ Season validation tests passed")


def test_week_validation():
    """Test week validation."""
    print("\nTesting week validation...")
    
    # Valid weeks
    assert validate_week(1) == 1
    assert validate_week(17) == 17
    assert validate_week("10") == 10
    
    # Invalid week (should raise error in strict mode)
    try:
        validate_week(25, strict=True)
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass
    
    # Invalid week (should clamp in non-strict mode)
    result = validate_week(25, strict=False)
    assert result <= 18
    
    print("✓ Week validation tests passed")


def test_time_period_validation():
    """Test time period validation."""
    print("\nTesting time period validation...")
    
    # Valid time period
    result = validate_time_period(season=2023, start_week=1, end_week=17)
    assert result["season"] == 2023
    assert result["start_week"] == 1
    assert result["end_week"] == 17
    
    # Invalid week range (should swap in non-strict mode)
    result = validate_time_period(season=2023, start_week=10, end_week=5, strict=False)
    assert result["start_week"] == 5
    assert result["end_week"] == 10
    
    print("✓ Time period validation tests passed")


def test_stat_value_validation():
    """Test statistical value validation."""
    print("\nTesting stat value validation...")
    
    # Integer stats
    assert validate_stat_value("passing_yards", 350) == 350
    assert validate_stat_value("passing_yards", "350") == 350
    assert validate_stat_value("passing_yards", 350.5) == 350
    
    # Float stats
    assert validate_stat_value("completion_rate", 65.5) == 65.5
    assert validate_stat_value("completion_rate", "65.5") == 65.5
    
    # None values
    assert validate_stat_value("passing_yards", None) is None
    
    print("✓ Stat value validation tests passed")


def test_stat_name_normalization():
    """Test stat name normalization."""
    print("\nTesting stat name normalization...")
    
    # Test normalization
    stats = ["passing yards", "Touchdowns", "completion-rate"]
    normalized = normalize_stat_names(stats)
    
    assert "passing_yards" in normalized or "passing" in normalized[0]
    assert all("_" in stat or stat.isalpha() for stat in normalized)
    
    print("✓ Stat name normalization tests passed")


def test_dataframe_normalization():
    """Test DataFrame normalization."""
    print("\nTesting DataFrame normalization...")
    
    # Create test DataFrame with inconsistent naming
    df = pd.DataFrame({
        "Player": ["patrick mahomes", "josh allen"],
        "Pass Yds": [350, 300],
        "Pass TD": [3, 2],
        "Comp": [25, 22],
        "Att": [35, 30],
        "Season": [2023, 2023]
    })
    
    # Normalize columns
    df_normalized = normalize_dataframe_columns(df)
    
    # Check that columns are normalized
    assert "player_name" in df_normalized.columns
    assert "passing_yards" in df_normalized.columns
    assert "passing_touchdowns" in df_normalized.columns
    
    # Normalize values
    df_normalized = normalize_dataframe_values(df_normalized)
    
    # Check that player names are normalized
    assert df_normalized["player_name"].iloc[0] == "Patrick Mahomes"
    assert df_normalized["player_name"].iloc[1] == "Josh Allen"
    
    print("✓ DataFrame normalization tests passed")


def test_complete_pipeline():
    """Test complete validation and normalization pipeline."""
    print("\nTesting complete pipeline...")
    
    # Create test DataFrame
    df = pd.DataFrame({
        "Player": ["pat mahomes", "JOSH ALLEN", "joe burrow"],
        "Pass Yds": ["350", "300", "280"],
        "Pass TD": [3, 2, 2],
        "Comp": [25.0, 22.0, 20.0],
        "Season": [2023, 2023, 2023]
    })
    
    # Run complete pipeline
    df_result = validate_and_normalize_player_stats(df, strict=False)
    
    # Verify results
    assert "player_name" in df_result.columns
    assert "passing_yards" in df_result.columns
    assert df_result["player_name"].iloc[0] == "Patrick Mahomes"
    assert df_result["passing_yards"].iloc[0] == 350
    
    print("✓ Complete pipeline tests passed")


if __name__ == "__main__":
    print("Running validator tests...\n")
    
    test_player_name_normalization()
    test_fuzzy_matching()
    test_season_validation()
    test_week_validation()
    test_time_period_validation()
    test_stat_value_validation()
    test_stat_name_normalization()
    test_dataframe_normalization()
    test_complete_pipeline()
    
    print("\n" + "="*50)
    print("All validator tests passed! ✓")
    print("="*50)
