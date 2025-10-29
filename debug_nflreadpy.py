"""
Debug script to explore nflreadpy data structure.
"""

import nflreadpy as nfl

# Load player stats for 2024
print("Loading player stats for 2024...")
df = nfl.load_player_stats(seasons=2024)

# Convert to pandas
df_pandas = df.to_pandas()

print(f"\nDataFrame shape: {df_pandas.shape}")
print(f"\nColumns: {list(df_pandas.columns)}")
print(f"\nFirst few rows:")
print(df_pandas.head())

# Check for player name columns
print("\n\nLooking for player name columns...")
name_cols = [col for col in df_pandas.columns if 'player' in col.lower() or 'name' in col.lower()]
print(f"Name-related columns: {name_cols}")

if name_cols:
    print(f"\nSample values from '{name_cols[0]}':")
    print(df_pandas[name_cols[0]].head(20))

# Check unique players
if 'player_display_name' in df_pandas.columns:
    print(f"\nTotal unique players: {df_pandas['player_display_name'].nunique()}")
    print("\nSample player names:")
    print(df_pandas['player_display_name'].unique()[:20])
