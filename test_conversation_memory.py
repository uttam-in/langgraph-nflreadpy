"""
Test script to verify conversation memory and follow-up question handling.

This script simulates a multi-turn conversation to ensure the chatbot
can remember context and handle follow-up questions correctly.
"""

import logging
from workflow import run_workflow, configure_logging

# Configure logging
configure_logging("INFO")
logger = logging.getLogger(__name__)


def test_conversation_flow():
    """Test a multi-turn conversation with follow-up questions."""
    
    print("\n" + "="*80)
    print("Testing Conversation Memory and Follow-up Questions")
    print("="*80 + "\n")
    
    # Initialize session state
    session_state = {
        "conversation_history": [],
        "session_id": "test_session_001"
    }
    
    # Test conversation flow
    test_queries = [
        "What were Patrick Mahomes' passing yards in week 10 of 2024?",
        "How many touchdowns did he throw?",
        "What about his completion rate?",
        "Compare him to Josh Allen in the same week",
        "Who had more yards?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"Turn {i}: {query}")
        print('='*80)
        
        # Run workflow with session state
        result = run_workflow(query, session_state)
        
        # Update session state with conversation history
        session_state["conversation_history"] = result.get("conversation_history", [])
        
        # Display results
        print(f"\nParsed Query:")
        parsed = result.get("parsed_query", {})
        print(f"  Players: {parsed.get('players', [])}")
        print(f"  Statistics: {parsed.get('statistics', [])}")
        print(f"  Time Period: {parsed.get('time_period', {})}")
        print(f"  Comparison: {parsed.get('comparison', False)}")
        
        print(f"\nResponse:")
        response = result.get("generated_response", "No response")
        # Truncate for readability
        if len(response) > 300:
            print(f"  {response[:300]}...")
        else:
            print(f"  {response}")
        
        if result.get("error"):
            print(f"\nError: {result['error']}")
        
        print(f"\nConversation History Size: {len(session_state['conversation_history'])} turns")
        
        # Show what's in memory
        if session_state['conversation_history']:
            last_turn = session_state['conversation_history'][-1]
            print(f"Last Turn Memory:")
            print(f"  - Players mentioned: {last_turn.get('mentioned_players', [])}")
            print(f"  - Stats mentioned: {last_turn.get('mentioned_stats', [])}")
    
    print("\n" + "="*80)
    print("Conversation Test Complete!")
    print("="*80 + "\n")
    
    # Summary
    print("Summary:")
    print(f"  Total turns: {len(session_state['conversation_history'])}")
    
    # Collect all mentioned entities
    all_players = set()
    all_stats = set()
    for turn in session_state['conversation_history']:
        all_players.update(turn.get('mentioned_players', []))
        all_stats.update(turn.get('mentioned_stats', []))
    
    print(f"  Unique players discussed: {', '.join(all_players)}")
    print(f"  Unique stats discussed: {', '.join(all_stats)}")


def test_pronoun_resolution():
    """Test pronoun and reference resolution."""
    
    print("\n" + "="*80)
    print("Testing Pronoun Resolution")
    print("="*80 + "\n")
    
    session_state = {
        "conversation_history": [],
        "session_id": "test_session_002"
    }
    
    test_cases = [
        ("Tell me about Travis Kelce's receiving yards in 2024", "Initial query"),
        ("How many touchdowns did he score?", "Pronoun 'he' should resolve to Travis Kelce"),
        ("What about his targets?", "Pronoun 'his' should resolve to Travis Kelce"),
        ("Compare him to George Kittle", "Pronoun 'him' should resolve to Travis Kelce"),
    ]
    
    for query, expected in test_cases:
        print(f"\nQuery: {query}")
        print(f"Expected: {expected}")
        
        result = run_workflow(query, session_state)
        session_state["conversation_history"] = result.get("conversation_history", [])
        
        parsed = result.get("parsed_query", {})
        print(f"Resolved Players: {parsed.get('players', [])}")
        print(f"Success: {'✓' if parsed.get('players') else '✗'}")


def test_context_continuation():
    """Test context continuation across multiple turns."""
    
    print("\n" + "="*80)
    print("Testing Context Continuation")
    print("="*80 + "\n")
    
    session_state = {
        "conversation_history": [],
        "session_id": "test_session_003"
    }
    
    queries = [
        "Show me Lamar Jackson's stats for week 15 of 2024",
        "What about week 16?",  # Should use same player
        "And week 17?",  # Should use same player
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        result = run_workflow(query, session_state)
        session_state["conversation_history"] = result.get("conversation_history", [])
        
        parsed = result.get("parsed_query", {})
        print(f"  Player: {parsed.get('players', [])}")
        print(f"  Week: {parsed.get('time_period', {}).get('specific_weeks', [])}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("NFL Chatbot - Conversation Memory Test Suite")
    print("="*80)
    
    try:
        # Run test suites
        test_conversation_flow()
        test_pronoun_resolution()
        test_context_continuation()
        
        print("\n" + "="*80)
        print("✓ All tests completed!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
