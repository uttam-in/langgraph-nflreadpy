"""
Test script to demonstrate the NFL chatbot using nflreadpy data source.

This script runs sample queries through the complete workflow to show
how the bot retrieves and presents current season NFL statistics.
"""

import logging
import os
from dotenv import load_dotenv
from workflow import run_workflow, configure_logging

# Load environment variables
load_dotenv()

# Configure logging
configure_logging("INFO")
logger = logging.getLogger(__name__)


# Sample queries that showcase nflreadpy data
SAMPLE_QUERIES = [
    # Current season queries
    "What were Patrick Mahomes' passing yards in week 10 of 2024?",
    "Show me Travis Kelce's receiving stats for the 2024 season",
    "How many touchdowns did Christian McCaffrey score in 2024?",
    "Compare Patrick Mahomes and Josh Allen passing yards in 2024",
    "What are Tyreek Hill's receiving yards this season?",
    
    # Recent performance
    "How did Lamar Jackson perform in week 15?",
    "Show me CeeDee Lamb's targets in the last game",
    
    # Team-based queries
    "How are the Chiefs quarterbacks performing this season?",
    
    # Statistical comparisons
    "Who has more passing touchdowns, Dak Prescott or Jalen Hurts in 2024?",
    "Compare the rushing yards of Derrick Henry and Josh Jacobs this season",
]


def print_separator(char="=", length=80):
    """Print a separator line."""
    print(char * length)


def print_query_result(query: str, result: dict, query_num: int, total: int):
    """
    Print formatted query result.
    
    Args:
        query: The user query
        result: The workflow result dictionary
        query_num: Current query number
        total: Total number of queries
    """
    print_separator()
    print(f"QUERY {query_num}/{total}")
    print_separator()
    print(f"\n📝 Question: {query}\n")
    
    # Check for errors
    if result.get("error"):
        print(f"⚠️  Error: {result['error']}\n")
    
    # Print response
    response = result.get("generated_response", "No response generated")
    print(f"🤖 Response:\n{response}\n")
    
    # Print data summary if available
    retrieved_data = result.get("retrieved_data")
    if retrieved_data is not None and not retrieved_data.empty:
        print(f"📊 Data Retrieved: {len(retrieved_data)} records")
        print(f"   Columns: {', '.join(retrieved_data.columns[:10])}{'...' if len(retrieved_data.columns) > 10 else ''}")
    
    print()


def run_sample_queries(queries: list, max_queries: int = None):
    """
    Run a list of sample queries through the workflow.
    
    Args:
        queries: List of query strings
        max_queries: Maximum number of queries to run (None for all)
    """
    if max_queries:
        queries = queries[:max_queries]
    
    total = len(queries)
    
    print_separator("=")
    print("🏈 NFL CHATBOT - NFLREADPY DATA SOURCE TEST")
    print_separator("=")
    print(f"\nRunning {total} sample queries...\n")
    
    results = []
    
    for i, query in enumerate(queries, 1):
        try:
            result = run_workflow(query)
            results.append({
                "query": query,
                "result": result,
                "success": result.get("error") is None
            })
            
            print_query_result(query, result, i, total)
            
        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            print(f"❌ Query failed: {e}\n")
            results.append({
                "query": query,
                "result": None,
                "success": False
            })
    
    # Print summary
    print_separator("=")
    print("SUMMARY")
    print_separator("=")
    
    successful = sum(1 for r in results if r["success"])
    failed = total - successful
    
    print(f"\n✅ Successful: {successful}/{total}")
    print(f"❌ Failed: {failed}/{total}")
    
    if failed > 0:
        print("\nFailed queries:")
        for r in results:
            if not r["success"]:
                print(f"  - {r['query']}")
    
    print_separator("=")


def run_interactive_mode():
    """
    Run the bot in interactive mode for manual testing.
    """
    print_separator("=")
    print("🏈 NFL CHATBOT - INTERACTIVE MODE")
    print_separator("=")
    print("\nAsk questions about NFL player statistics!")
    print("Type 'quit' or 'exit' to stop.\n")
    print("Example queries:")
    for query in SAMPLE_QUERIES[:3]:
        print(f"  - {query}")
    print()
    
    session_state = {"conversation_history": []}
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("\n🔄 Processing...\n")
            
            result = run_workflow(user_input, session_state)
            
            # Update session state
            session_state["conversation_history"] = result.get("conversation_history", [])
            
            # Print response
            response = result.get("generated_response", "No response generated")
            print(f"Bot: {response}\n")
            
            # Show data summary
            retrieved_data = result.get("retrieved_data")
            if retrieved_data is not None and not retrieved_data.empty:
                print(f"📊 Retrieved {len(retrieved_data)} records\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"\n❌ Error: {e}\n")


def main():
    """Main entry point."""
    import sys
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  ERROR: OPENAI_API_KEY not found!")
        print("Please set up your .env file with your OpenAI API key.\n")
        return
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "interactive":
            run_interactive_mode()
        elif sys.argv[1] == "quick":
            # Run just 3 queries for quick testing
            run_sample_queries(SAMPLE_QUERIES, max_queries=3)
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Usage: python test_bot_with_nflreadpy.py [interactive|quick]")
    else:
        # Run all sample queries
        run_sample_queries(SAMPLE_QUERIES)


if __name__ == "__main__":
    main()
