# NFLReadPy Integration Guide

## Overview

The NFL chatbot now uses **nflreadpy** as the primary data source for current season (2024) statistics, providing access to live, up-to-date NFL player performance data.

## Data Source Architecture

### Data Source Priority

The bot uses an intelligent routing system that selects the best data source based on the query:

1. **Current Season (2024)**: 
   - Primary: `nflreadpy` (live data)
   - Fallback: ESPN API, Kaggle dataset

2. **Historical Data (1999-2023)**:
   - Primary: Kaggle dataset
   - Fallback: nflreadpy, ESPN API

### Why NFLReadPy?

- ✅ **Live Data**: Updated regularly with current season statistics
- ✅ **Comprehensive**: 114 columns of detailed player stats
- ✅ **Fast**: Efficient data loading with Polars backend
- ✅ **Reliable**: Automatic retry logic and caching
- ✅ **Rich Stats**: Includes advanced metrics like EPA, CPOE, etc.

## Available Statistics

### Passing Stats
- `passing_yards`, `passing_tds`, `passing_interceptions`
- `completions`, `attempts`, `completion_rate`
- `sacks_suffered`, `sack_yards_lost`
- `passing_air_yards`, `passing_yards_after_catch`
- `passing_epa`, `passing_cpoe` (advanced metrics)

### Rushing Stats
- `rushing_yards`, `rushing_tds`, `rushing_fumbles`
- `carries`, `yards_per_carry`
- `rushing_first_downs`, `rushing_epa`

### Receiving Stats
- `receiving_yards`, `receiving_tds`, `receiving_fumbles`
- `receptions`, `targets`, `target_share`
- `receiving_air_yards`, `receiving_yards_after_catch`
- `receiving_epa`, `racr`, `wopr`

### Defensive Stats
- `def_tackles_solo`, `def_tackles_with_assist`
- `def_sacks`, `def_qb_hits`
- `def_interceptions`, `def_pass_defended`
- `def_fumbles_forced`, `def_tds`

### Special Teams
- `fg_made`, `fg_att`, `fg_pct`, `fg_long`
- `pat_made`, `pat_att`
- `punt_returns`, `kickoff_returns`

### Fantasy Stats
- `fantasy_points` (standard scoring)
- `fantasy_points_ppr` (PPR scoring)

## Sample Queries

### Basic Player Stats
```
"What were Patrick Mahomes' passing yards in week 10?"
"Show me Travis Kelce's receiving stats for 2024"
"How many touchdowns did Christian McCaffrey score this season?"
```

### Comparisons
```
"Compare Patrick Mahomes and Josh Allen passing yards in 2024"
"Who has more receiving yards, Tyreek Hill or CeeDee Lamb?"
"Compare the rushing stats of Derrick Henry and Josh Jacobs"
```

### Recent Performance
```
"How did Lamar Jackson perform last week?"
"Show me Justin Jefferson's targets in the last 3 games"
"What are Brock Purdy's stats from week 15?"
```

### Advanced Queries
```
"What is Patrick Mahomes' EPA this season?"
"Show me the completion percentage for all Chiefs quarterbacks"
"Which running back has the highest yards per carry in 2024?"
```

### Team-Based Queries
```
"How are the Chiefs quarterbacks performing this season?"
"Show me all 49ers receivers' stats"
"What are the Bills' offensive stats?"
```

## Testing the Integration

### Quick Test (3 queries)
```bash
python test_bot_with_nflreadpy.py quick
```

### Full Test Suite (10 queries)
```bash
python test_bot_with_nflreadpy.py
```

### Interactive Mode
```bash
python test_bot_with_nflreadpy.py interactive
```

### Direct Data Source Test
```bash
python test_nflreadpy.py
```

## Caching Strategy

The bot implements multi-level caching for optimal performance:

### 1. NFLReadPy Cache
- **TTL**: 24 hours (configurable)
- **Scope**: Raw player data from nflreadpy
- **Location**: Global cache manager
- **Purpose**: Avoid repeated API calls for same player/season

### 2. Query Cache
- **TTL**: 1 hour (configurable)
- **Capacity**: 100 queries (LRU eviction)
- **Scope**: Complete query results
- **Purpose**: Instant responses for repeated queries

### Cache Configuration

In `.env`:
```env
# NFLReadPy cache TTL in hours
NFLREADPY_CACHE_TTL_HOURS=24

# Query cache settings
QUERY_CACHE_CAPACITY=100
QUERY_CACHE_TTL_HOURS=1
```

## Performance Characteristics

### First Query (Cold Cache)
- Data fetch: ~300-500ms
- Query parsing: ~500-800ms
- LLM generation: ~1-2s
- **Total**: ~2-3 seconds

### Subsequent Queries (Warm Cache)
- Data fetch: <10ms (cached)
- Query parsing: ~500-800ms
- LLM generation: ~1-2s
- **Total**: ~1.5-2.5 seconds

### Repeated Queries (Query Cache Hit)
- **Total**: <100ms (instant)

## Error Handling

The integration includes robust error handling:

### Automatic Fallback
If nflreadpy fails, the bot automatically tries:
1. ESPN API
2. Kaggle dataset (for historical data)

### Retry Logic
- 3 retry attempts with exponential backoff
- Handles transient network errors
- Logs all failures for debugging

### User-Friendly Messages
```
"I couldn't find statistics for that player. Please check the spelling."
"Data for that time period is temporarily unavailable. Please try again."
"I found multiple players with that name. Did you mean [suggestions]?"
```

## Troubleshooting

### Issue: "No module named 'pyarrow'"
**Solution**: Install pyarrow
```bash
pip install pyarrow
```

### Issue: "Player not found"
**Possible causes**:
1. Player name spelling (try full name: "Patrick Mahomes" not "Mahomes")
2. Player hasn't played in 2024 (injured/retired)
3. Player is on practice squad (not in game stats)

**Solution**: Check player name and try alternative spellings

### Issue: Slow first query
**Expected behavior**: First query loads full season data (~19k records)
**Solution**: Subsequent queries use cache and are much faster

### Issue: Missing statistics
**Cause**: Player hasn't recorded that stat type
**Example**: QB won't have receiving_yards
**Solution**: Query appropriate stats for player position

## Configuration

### Environment Variables

```env
# Data source settings
KAGGLE_DATA_PATH=data/nfl_offensive_stats.csv
NFLREADPY_CACHE_TTL_HOURS=24

# Cache settings
KAGGLE_CACHE_ENABLED=true
WARM_KAGGLE_CACHE_ON_STARTUP=true
QUERY_CACHE_CAPACITY=100
QUERY_CACHE_TTL_HOURS=1

# API settings
OPENAI_API_KEY=your_key_here
```

### Programmatic Configuration

```python
from data_sources.nflreadpy_source import NFLReadPyDataSource

# Initialize with custom cache TTL
source = NFLReadPyDataSource(cache_ttl_hours=12)

# Fetch player stats
stats = source.get_player_stats(
    player_name="Patrick Mahomes",
    season=2024,
    week=10,
    stats=["passing_yards", "passing_tds"]
)

# Check availability
if source.is_available():
    print("NFLReadPy is ready!")

# Clear cache
source.clear_cache()
```

## Integration with Chainlit UI

The bot automatically uses nflreadpy when you run the Chainlit app:

```bash
chainlit run app.py
```

The welcome message highlights live data support:
> "Powered by live data from nflreadpy so you can ask about the latest games and stats."

## Data Freshness

- **Update Frequency**: nflreadpy data is updated regularly during the season
- **Cache Refresh**: Automatic after 24 hours (configurable)
- **Manual Refresh**: Clear cache to force fresh data fetch

## Best Practices

### 1. Use Full Player Names
✅ "Patrick Mahomes"
❌ "Mahomes" (may be ambiguous)

### 2. Specify Time Period
✅ "Patrick Mahomes stats in week 10 of 2024"
✅ "Travis Kelce receiving yards this season"
❌ "Show me stats" (too vague)

### 3. Request Relevant Stats
✅ "Patrick Mahomes passing yards" (QB stat)
❌ "Patrick Mahomes receiving yards" (not a QB stat)

### 4. Use Comparisons Wisely
✅ "Compare Patrick Mahomes and Josh Allen" (same position)
⚠️ "Compare Patrick Mahomes and Travis Kelce" (different positions)

## Future Enhancements

Potential improvements for the nflreadpy integration:

1. **Real-time Updates**: Fetch data during live games
2. **Play-by-Play Data**: Access detailed play information
3. **Advanced Analytics**: More EPA, CPOE, and situational stats
4. **Team Aggregations**: Automatic team-level statistics
5. **Historical Trends**: Compare current season to past performance

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Run diagnostic: `python test_nflreadpy.py`
3. Review error messages in console
4. Check cache stats: `cache.get_cache_stats()`

## References

- [nflreadpy Documentation](https://github.com/nflverse/nflreadpy)
- [NFL Data Sources](https://github.com/nflverse)
- [Project README](README.md)
