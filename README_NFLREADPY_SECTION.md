# 🆕 NFLReadPy Integration - Live 2024 Data

## What's New

The chatbot now uses **nflreadpy** to provide **live, current season (2024) NFL statistics**! This means you can ask about the latest games, recent player performance, and up-to-date season totals.

### Key Features

✅ **Live Data**: Access to current 2024 NFL season statistics
✅ **Comprehensive Stats**: 114 columns including passing, rushing, receiving, defensive, and special teams
✅ **Advanced Metrics**: EPA, CPOE, air yards, target share, and more
✅ **Fast Performance**: Intelligent caching with 24-hour TTL
✅ **Automatic Fallback**: Seamless fallback to ESPN/Kaggle if needed

## Quick Start

### Try Sample Queries

```bash
# Quick demo (2 queries)
python demo_nflreadpy.py quick

# Full demo (5 queries)
python demo_nflreadpy.py

# Interactive mode
python test_bot_with_nflreadpy.py interactive

# Web interface
chainlit run app.py
```

### Example Queries

**Current Week Performance**
```
"What were Patrick Mahomes' passing yards in week 10 of 2024?"
```

**Season Overview**
```
"Show me Travis Kelce's receiving stats for the 2024 season"
```

**Player Comparisons**
```
"Compare Patrick Mahomes and Josh Allen passing yards in 2024"
```

**Recent Performance**
```
"How did Lamar Jackson perform last week?"
```

See [SAMPLE_QUERIES.md](SAMPLE_QUERIES.md) for 50+ more examples!

## Data Sources

The bot intelligently routes queries to the best data source:

| Time Period | Primary Source | Fallback |
|-------------|---------------|----------|
| **2024 Season** | nflreadpy (live) | ESPN API, Kaggle |
| **1999-2023** | Kaggle dataset | nflreadpy, ESPN API |

## Available Statistics

### Core Stats
- **Passing**: yards, TDs, completions, attempts, interceptions, sacks
- **Rushing**: yards, TDs, carries, fumbles, yards per carry
- **Receiving**: yards, TDs, receptions, targets, yards per reception
- **Defensive**: tackles, sacks, interceptions, forced fumbles
- **Special Teams**: field goals, punts, returns

### Advanced Metrics
- **EPA** (Expected Points Added)
- **CPOE** (Completion Percentage Over Expected)
- **Air Yards** and **YAC** (Yards After Catch)
- **Target Share**, **WOPR**, **RACR**
- **Fantasy Points** (standard and PPR)

## Performance

- **First Query**: ~2-3 seconds (loads data)
- **Cached Queries**: ~1.5-2 seconds
- **Repeated Queries**: <100ms (instant)
- **Cache Hit Rate**: >80% after warmup

## Documentation

- 📖 [Complete Integration Guide](NFLREADPY_INTEGRATION_GUIDE.md)
- 📝 [Sample Queries](SAMPLE_QUERIES.md) - 50+ example queries
- ✅ [Setup Complete](NFLREADPY_SETUP_COMPLETE.md) - What was accomplished
- 🧪 [Test Results](NFLREADPY_TEST_RESULTS.md) - Detailed test results

## Testing

```bash
# Test data source directly
python test_nflreadpy.py

# Test bot with sample queries (quick)
python test_bot_with_nflreadpy.py quick

# Test bot with all sample queries
python test_bot_with_nflreadpy.py

# Interactive testing
python test_bot_with_nflreadpy.py interactive
```

## Configuration

Add to your `.env` file:

```env
# NFLReadPy cache TTL in hours (default: 24)
NFLREADPY_CACHE_TTL_HOURS=24

# Query cache settings
QUERY_CACHE_CAPACITY=100
QUERY_CACHE_TTL_HOURS=1
```

## Troubleshooting

**Missing pyarrow dependency?**
```bash
pip install pyarrow
```

**Player not found?**
- Use full names: "Patrick Mahomes" not "Mahomes"
- Check spelling
- Verify player played in 2024

**Slow first query?**
- Expected behavior (loads full season data)
- Subsequent queries are much faster

See [NFLREADPY_INTEGRATION_GUIDE.md](NFLREADPY_INTEGRATION_GUIDE.md) for more help.

---

**Add this section to your README.md after the "Features" section to highlight the new nflreadpy integration!**
