"""
Cache utility functions for NFL Player Performance Chatbot.

This module provides utility functions for managing and monitoring
the cache system, including cache warming, cleanup, and statistics.
"""

import logging
from typing import Dict, Any
import pandas as pd

from cache_manager import get_cache_manager, initialize_cache_manager

logger = logging.getLogger(__name__)


def warm_kaggle_cache(data_path: str = None) -> bool:
    """
    Pre-load Kaggle dataset into cache on startup.
    
    This function should be called during application initialization
    to load the Kaggle dataset into memory for fast access.
    
    Args:
        data_path: Path to Kaggle dataset (optional)
        
    Returns:
        True if cache was warmed successfully, False otherwise
    """
    try:
        logger.info("Warming Kaggle dataset cache...")
        
        from data_sources.kaggle_source import KaggleDataSource
        
        # Create Kaggle source and load data
        kaggle_source = KaggleDataSource(data_path=data_path)
        
        # Check if data is available
        if not kaggle_source.is_available():
            logger.warning("Kaggle dataset not available, skipping cache warming")
            return False
        
        # Load data (this will automatically cache it)
        kaggle_source._load_data()
        
        # Get cache stats
        cache = get_cache_manager()
        cache_info = cache.get_kaggle_cache_info()
        
        if cache_info.get("cached"):
            logger.info(
                f"Kaggle cache warmed successfully: "
                f"{cache_info['records']} records, "
                f"{cache_info['memory_mb']} MB"
            )
            return True
        else:
            logger.warning("Failed to warm Kaggle cache")
            return False
            
    except Exception as e:
        logger.error(f"Error warming Kaggle cache: {e}")
        return False


def get_cache_statistics() -> Dict[str, Any]:
    """
    Get comprehensive cache statistics.
    
    Returns:
        Dictionary with statistics for all cache layers
    """
    cache = get_cache_manager()
    return cache.get_stats()


def print_cache_statistics():
    """
    Print formatted cache statistics to console.
    """
    stats = get_cache_statistics()
    
    print("\n" + "=" * 80)
    print("CACHE STATISTICS")
    print("=" * 80)
    
    # Kaggle cache
    print("\nKaggle Dataset Cache:")
    kaggle_stats = stats.get("kaggle", {})
    if kaggle_stats.get("cached"):
        print(f"  Status: CACHED")
        print(f"  Records: {kaggle_stats['records']:,}")
        print(f"  Memory: {kaggle_stats['memory_mb']} MB")
        print(f"  Age: {kaggle_stats.get('age_seconds', 0):.0f} seconds")
    else:
        print(f"  Status: NOT CACHED")
    
    # nflreadpy cache
    print("\nnflreadpy Data Cache:")
    nflreadpy_stats = stats.get("nflreadpy", {})
    print(f"  Total Entries: {nflreadpy_stats['total_entries']}")
    print(f"  Valid Entries: {nflreadpy_stats['valid_entries']}")
    print(f"  Expired Entries: {nflreadpy_stats['expired_entries']}")
    print(f"  TTL: {nflreadpy_stats['ttl_hours']} hours")
    
    # Query cache
    print("\nQuery Results Cache:")
    query_stats = stats.get("query", {})
    print(f"  Size: {query_stats['size']} / {query_stats['capacity']}")
    print(f"  Hits: {query_stats['hits']}")
    print(f"  Misses: {query_stats['misses']}")
    print(f"  Hit Rate: {query_stats['hit_rate']}%")
    print(f"  Expired Entries: {query_stats['expired_entries']}")
    
    print("=" * 80 + "\n")


def cleanup_expired_cache() -> Dict[str, int]:
    """
    Clean up all expired cache entries.
    
    Returns:
        Dictionary with counts of removed entries per cache
    """
    logger.info("Running cache cleanup...")
    cache = get_cache_manager()
    results = cache.cleanup_expired()
    
    total = sum(results.values())
    logger.info(f"Cache cleanup complete: {total} entries removed")
    
    return results


def clear_all_caches():
    """
    Clear all cache layers.
    
    Warning: This will remove all cached data and may impact performance
    until caches are repopulated.
    """
    logger.warning("Clearing all caches...")
    cache = get_cache_manager()
    cache.clear_all()
    logger.info("All caches cleared")


def invalidate_player_cache(player_name: str) -> int:
    """
    Invalidate all cache entries for a specific player.
    
    Useful when player data needs to be refreshed.
    
    Args:
        player_name: Name of the player
        
    Returns:
        Total number of entries invalidated
    """
    logger.info(f"Invalidating cache for player: {player_name}")
    cache = get_cache_manager()
    
    total = 0
    total += cache.invalidate_nflreadpy_player(player_name)
    total += cache.invalidate_query_cache_by_player(player_name)
    
    logger.info(f"Invalidated {total} cache entries for {player_name}")
    return total


def invalidate_season_cache(season: int) -> int:
    """
    Invalidate all cache entries for a specific season.
    
    Useful when season data needs to be refreshed.
    
    Args:
        season: Season year
        
    Returns:
        Number of entries invalidated
    """
    logger.info(f"Invalidating cache for season: {season}")
    cache = get_cache_manager()
    
    count = cache.invalidate_nflreadpy_season(season)
    
    logger.info(f"Invalidated {count} cache entries for season {season}")
    return count


def configure_cache(
    kaggle_cache_enabled: bool = True,
    nflreadpy_ttl_hours: int = 24,
    query_cache_capacity: int = 100,
    query_cache_ttl_hours: int = 1
):
    """
    Configure the cache manager with custom settings.
    
    This should be called during application initialization before
    any cache operations.
    
    Args:
        kaggle_cache_enabled: Enable Kaggle dataset caching
        nflreadpy_ttl_hours: TTL for nflreadpy data in hours
        query_cache_capacity: Maximum number of query results to cache
        query_cache_ttl_hours: TTL for query cache in hours
    """
    logger.info("Configuring cache manager...")
    
    initialize_cache_manager(
        kaggle_cache_enabled=kaggle_cache_enabled,
        nflreadpy_ttl_hours=nflreadpy_ttl_hours,
        query_cache_capacity=query_cache_capacity,
        query_cache_ttl_hours=query_cache_ttl_hours
    )
    
    logger.info(
        f"Cache configured: "
        f"Kaggle={kaggle_cache_enabled}, "
        f"nflreadpy_ttl={nflreadpy_ttl_hours}h, "
        f"query_capacity={query_cache_capacity}, "
        f"query_ttl={query_cache_ttl_hours}h"
    )


def get_cache_memory_usage() -> Dict[str, float]:
    """
    Estimate memory usage of all caches.
    
    Returns:
        Dictionary with memory usage in MB for each cache
    """
    cache = get_cache_manager()
    stats = cache.get_stats()
    
    memory_usage = {}
    
    # Kaggle cache memory
    kaggle_stats = stats.get("kaggle", {})
    if kaggle_stats.get("cached"):
        memory_usage["kaggle_mb"] = kaggle_stats["memory_mb"]
    else:
        memory_usage["kaggle_mb"] = 0.0
    
    # Estimate nflreadpy cache memory (rough estimate)
    nflreadpy_stats = stats.get("nflreadpy", {})
    # Assume ~100KB per entry on average
    memory_usage["nflreadpy_mb"] = nflreadpy_stats["valid_entries"] * 0.1
    
    # Estimate query cache memory (rough estimate)
    query_stats = stats.get("query", {})
    # Assume ~50KB per entry on average
    memory_usage["query_mb"] = query_stats["size"] * 0.05
    
    # Total
    memory_usage["total_mb"] = sum(memory_usage.values())
    
    return memory_usage


def schedule_cache_cleanup(interval_hours: int = 6):
    """
    Schedule periodic cache cleanup.
    
    Note: This is a placeholder for future implementation.
    In production, you would use a task scheduler like APScheduler
    or a background worker to run cleanup periodically.
    
    Args:
        interval_hours: Cleanup interval in hours
    """
    logger.info(
        f"Cache cleanup scheduling requested (interval: {interval_hours}h). "
        "Note: Automatic scheduling not yet implemented. "
        "Call cleanup_expired_cache() manually or integrate with a task scheduler."
    )


if __name__ == "__main__":
    """
    Command-line interface for cache management.
    """
    import sys
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python cache_utils.py <command>")
        print("\nCommands:")
        print("  stats       - Display cache statistics")
        print("  warm        - Warm Kaggle cache")
        print("  cleanup     - Clean up expired entries")
        print("  clear       - Clear all caches")
        print("  memory      - Show memory usage")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "stats":
        print_cache_statistics()
    
    elif command == "warm":
        success = warm_kaggle_cache()
        if success:
            print("✓ Kaggle cache warmed successfully")
        else:
            print("✗ Failed to warm Kaggle cache")
    
    elif command == "cleanup":
        results = cleanup_expired_cache()
        print(f"Cleaned up {sum(results.values())} expired entries")
        print(f"  nflreadpy: {results.get('nflreadpy', 0)}")
        print(f"  query: {results.get('query', 0)}")
    
    elif command == "clear":
        confirm = input("Are you sure you want to clear all caches? (yes/no): ")
        if confirm.lower() == "yes":
            clear_all_caches()
            print("✓ All caches cleared")
        else:
            print("Cancelled")
    
    elif command == "memory":
        memory = get_cache_memory_usage()
        print("\nCache Memory Usage:")
        print(f"  Kaggle: {memory['kaggle_mb']:.2f} MB")
        print(f"  nflreadpy: {memory['nflreadpy_mb']:.2f} MB")
        print(f"  Query: {memory['query_mb']:.2f} MB")
        print(f"  Total: {memory['total_mb']:.2f} MB")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
