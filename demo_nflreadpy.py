"""
Quick demo script showcasing the NFL chatbot with nflreadpy data.

This script demonstrates the most impressive capabilities of the bot
with carefully selected queries that show off the live data integration.
"""

import os
from dotenv import load_dotenv
from workflow import run_workflow, configure_logging
import time

# Load environment
load_dotenv()
configure_logging("WARNING")  # Reduce log noise for demo

# Demo queries that showcase different capabilities
DEMO_QUERIES = [
    {
        "title": "Current Week Performance",
        "query": "What were Patrick Mahomes' passing yards in week 10 of 2024?",
        "highlight": "Shows live current season data"
    },
    {
        "title": "Season Overview",
        "query": "Show me Travis Kelce's receiving stats for the 2024 season",
        "highlight": "Aggregates full season statistics"
    },
    {
        "title": "Player Comparison",
        "query": "Compare Patrick Mahomes and Josh Allen passing yards in 2024",
        "highlight": "Compares multiple players side-by-side"
    },
    {
        "title": "Touchdown Analysis",
        "query": "How many touchdowns did Christian McCaffrey score in 2024?",
        "highlight": "Specific stat extraction"
    },
    {
        "title": "Wide Receiver Stats",
        "query": "What are Tyreek Hill's receiving yards this season?",
        "highlight": "Position-specific statistics"
    }
]


def print_header():
    """Print demo header."""
    print("\n" + "="*80)
    print("🏈 NFL CHATBOT DEMO - POWERED BY NFLREADPY")
    print("="*80)
    print("\nThis demo showcases live 2024 NFL statistics using nflreadpy.")
    print("Watch as the bot retrieves and analyzes current season data!\n")
    print("="*80 + "\n")


def print_query_demo(query_info: dict, index: int, total: int):
    """Print a single query demo."""
    print(f"\n{'─'*80}")
    print(f"DEMO {index}/{total}: {query_info['title']}")
    print(f"{'─'*80}")
    print(f"\n💡 {query_info['highlight']}\n")
    print(f"❓ Query: \"{query_info['query']}\"\n")
    print("⏳ Processing...\n")
    
    start_time = time.time()
    
    try:
        result = run_workflow(query_info['query'])
        elapsed = time.time() - start_time
        
        response = result.get("generated_response", "No response")
        retrieved_data = result.get("retrieved_data")
        
        print(f"✅ Response (in {elapsed:.2f}s):\n")
        print(f"{response}\n")
        
        if retrieved_data is not None and not retrieved_data.empty:
            print(f"📊 Data: {len(retrieved_data)} records retrieved")
            print(f"   Columns: {', '.join(list(retrieved_data.columns)[:8])}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False


def run_demo(pause_between: float = 2.0):
    """
    Run the full demo.
    
    Args:
        pause_between: Seconds to pause between queries
    """
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  ERROR: OPENAI_API_KEY not found!")
        print("Please set up your .env file with your OpenAI API key.\n")
        return
    
    print_header()
    
    total = len(DEMO_QUERIES)
    successful = 0
    
    for i, query_info in enumerate(DEMO_QUERIES, 1):
        if print_query_demo(query_info, i, total):
            successful += 1
        
        # Pause between queries (except after last one)
        if i < total:
            print(f"\n{'─'*80}")
            print(f"⏸️  Pausing {pause_between}s before next query...")
            print(f"{'─'*80}")
            time.sleep(pause_between)
    
    # Print summary
    print("\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80)
    print(f"\n✅ Successfully completed: {successful}/{total} queries")
    print(f"\n🎯 Key Features Demonstrated:")
    print("   • Live 2024 NFL season data")
    print("   • Week-by-week statistics")
    print("   • Season aggregations")
    print("   • Player comparisons")
    print("   • Multiple stat types (passing, rushing, receiving)")
    print("   • Fast response times with caching")
    print("\n💡 Try it yourself:")
    print("   python test_bot_with_nflreadpy.py interactive")
    print("   OR")
    print("   chainlit run app.py")
    print("\n" + "="*80 + "\n")


def quick_demo():
    """Run a quick 2-query demo."""
    print_header()
    print("🚀 QUICK DEMO (2 queries)\n")
    
    quick_queries = DEMO_QUERIES[:2]
    
    for i, query_info in enumerate(quick_queries, 1):
        print_query_demo(query_info, i, len(quick_queries))
        if i < len(quick_queries):
            time.sleep(1)
    
    print("\n" + "="*80)
    print("✅ Quick demo complete!")
    print("Run 'python demo_nflreadpy.py' for the full demo")
    print("="*80 + "\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_demo()
    else:
        run_demo(pause_between=2.0)
