# Caching Layer Documentation

## Overview

The NFL Player Performance Chatbot implements a comprehensive caching layer to improve performance and reduce load on data sources. The caching system consists of three main components:

1. **Kaggle Dataset Cache** - In-memory cache for the historical dataset (1999-2023)
2. **nflreadpy Data Cache** - TTL-based cache for current season data (24-hour expiration)
3. **Query Results Cache** - LRU cache for frequently queried player statistics (1-hour expiration)

## Architecture

### Cache Manager (`cache_manager.py`)

The `CacheManager` class provides centralized cache management with the following features:

- **Multiple cache layers** with different strategies
- **TTL-based expiration** for time-sensitive data
- **LRU eviction** for query results cache
- **Cache invalidation** by player, season, or tag
- **Statistics and monitoring** for cache performance

### Cache Utilities (`cache_utils.py`)

Utility functions for cache management:

- `warm_kaggle_cache()` - Pre-load Kaggle dataset on startup
- `get_cache_statistics()` - Get comprehensive cache stats
- `cleanup_expired_cache()` - Remove expired entries
- `invalidate_player_cache()` - Invalidate specific player data
- `configure_cache()` - Configure cache settings

## Configuration

Cache settings can be configured via environment variables in `.env`:

```bash
# Enable/disable Kaggle dataset caching
KAGGLE_CACHE_ENABLED=true

# Warm Kaggle cache on startup (recommended)
WARM_KAGGLE_CACHE_ON_STARTUP=true

# Path to Kaggle dataset
KAGGLE_DATA_PATH=./data/kaggle

# TTL for nflreadpy data (hours)
NFLREADPY_CACHE_TTL_HOURS=24

# Query cache capacity (max entries)
QUERY_CACHE_CAPACITY=100

# TTL for query results (hours)
QUERY_CACHE_TTL_HOURS=1
```

## Usage

### Automatic Caching

The caching layer is automatically integrated into the data sources and retriever node. No code changes are required to benefit from caching.

### Manual Cache Management

```python
from cache_utils import (
    get_cache_statistics,
    cleanup_expired_cache,
    invalidate_player_cache,
    clear_all_caches
)

# Get cache statistics
stats = get_cache_statistics()
print(f"Query cache hit rate: {stats['query']['hit_rate']}%")

# Clean up expired entries
cleanup_expired_cache()

# Invalidate cache for a specific player
invalidate_player_cache("Patrick Mahomes")

# Clear all caches (use with caution)
clear_all_caches()
```

### Command-Line Interface

The cache utilities can be accessed via command line:

```bash
# Display cache statistics
python cache_utils.py stats

# Warm Kaggle cache
python cache_utils.py warm

# Clean up expired entries
python cache_utils.py cleanup

# Clear all caches
python cache_utils.py clear

# Show memory usage
python cache_utils.py memory
```

## Cache Layers

### 1. Kaggle Dataset Cache

**Purpose**: Store the entire Kaggle dataset in memory for fast access to historical data (1999-2023).

**Characteristics**:
- **Storage**: In-memory DataFrame
- **Expiration**: No expiration (persistent during runtime)
- **Size**: ~50-200 MB depending on dataset
- **Warming**: Loaded on startup if `WARM_KAGGLE_CACHE_ON_STARTUP=true`

**Benefits**:
- Eliminates repeated CSV file reads
- Instant access to historical data
- Reduces disk I/O

### 2. nflreadpy Data Cache

**Purpose**: Cache current season data from nflreadpy with automatic expiration.

**Characteristics**:
- **Storage**: Dictionary of DataFrames keyed by player/season/week
- **Expiration**: 24 hours (configurable)
- **Size**: ~100 KB per player/season/week combination
- **Invalidation**: By player or season

**Benefits**:
- Reduces API calls to nflreadpy
- Provides fresh data with daily updates
- Handles multiple concurrent requests efficiently

### 3. Query Results Cache

**Purpose**: Cache frequently queried player statistics to avoid redundant data processing.

**Characteristics**:
- **Storage**: LRU cache with configurable capacity
- **Expiration**: 1 hour (configurable)
- **Capacity**: 100 entries (configurable)
- **Eviction**: Least Recently Used (LRU)

**Benefits**:
- Instant responses for repeated queries
- Reduces load on data sources
- Improves user experience with faster responses

## Cache Keys

### nflreadpy Cache Key Format
```
nflreadpy:{player_name}:{season}:{week}
```

Example: `nflreadpy:Patrick Mahomes:2024:1`

### Query Cache Key Format
```
query:{md5_hash_of_params}
```

The hash is generated from query parameters including players, statistics, season, week, filters, and aggregation.

## Cache Invalidation

### Automatic Invalidation

- **TTL Expiration**: Entries automatically expire after their TTL
- **Capacity Eviction**: LRU cache evicts least recently used entries when full

### Manual Invalidation

```python
from cache_manager import get_cache_manager

cache = get_cache_manager()

# Invalidate all data for a player
cache.invalidate_nflreadpy_player("Patrick Mahomes")

# Invalidate all data for a season
cache.invalidate_nflreadpy_season(2024)

# Clear specific cache layer
cache.clear_nflreadpy_cache()
cache.clear_query_cache()
cache.clear_kaggle_cache()

# Clear all caches
cache.clear_all()
```

## Monitoring

### Cache Statistics

```python
from cache_utils import print_cache_statistics

# Print formatted statistics
print_cache_statistics()
```

Output:
```
================================================================================
CACHE STATISTICS
================================================================================

Kaggle Dataset Cache:
  Status: CACHED
  Records: 50,000
  Memory: 125.5 MB
  Age: 3600 seconds

nflreadpy Data Cache:
  Total Entries: 15
  Valid Entries: 12
  Expired Entries: 3
  TTL: 24.0 hours

Query Results Cache:
  Size: 45 / 100
  Hits: 234
  Misses: 56
  Hit Rate: 80.69%
  Expired Entries: 2
================================================================================
```

### Memory Usage

```python
from cache_utils import get_cache_memory_usage

memory = get_cache_memory_usage()
print(f"Total cache memory: {memory['total_mb']:.2f} MB")
```

## Performance Impact

### Expected Performance Improvements

1. **Kaggle Dataset Access**
   - Without cache: ~500-1000ms (CSV read)
   - With cache: ~1-5ms (memory access)
   - **Improvement**: 100-1000x faster

2. **nflreadpy API Calls**
   - Without cache: ~200-500ms (API call)
   - With cache: ~1-5ms (memory access)
   - **Improvement**: 40-500x faster

3. **Repeated Queries**
   - Without cache: Full data retrieval + processing
   - With cache: ~1-5ms (memory access)
   - **Improvement**: 50-200x faster

### Memory Considerations

- **Kaggle Cache**: 50-200 MB (one-time cost)
- **nflreadpy Cache**: ~100 KB per entry × number of cached players
- **Query Cache**: ~50 KB per entry × cache capacity

**Total Estimated Memory**: 100-500 MB depending on usage patterns

## Best Practices

### 1. Cache Warming

Always warm the Kaggle cache on startup in production:

```bash
WARM_KAGGLE_CACHE_ON_STARTUP=true
```

### 2. TTL Configuration

- **Historical data**: No expiration (Kaggle cache)
- **Current season**: 24 hours (nflreadpy cache)
- **Query results**: 1 hour (query cache)

Adjust based on your data freshness requirements.

### 3. Capacity Planning

Set query cache capacity based on expected concurrent users:

- **Small deployment** (< 10 users): 50 entries
- **Medium deployment** (10-100 users): 100-200 entries
- **Large deployment** (> 100 users): 500+ entries

### 4. Monitoring

Regularly monitor cache statistics to optimize settings:

```bash
python cache_utils.py stats
```

Look for:
- **Hit rate** > 70% (good cache effectiveness)
- **Expired entries** < 10% (appropriate TTL)
- **Memory usage** within acceptable limits

### 5. Cleanup

Schedule periodic cleanup to remove expired entries:

```python
from cache_utils import cleanup_expired_cache
import schedule

# Run cleanup every 6 hours
schedule.every(6).hours.do(cleanup_expired_cache)
```

## Troubleshooting

### High Memory Usage

If cache memory usage is too high:

1. Reduce query cache capacity
2. Disable Kaggle cache if not needed
3. Reduce TTL values

```bash
KAGGLE_CACHE_ENABLED=false
QUERY_CACHE_CAPACITY=50
NFLREADPY_CACHE_TTL_HOURS=12
```

### Low Hit Rate

If query cache hit rate is low (< 50%):

1. Increase cache capacity
2. Increase TTL
3. Check if queries are too diverse

### Stale Data

If data seems outdated:

1. Reduce TTL values
2. Manually invalidate cache
3. Clear specific player/season data

```python
from cache_utils import invalidate_player_cache

invalidate_player_cache("Patrick Mahomes")
```

## Testing

Run cache tests to verify functionality:

```bash
python test_cache.py
```

This tests:
- Cache initialization
- Kaggle dataset caching
- nflreadpy data caching with TTL
- Query results caching
- Cache expiration
- LRU eviction
- Cache statistics

## Future Enhancements

Potential improvements for the caching layer:

1. **Distributed Caching**: Use Redis for multi-instance deployments
2. **Persistent Cache**: Save cache to disk for faster restarts
3. **Smart Prefetching**: Predict and cache likely queries
4. **Compression**: Compress cached data to reduce memory
5. **Cache Warming**: Pre-populate cache with popular players
6. **Metrics Export**: Export cache metrics to monitoring systems

## Requirements Addressed

This caching implementation addresses requirement **4.4**:

- ✅ In-memory cache for Kaggle dataset on startup
- ✅ TTL-based caching for nflreadpy data (24-hour expiration)
- ✅ Cache for frequently queried player statistics
- ✅ Cache invalidation logic

The caching layer significantly improves application performance while maintaining data freshness and providing flexible configuration options.
