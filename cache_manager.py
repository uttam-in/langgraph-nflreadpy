"""
Cache Manager for NFL Player Performance Chatbot.

This module provides a centralized caching layer for the chatbot with:
- In-memory cache for Kaggle dataset on startup
- TTL-based caching for nflreadpy data (24-hour expiration)
- Cache for frequently queried player statistics
- Cache invalidation logic

Requirements addressed:
- 4.4: Implement caching to improve performance and reduce data source load
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple
from collections import OrderedDict
import pandas as pd
import hashlib
import json

logger = logging.getLogger(__name__)


class CacheEntry:
    """
    Represents a single cache entry with data and metadata.
    """
    
    def __init__(
        self,
        data: Any,
        ttl: Optional[timedelta] = None,
        tags: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a cache entry.
        
        Args:
            data: The cached data
            ttl: Time-to-live for this entry (None = no expiration)
            tags: Optional metadata tags for cache management
        """
        self.data = data
        self.created_at = datetime.now()
        self.ttl = ttl
        self.last_accessed = datetime.now()
        self.access_count = 0
        self.tags = tags or {}
    
    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        if self.ttl is None:
            return False
        return datetime.now() - self.created_at > self.ttl
    
    def access(self) -> Any:
        """
        Access the cached data and update access metadata.
        
        Returns:
            The cached data
        """
        self.last_accessed = datetime.now()
        self.access_count += 1
        return self.data
    
    def age(self) -> timedelta:
        """Get the age of this cache entry."""
        return datetime.now() - self.created_at


class LRUCache:
    """
    Least Recently Used (LRU) cache implementation.
    
    Automatically evicts least recently used entries when capacity is reached.
    """
    
    def __init__(self, capacity: int = 100):
        """
        Initialize LRU cache.
        
        Args:
            capacity: Maximum number of entries to store
        """
        self.capacity = capacity
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key not in self.cache:
            self._misses += 1
            return None
        
        entry = self.cache[key]
        
        # Check if expired
        if entry.is_expired():
            logger.debug(f"Cache entry expired: {key}")
            del self.cache[key]
            self._misses += 1
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        self._hits += 1
        
        return entry.access()
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None,
        tags: Optional[Dict[str, Any]] = None
    ):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live for this entry
            tags: Optional metadata tags
        """
        # Remove existing entry if present
        if key in self.cache:
            del self.cache[key]
        
        # Check capacity and evict if necessary
        if len(self.cache) >= self.capacity:
            # Remove least recently used (first item)
            evicted_key, evicted_entry = self.cache.popitem(last=False)
            logger.debug(
                f"Cache capacity reached. Evicted: {evicted_key} "
                f"(age: {evicted_entry.age()}, accesses: {evicted_entry.access_count})"
            )
        
        # Add new entry
        entry = CacheEntry(value, ttl=ttl, tags=tags)
        self.cache[key] = entry
        logger.debug(f"Cache entry added: {key} (TTL: {ttl})")
    
    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if entry was deleted, False if not found
        """
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"Cache entry deleted: {key}")
            return True
        return False
    
    def clear(self):
        """Clear all entries from cache."""
        count = len(self.cache)
        self.cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info(f"Cache cleared ({count} entries removed)")
    
    def invalidate_by_tag(self, tag_key: str, tag_value: Any) -> int:
        """
        Invalidate all cache entries matching a tag.
        
        Args:
            tag_key: Tag key to match
            tag_value: Tag value to match
            
        Returns:
            Number of entries invalidated
        """
        keys_to_delete = []
        
        for key, entry in self.cache.items():
            if entry.tags.get(tag_key) == tag_value:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self.cache[key]
        
        if keys_to_delete:
            logger.info(
                f"Invalidated {len(keys_to_delete)} cache entries "
                f"with tag {tag_key}={tag_value}"
            )
        
        return len(keys_to_delete)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        # Count expired entries
        expired_count = sum(1 for entry in self.cache.values() if entry.is_expired())
        
        return {
            "size": len(self.cache),
            "capacity": self.capacity,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2),
            "expired_entries": expired_count
        }
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        keys_to_delete = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]
        
        for key in keys_to_delete:
            del self.cache[key]
        
        if keys_to_delete:
            logger.info(f"Cleaned up {len(keys_to_delete)} expired cache entries")
        
        return len(keys_to_delete)


class CacheManager:
    """
    Centralized cache manager for the NFL Player Performance Chatbot.
    
    Manages multiple cache layers:
    - Kaggle dataset cache (persistent during runtime)
    - nflreadpy data cache (24-hour TTL)
    - Player statistics query cache (1-hour TTL)
    """
    
    def __init__(
        self,
        kaggle_cache_enabled: bool = True,
        nflreadpy_ttl_hours: int = 24,
        query_cache_capacity: int = 100,
        query_cache_ttl_hours: int = 1
    ):
        """
        Initialize the cache manager.
        
        Args:
            kaggle_cache_enabled: Enable in-memory caching for Kaggle dataset
            nflreadpy_ttl_hours: TTL for nflreadpy data in hours
            query_cache_capacity: Maximum number of query results to cache
            query_cache_ttl_hours: TTL for query cache in hours
        """
        self.kaggle_cache_enabled = kaggle_cache_enabled
        self.nflreadpy_ttl = timedelta(hours=nflreadpy_ttl_hours)
        self.query_cache_ttl = timedelta(hours=query_cache_ttl_hours)
        
        # Kaggle dataset cache (single entry, no expiration)
        self._kaggle_data: Optional[pd.DataFrame] = None
        self._kaggle_loaded_at: Optional[datetime] = None
        
        # nflreadpy data cache (TTL-based)
        self._nflreadpy_cache: Dict[str, CacheEntry] = {}
        
        # Query results cache (LRU with TTL)
        self._query_cache = LRUCache(capacity=query_cache_capacity)
        
        logger.info(
            f"CacheManager initialized: "
            f"Kaggle={kaggle_cache_enabled}, "
            f"nflreadpy_ttl={nflreadpy_ttl_hours}h, "
            f"query_capacity={query_cache_capacity}, "
            f"query_ttl={query_cache_ttl_hours}h"
        )
    
    # Kaggle Dataset Cache Methods
    
    def get_kaggle_data(self) -> Optional[pd.DataFrame]:
        """
        Get cached Kaggle dataset.
        
        Returns:
            Cached DataFrame or None if not cached
        """
        if not self.kaggle_cache_enabled:
            return None
        
        if self._kaggle_data is not None:
            logger.debug("Returning cached Kaggle dataset")
            return self._kaggle_data
        
        return None
    
    def set_kaggle_data(self, data: pd.DataFrame):
        """
        Cache the Kaggle dataset in memory.
        
        Args:
            data: Kaggle dataset DataFrame
        """
        if not self.kaggle_cache_enabled:
            logger.debug("Kaggle caching disabled, skipping cache")
            return
        
        self._kaggle_data = data
        self._kaggle_loaded_at = datetime.now()
        
        logger.info(
            f"Kaggle dataset cached: {len(data)} records, "
            f"{data.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"
        )
    
    def clear_kaggle_cache(self):
        """Clear the Kaggle dataset cache."""
        if self._kaggle_data is not None:
            logger.info("Clearing Kaggle dataset cache")
            self._kaggle_data = None
            self._kaggle_loaded_at = None
    
    def get_kaggle_cache_info(self) -> Dict[str, Any]:
        """
        Get information about Kaggle cache.
        
        Returns:
            Dictionary with cache information
        """
        if self._kaggle_data is None:
            return {"cached": False}
        
        return {
            "cached": True,
            "records": len(self._kaggle_data),
            "memory_mb": round(
                self._kaggle_data.memory_usage(deep=True).sum() / 1024 / 1024,
                2
            ),
            "loaded_at": self._kaggle_loaded_at.isoformat() if self._kaggle_loaded_at else None,
            "age_seconds": (
                (datetime.now() - self._kaggle_loaded_at).total_seconds()
                if self._kaggle_loaded_at else None
            )
        }
    
    # nflreadpy Data Cache Methods
    
    def _make_nflreadpy_key(
        self,
        player_name: str,
        season: Optional[int],
        week: Optional[int]
    ) -> str:
        """Generate cache key for nflreadpy data."""
        return f"nflreadpy:{player_name}:{season}:{week}"
    
    def get_nflreadpy_data(
        self,
        player_name: str,
        season: Optional[int] = None,
        week: Optional[int] = None
    ) -> Optional[pd.DataFrame]:
        """
        Get cached nflreadpy data.
        
        Args:
            player_name: Player name
            season: Season year
            week: Week number
            
        Returns:
            Cached DataFrame or None if not cached or expired
        """
        key = self._make_nflreadpy_key(player_name, season, week)
        
        if key not in self._nflreadpy_cache:
            return None
        
        entry = self._nflreadpy_cache[key]
        
        # Check if expired
        if entry.is_expired():
            logger.debug(f"nflreadpy cache entry expired: {key}")
            del self._nflreadpy_cache[key]
            return None
        
        logger.debug(f"Returning cached nflreadpy data: {key}")
        return entry.access()
    
    def set_nflreadpy_data(
        self,
        player_name: str,
        data: pd.DataFrame,
        season: Optional[int] = None,
        week: Optional[int] = None
    ):
        """
        Cache nflreadpy data with TTL.
        
        Args:
            player_name: Player name
            data: Data to cache
            season: Season year
            week: Week number
        """
        key = self._make_nflreadpy_key(player_name, season, week)
        
        entry = CacheEntry(
            data=data,
            ttl=self.nflreadpy_ttl,
            tags={
                "source": "nflreadpy",
                "player": player_name,
                "season": season
            }
        )
        
        self._nflreadpy_cache[key] = entry
        
        logger.debug(
            f"nflreadpy data cached: {key} "
            f"(TTL: {self.nflreadpy_ttl}, records: {len(data)})"
        )
    
    def invalidate_nflreadpy_player(self, player_name: str) -> int:
        """
        Invalidate all nflreadpy cache entries for a player.
        
        Args:
            player_name: Player name
            
        Returns:
            Number of entries invalidated
        """
        keys_to_delete = [
            key for key, entry in self._nflreadpy_cache.items()
            if entry.tags.get("player") == player_name
        ]
        
        for key in keys_to_delete:
            del self._nflreadpy_cache[key]
        
        if keys_to_delete:
            logger.info(
                f"Invalidated {len(keys_to_delete)} nflreadpy cache entries "
                f"for player: {player_name}"
            )
        
        return len(keys_to_delete)
    
    def invalidate_nflreadpy_season(self, season: int) -> int:
        """
        Invalidate all nflreadpy cache entries for a season.
        
        Args:
            season: Season year
            
        Returns:
            Number of entries invalidated
        """
        keys_to_delete = [
            key for key, entry in self._nflreadpy_cache.items()
            if entry.tags.get("season") == season
        ]
        
        for key in keys_to_delete:
            del self._nflreadpy_cache[key]
        
        if keys_to_delete:
            logger.info(
                f"Invalidated {len(keys_to_delete)} nflreadpy cache entries "
                f"for season: {season}"
            )
        
        return len(keys_to_delete)
    
    def clear_nflreadpy_cache(self):
        """Clear all nflreadpy cache entries."""
        count = len(self._nflreadpy_cache)
        self._nflreadpy_cache.clear()
        logger.info(f"nflreadpy cache cleared ({count} entries removed)")
    
    def cleanup_nflreadpy_expired(self) -> int:
        """
        Remove expired nflreadpy cache entries.
        
        Returns:
            Number of entries removed
        """
        keys_to_delete = [
            key for key, entry in self._nflreadpy_cache.items()
            if entry.is_expired()
        ]
        
        for key in keys_to_delete:
            del self._nflreadpy_cache[key]
        
        if keys_to_delete:
            logger.info(
                f"Cleaned up {len(keys_to_delete)} expired nflreadpy cache entries"
            )
        
        return len(keys_to_delete)
    
    # Query Results Cache Methods
    
    def _make_query_key(self, query_params: Dict[str, Any]) -> str:
        """
        Generate cache key for query results.
        
        Args:
            query_params: Query parameters dictionary
            
        Returns:
            Cache key string
        """
        # Create a stable hash of query parameters
        # Sort keys to ensure consistent hashing
        sorted_params = json.dumps(query_params, sort_keys=True)
        hash_obj = hashlib.md5(sorted_params.encode())
        return f"query:{hash_obj.hexdigest()}"
    
    def get_query_result(self, query_params: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """
        Get cached query result.
        
        Args:
            query_params: Query parameters
            
        Returns:
            Cached DataFrame or None if not cached or expired
        """
        key = self._make_query_key(query_params)
        result = self._query_cache.get(key)
        
        if result is not None:
            logger.debug(f"Query cache hit: {key[:16]}...")
        
        return result
    
    def set_query_result(
        self,
        query_params: Dict[str, Any],
        result: pd.DataFrame
    ):
        """
        Cache query result.
        
        Args:
            query_params: Query parameters
            result: Query result to cache
        """
        key = self._make_query_key(query_params)
        
        self._query_cache.set(
            key=key,
            value=result,
            ttl=self.query_cache_ttl,
            tags={
                "type": "query_result",
                "players": query_params.get("players", []),
                "season": query_params.get("season")
            }
        )
        
        logger.debug(
            f"Query result cached: {key[:16]}... "
            f"(records: {len(result)})"
        )
    
    def invalidate_query_cache_by_player(self, player_name: str) -> int:
        """
        Invalidate query cache entries containing a specific player.
        
        Args:
            player_name: Player name
            
        Returns:
            Number of entries invalidated
        """
        return self._query_cache.invalidate_by_tag("players", player_name)
    
    def clear_query_cache(self):
        """Clear all query cache entries."""
        self._query_cache.clear()
    
    # Global Cache Management Methods
    
    def clear_all(self):
        """Clear all caches."""
        logger.info("Clearing all caches")
        self.clear_kaggle_cache()
        self.clear_nflreadpy_cache()
        self.clear_query_cache()
    
    def cleanup_expired(self) -> Dict[str, int]:
        """
        Clean up all expired cache entries.
        
        Returns:
            Dictionary with counts of removed entries per cache
        """
        logger.info("Running cache cleanup")
        
        results = {
            "nflreadpy": self.cleanup_nflreadpy_expired(),
            "query": self._query_cache.cleanup_expired()
        }
        
        total = sum(results.values())
        logger.info(f"Cache cleanup complete: {total} total entries removed")
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics.
        
        Returns:
            Dictionary with statistics for all caches
        """
        # Count valid nflreadpy entries
        valid_nflreadpy = sum(
            1 for entry in self._nflreadpy_cache.values()
            if not entry.is_expired()
        )
        
        return {
            "kaggle": self.get_kaggle_cache_info(),
            "nflreadpy": {
                "total_entries": len(self._nflreadpy_cache),
                "valid_entries": valid_nflreadpy,
                "expired_entries": len(self._nflreadpy_cache) - valid_nflreadpy,
                "ttl_hours": self.nflreadpy_ttl.total_seconds() / 3600
            },
            "query": self._query_cache.get_stats()
        }


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """
    Get the global cache manager instance.
    
    Returns:
        Global CacheManager instance
    """
    global _cache_manager
    
    if _cache_manager is None:
        _cache_manager = CacheManager()
        logger.info("Global cache manager initialized")
    
    return _cache_manager


def initialize_cache_manager(
    kaggle_cache_enabled: bool = True,
    nflreadpy_ttl_hours: int = 24,
    query_cache_capacity: int = 100,
    query_cache_ttl_hours: int = 1
) -> CacheManager:
    """
    Initialize the global cache manager with custom settings.
    
    Args:
        kaggle_cache_enabled: Enable Kaggle dataset caching
        nflreadpy_ttl_hours: TTL for nflreadpy data
        query_cache_capacity: Query cache capacity
        query_cache_ttl_hours: TTL for query cache
        
    Returns:
        Initialized CacheManager instance
    """
    global _cache_manager
    
    _cache_manager = CacheManager(
        kaggle_cache_enabled=kaggle_cache_enabled,
        nflreadpy_ttl_hours=nflreadpy_ttl_hours,
        query_cache_capacity=query_cache_capacity,
        query_cache_ttl_hours=query_cache_ttl_hours
    )
    
    logger.info("Global cache manager initialized with custom settings")
    
    return _cache_manager
