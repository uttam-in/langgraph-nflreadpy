# Data Validation and Normalization

This document describes the validation and normalization functionality implemented for the NFL Player Performance Chatbot.

## Overview

The `validators.py` module provides comprehensive validation and normalization functions to ensure data consistency across different data sources (Kaggle, nflreadpy, ESPN) and handle user input variations.

## Key Features

### 1. Player Name Normalization

Handles various input formats and common misspellings:

```python
from validators import normalize_player_name

# Handles case variations
normalize_player_name("patrick mahomes")  # -> "Patrick Mahomes"
normalize_player_name("JOSH ALLEN")       # -> "Josh Allen"

# Handles nicknames
normalize_player_name("cmc")              # -> "Christian McCaffrey"

# Handles common misspellings
normalize_player_name("tyreke hill")      # -> "Tyreek Hill"
```

### 2. Fuzzy Player Name Matching

Suggests similar names when exact match fails:

```python
from validators import find_similar_player_names

available_players = ["Patrick Mahomes", "Josh Allen", "Joe Burrow"]
matches = find_similar_player_names("patrick mahommes", available_players)
# Returns: [("Patrick Mahomes", 0.9677), ...]
```

### 3. Time Period Validation

Validates seasons and weeks:

```python
from validators import validate_season, validate_week, validate_time_period

# Validate season (1999-2025)
validate_season(2023)  # -> 2023
validate_season(1990, strict=False)  # -> 1999 (auto-corrected)

# Validate week (1-18)
validate_week(10)  # -> 10
validate_week(25, strict=False)  # -> 18 (clamped)

# Validate complete time period
validate_time_period(season=2023, start_week=1, end_week=17)
# -> {'season': 2023, 'start_week': 1, 'end_week': 17}
```

### 4. Statistical Value Validation

Ensures correct data types for statistics:

```python
from validators import validate_stat_value

# Integer stats
validate_stat_value("passing_yards", "350")  # -> 350 (int)

# Float stats
validate_stat_value("completion_rate", "65.5")  # -> 65.5 (float)

# Handles None/NaN
validate_stat_value("passing_yards", None)  # -> None
```

### 5. DataFrame Normalization

Normalizes DataFrames from different sources:

```python
from validators import validate_and_normalize_player_stats

# Handles inconsistent column names
df = pd.DataFrame({
    "Player": ["patrick mahomes"],
    "Pass Yds": ["350"],
    "Pass TD": [3]
})

df_normalized = validate_and_normalize_player_stats(df)
# Columns: player_name, passing_yards, passing_touchdowns
# Values: "Patrick Mahomes", 350 (int), 3
```

## Integration with Data Sources

The validators are integrated into the data layer:

### Base DataSource Class

```python
# data_sources/base.py
def normalize_player_name(self, name: str) -> str:
    from validators import normalize_player_name as normalize_name
    return normalize_name(name, strict=False)
```

### Kaggle DataSource

```python
# data_sources/kaggle_source.py
from validators import validate_and_normalize_player_stats

# Automatically normalizes data on load
df = pd.read_csv(csv_file)
df = validate_and_normalize_player_stats(df, strict=False)
```

## Validation Rules

### Player Names
- Title case formatting
- Whitespace trimming
- Common misspelling corrections
- Punctuation normalization (e.g., "A.J." vs "AJ")
- Special case handling (McCaffrey, O'Brien)

### Seasons
- Valid range: 1999 to current season
- Auto-correction in non-strict mode
- Raises ValidationError in strict mode

### Weeks
- Valid range: 1-18 (including playoffs)
- Auto-correction in non-strict mode
- Raises ValidationError in strict mode

### Statistical Fields
- Type conversion (string to int/float)
- None/NaN handling
- Validation against known stat fields

### DataFrame Columns
- Lowercase with underscores
- Common abbreviation mapping (Pass Yds -> passing_yards)
- Consistent naming across sources

## Error Handling

Two modes of operation:

### Strict Mode
Raises `ValidationError` for invalid input:

```python
try:
    validate_season(1990, strict=True)
except ValidationError as e:
    print(f"Error: {e}")
```

### Non-Strict Mode
Auto-corrects invalid input:

```python
season = validate_season(1990, strict=False)  # -> 1999
```

## Requirements Addressed

- **Requirement 6.4**: Handle common variations in player name spelling and team references
- **Requirement 4.3**: Normalize data formats across different sources

## Testing

Run the test suite:

```bash
python test_validators.py
```

Run usage examples:

```bash
python validators_usage_example.py
```

## Valid Statistical Fields

The module recognizes the following statistical categories:

**Passing**: completions, attempts, passing_yards, passing_touchdowns, interceptions, sacks, completion_rate, yards_per_attempt, passer_rating, qbr

**Rushing**: rushing_attempts, rushing_yards, rushing_touchdowns, yards_per_carry

**Receiving**: targets, receptions, receiving_yards, receiving_touchdowns, yards_per_reception

**Advanced**: epa, success_rate, cpoe, air_yards, yac, fantasy_points

## Common Column Name Mappings

The normalizer handles these common variations:

- `Pass Yds`, `pass_yds`, `PassYds` → `passing_yards`
- `Pass TD`, `pass_td`, `PassTD` → `passing_touchdowns`
- `Comp`, `comps` → `completions`
- `Att`, `atts` → `attempts`
- `Int`, `ints` → `interceptions`
- `Rec`, `recs` → `receptions`
- `Tgt`, `tgts` → `targets`
- `Player`, `name`, `PlayerName` → `player_name`

## Future Enhancements

Potential improvements:

1. Add more player name corrections as they're discovered
2. Expand team name normalization
3. Add position validation
4. Implement statistical value range validation (e.g., completion_rate 0-100)
5. Add support for playoff week validation
6. Implement data quality scoring
