"""
Test script for nflreadpy data fetching functionality.
"""

import logging
from data_sources.nflreadpy_source import NFLReadPyDataSource

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_nflreadpy_availability():
    """Test if nflreadpy is available."""
    print("\n=== Testing nflreadpy Availability ===")
    source = NFLReadPyDataSource()
    
    is_available = source.is_available()
    print(f"nflreadpy available: {is_available}")
    
    return source, is_available


def test_fetch_player_stats(source):
    """Test fetching player statistics."""
    print("\n=== Testing Player Stats Fetch ===")
    
    # Test with a well-known player
    test_players = [
        "Patrick Mahomes",
        "Travis Kelce",
        "Christian McCaffrey"
    ]
    
    for player_name in test_players:
        print(f"\nFetching stats for: {player_name}")
        try:
            stats = source.get_player_stats(
                player_name=player_name,
                season=2024
            )
            
            print(f"✓ Successfully fetched data")
            print(f"  Rows: {len(stats)}")
            print(f"  Columns: {list(stats.columns)}")
            
            if not stats.empty:
                print(f"\nSample data:")
                print(stats.head())
            
        except Exception as e:
            print(f"✗ Error: {e}")


def test_cache_functionality(source):
    """Test caching functionality."""
    print("\n=== Testing Cache Functionality ===")
    
    player_name = "Patrick Mahomes"
    
    # First fetch (should hit API)
    print(f"\nFirst fetch for {player_name}...")
    try:
        stats1 = source.get_player_stats(player_name, season=2024)
        print(f"✓ First fetch successful: {len(stats1)} rows")
    except Exception as e:
        print(f"✗ First fetch failed: {e}")
        return
    
    # Second fetch (should hit cache)
    print(f"\nSecond fetch for {player_name} (should use cache)...")
    try:
        stats2 = source.get_player_stats(player_name, season=2024)
        print(f"✓ Second fetch successful: {len(stats2)} rows")
    except Exception as e:
        print(f"✗ Second fetch failed: {e}")
    
    # Check cache stats
    cache_stats = source.get_cache_stats()
    print(f"\nCache stats: {cache_stats}")


def test_specific_stats(source):
    """Test fetching specific statistics."""
    print("\n=== Testing Specific Stats Fetch ===")
    
    player_name = "Patrick Mahomes"
    requested_stats = ["passing_yards", "passing_tds", "completions", "attempts"]
    
    print(f"\nFetching specific stats for {player_name}: {requested_stats}")
    try:
        stats = source.get_player_stats(
            player_name=player_name,
            season=2024,
            stats=requested_stats
        )
        
        print(f"✓ Successfully fetched specific stats")
        print(f"  Columns returned: {list(stats.columns)}")
        
        if not stats.empty:
            print(f"\nData:")
            print(stats)
        
    except Exception as e:
        print(f"✗ Error: {e}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("NFL ReadPy Data Source Test Suite")
    print("=" * 60)
    
    # Test availability
    source, is_available = test_nflreadpy_availability()
    
    if not is_available:
        print("\n⚠️  nflreadpy is not available. Install with:")
        print("   pip install nflreadpy")
        return
    
    # Run tests
    test_fetch_player_stats(source)
    test_cache_functionality(source)
    test_specific_stats(source)
    
    print("\n" + "=" * 60)
    print("Test suite completed")
    print("=" * 60)


if __name__ == "__main__":
    main()
