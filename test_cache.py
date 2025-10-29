"""
Test script for cache functionality.

This script tests the caching layer implementation to ensure:
- Kaggle dataset caching works correctly
- nflreadpy data caching with TTL works
- Query result caching works
- Cache invalidation works
"""

import logging
import time
from datetime import timedelta
import pandas as pd

from cache_manager import CacheManager, get_cache_manager, initialize_cache_manager
from cache_utils import (
    configure_cache,
    warm_kaggle_cache,
    get_cache_statistics,
    print_cache_statistics,
    cleanup_expired_cache,
    invalidate_player_cache
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_cache_manager_initialization():
    """Test cache manager initialization."""
    print("\n" + "=" * 80)
    print("TEST: Cache Manager Initialization")
    print("=" * 80)
    
    # Initialize with custom settings
    cache = initialize_cache_manager(
        kaggle_cache_enabled=True,
        nflreadpy_ttl_hours=1,  # Short TTL for testing
        query_cache_capacity=10,
        query_cache_ttl_hours=1
    )
    
    assert cache is not None, "Cache manager should be initialized"
    print("✓ Cache manager initialized successfully")
    
    # Get stats
    stats = cache.get_stats()
    print(f"✓ Initial stats retrieved: {stats}")
    
    return cache


def test_kaggle_cache():
    """Test Kaggle dataset caching."""
    print("\n" + "=" * 80)
    print("TEST: Kaggle Dataset Cache")
    print("=" * 80)
    
    cache = get_cache_manager()
    
    # Create sample data
    sample_data = pd.DataFrame({
        'player_name': ['Patrick Mahomes', 'Josh Allen', 'Joe Burrow'],
        'team': ['KC', 'BUF', 'CIN'],
        'passing_yards': [5250, 4283, 4475],
        'season': [2023, 2023, 2023]
    })
    
    # Cache the data
    cache.set_kaggle_data(sample_data)
    print("✓ Kaggle data cached")
    
    # Retrieve from cache
    cached_data = cache.get_kaggle_data()
    assert cached_data is not None, "Should retrieve cached data"
    assert len(cached_data) == 3, "Should have 3 records"
    print(f"✓ Retrieved {len(cached_data)} records from cache")
    
    # Get cache info
    info = cache.get_kaggle_cache_info()
    print(f"✓ Cache info: {info}")
    
    # Clear cache
    cache.clear_kaggle_cache()
    assert cache.get_kaggle_data() is None, "Cache should be empty after clear"
    print("✓ Cache cleared successfully")


def test_nflreadpy_cache():
    """Test nflreadpy data caching with TTL."""
    print("\n" + "=" * 80)
    print("TEST: nflreadpy Data Cache (with TTL)")
    print("=" * 80)
    
    cache = get_cache_manager()
    
    # Create sample data
    sample_data = pd.DataFrame({
        'player_name': ['Patrick Mahomes'],
        'team': ['KC'],
        'passing_yards': [320],
        'week': [1],
        'season': [2024]
    })
    
    # Cache the data
    player_name = "Patrick Mahomes"
    season = 2024
    week = 1
    
    cache.set_nflreadpy_data(player_name, sample_data, season, week)
    print(f"✓ nflreadpy data cached for {player_name}")
    
    # Retrieve from cache
    cached_data = cache.get_nflreadpy_data(player_name, season, week)
    assert cached_data is not None, "Should retrieve cached data"
    assert len(cached_data) == 1, "Should have 1 record"
    print(f"✓ Retrieved data from cache")
    
    # Test cache miss
    cached_data = cache.get_nflreadpy_data("Josh Allen", season, week)
    assert cached_data is None, "Should return None for cache miss"
    print("✓ Cache miss handled correctly")
    
    # Test invalidation by player
    count = cache.invalidate_nflreadpy_player(player_name)
    assert count == 1, "Should invalidate 1 entry"
    print(f"✓ Invalidated {count} entry for {player_name}")
    
    # Verify invalidation
    cached_data = cache.get_nflreadpy_data(player_name, season, week)
    assert cached_data is None, "Cache should be empty after invalidation"
    print("✓ Invalidation verified")


def test_query_cache():
    """Test query results caching."""
    print("\n" + "=" * 80)
    print("TEST: Query Results Cache")
    print("=" * 80)
    
    cache = get_cache_manager()
    
    # Create sample query and result
    query_params = {
        "players": ["Patrick Mahomes"],
        "statistics": ["passing_yards"],
        "season": 2023,
        "week": None,
        "filters": {},
        "aggregation": None
    }
    
    result_data = pd.DataFrame({
        'player_name': ['Patrick Mahomes'],
        'passing_yards': [5250],
        'season': [2023]
    })
    
    # Cache the result
    cache.set_query_result(query_params, result_data)
    print("✓ Query result cached")
    
    # Retrieve from cache
    cached_result = cache.get_query_result(query_params)
    assert cached_result is not None, "Should retrieve cached result"
    assert len(cached_result) == 1, "Should have 1 record"
    print(f"✓ Retrieved query result from cache")
    
    # Test cache miss with different params
    different_params = {**query_params, "season": 2022}
    cached_result = cache.get_query_result(different_params)
    assert cached_result is None, "Should return None for different params"
    print("✓ Cache miss for different params handled correctly")
    
    # Get cache stats
    stats = cache._query_cache.get_stats()
    print(f"✓ Query cache stats: hits={stats['hits']}, misses={stats['misses']}, hit_rate={stats['hit_rate']}%")


def test_cache_expiration():
    """Test cache TTL and expiration."""
    print("\n" + "=" * 80)
    print("TEST: Cache Expiration (TTL)")
    print("=" * 80)
    
    # Create cache with very short TTL for testing
    cache = initialize_cache_manager(
        kaggle_cache_enabled=True,
        nflreadpy_ttl_hours=0.0001,  # ~0.36 seconds
        query_cache_capacity=10,
        query_cache_ttl_hours=0.0001
    )
    
    # Cache some data
    sample_data = pd.DataFrame({'test': [1, 2, 3]})
    cache.set_nflreadpy_data("Test Player", sample_data, 2024, 1)
    
    # Should be in cache immediately
    cached = cache.get_nflreadpy_data("Test Player", 2024, 1)
    assert cached is not None, "Should be in cache immediately"
    print("✓ Data cached successfully")
    
    # Wait for expiration
    print("⏳ Waiting for cache to expire...")
    time.sleep(1)
    
    # Should be expired now
    cached = cache.get_nflreadpy_data("Test Player", 2024, 1)
    assert cached is None, "Should be expired after TTL"
    print("✓ Cache expired correctly after TTL")
    
    # Test cleanup
    cache.set_nflreadpy_data("Test Player 2", sample_data, 2024, 2)
    time.sleep(1)
    
    cleanup_results = cache.cleanup_expired()
    print(f"✓ Cleanup removed {cleanup_results['nflreadpy']} expired entries")


def test_lru_eviction():
    """Test LRU cache eviction."""
    print("\n" + "=" * 80)
    print("TEST: LRU Cache Eviction")
    print("=" * 80)
    
    # Create cache with small capacity
    cache = initialize_cache_manager(
        kaggle_cache_enabled=True,
        nflreadpy_ttl_hours=24,
        query_cache_capacity=3,  # Small capacity for testing
        query_cache_ttl_hours=1
    )
    
    # Add 4 items (should evict the first one)
    for i in range(4):
        query_params = {"test": i}
        result = pd.DataFrame({'value': [i]})
        cache.set_query_result(query_params, result)
        print(f"  Added query {i}")
    
    # First item should be evicted
    first_params = {"test": 0}
    cached = cache.get_query_result(first_params)
    assert cached is None, "First item should be evicted"
    print("✓ LRU eviction working correctly")
    
    # Other items should still be there
    for i in range(1, 4):
        params = {"test": i}
        cached = cache.get_query_result(params)
        assert cached is not None, f"Item {i} should still be in cache"
    print("✓ Recent items retained in cache")


def test_cache_statistics():
    """Test cache statistics reporting."""
    print("\n" + "=" * 80)
    print("TEST: Cache Statistics")
    print("=" * 80)
    
    # Get and print statistics
    print_cache_statistics()
    
    stats = get_cache_statistics()
    assert "kaggle" in stats, "Should have Kaggle stats"
    assert "nflreadpy" in stats, "Should have nflreadpy stats"
    assert "query" in stats, "Should have query stats"
    print("✓ Statistics retrieved successfully")


def run_all_tests():
    """Run all cache tests."""
    print("\n" + "=" * 80)
    print("RUNNING CACHE TESTS")
    print("=" * 80)
    
    try:
        test_cache_manager_initialization()
        test_kaggle_cache()
        test_nflreadpy_cache()
        test_query_cache()
        test_cache_expiration()
        test_lru_eviction()
        test_cache_statistics()
        
        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80 + "\n")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n✗ ERROR: {e}\n")
        raise


if __name__ == "__main__":
    run_all_tests()
