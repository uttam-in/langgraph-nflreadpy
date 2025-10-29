"""
Unit tests for the Memory Node.

Tests the conversation history management, entity extraction,
and context retrieval functionality.
"""

import unittest
from datetime import datetime

from nodes.memory import (
    update_memory,
    get_context,
    initialize_memory,
    clear_memory,
    extract_mentioned_players,
    extract_mentioned_stats,
    create_conversation_turn,
    get_memory_summary,
    MAX_CONVERSATION_HISTORY
)
from models.models import ChatbotState, ConversationTurn


class TestMemoryNode(unittest.TestCase):
    """Test cases for Memory Node functionality."""
    
    def test_initialize_memory(self):
        """Test that memory initializes as empty list."""
        history = initialize_memory()
        self.assertIsInstance(history, list)
        self.assertEqual(len(history), 0)
    
    def test_extract_mentioned_players(self):
        """Test player name extraction from text."""
        # Test with clear player name
        text = "How did Patrick Mahomes perform?"
        players = extract_mentioned_players(text)
        self.assertIn("Patrick Mahomes", players)
        
        # Test with parsed query
        parsed_query = {"players": ["Josh Allen", "Joe Burrow"]}
        players = extract_mentioned_players("Compare them", parsed_query)
        self.assertIn("Josh Allen", players)
        self.assertIn("Joe Burrow", players)
    
    def test_extract_mentioned_stats(self):
        """Test statistical category extraction from text."""
        # Test with common stat terms
        text = "What were his passing yards and touchdowns?"
        stats = extract_mentioned_stats(text)
        self.assertTrue(any('yards' in s for s in stats))
        self.assertTrue(any('touchdown' in s for s in stats))
        
        # Test with parsed query
        parsed_query = {"statistics": ["completion_rate", "interceptions"]}
        stats = extract_mentioned_stats("Show me the stats", parsed_query)
        self.assertIn("completion_rate", stats)
        self.assertIn("interceptions", stats)
    
    def test_create_conversation_turn(self):
        """Test creation of ConversationTurn object."""
        turn = create_conversation_turn(
            user_query="How did Patrick Mahomes perform in 2023?",
            bot_response="Patrick Mahomes had 4,183 passing yards.",
            parsed_query={"players": ["Patrick Mahomes"], "statistics": ["passing_yards"]}
        )
        
        self.assertIsInstance(turn, ConversationTurn)
        self.assertEqual(turn.user_query, "How did Patrick Mahomes perform in 2023?")
        self.assertIn("Patrick Mahomes", turn.mentioned_players)
        self.assertTrue(len(turn.mentioned_stats) > 0)
        self.assertIsInstance(turn.timestamp, datetime)
    
    def test_update_memory_single_turn(self):
        """Test updating memory with a single conversation turn."""
        state: ChatbotState = {
            "messages": [],
            "user_query": "How did Patrick Mahomes perform?",
            "parsed_query": {"players": ["Patrick Mahomes"], "statistics": ["passing_yards"]},
            "retrieved_data": None,
            "generated_response": "Patrick Mahomes had 4,183 passing yards.",
            "conversation_history": [],
            "error": None,
            "session_id": "test-session"
        }
        
        updated_state = update_memory(state)
        
        self.assertEqual(len(updated_state["conversation_history"]), 1)
        turn = updated_state["conversation_history"][0]
        self.assertEqual(turn["user_query"], "How did Patrick Mahomes perform?")
        self.assertIn("Patrick Mahomes", turn["mentioned_players"])
    
    def test_update_memory_max_history(self):
        """Test that memory maintains only last 10 turns."""
        state: ChatbotState = {
            "messages": [],
            "user_query": "",
            "parsed_query": {},
            "retrieved_data": None,
            "generated_response": "",
            "conversation_history": [],
            "error": None,
            "session_id": "test-session"
        }
        
        # Add 12 turns
        for i in range(12):
            state["user_query"] = f"Query {i+1}"
            state["generated_response"] = f"Response {i+1}"
            state["parsed_query"] = {"players": [f"Player{i+1}"], "statistics": ["yards"]}
            state = update_memory(state)
        
        # Should only keep last 10
        self.assertEqual(len(state["conversation_history"]), MAX_CONVERSATION_HISTORY)
        
        # First turn should be "Query 3" (turns 1-2 dropped)
        self.assertEqual(state["conversation_history"][0]["user_query"], "Query 3")
        
        # Last turn should be "Query 12"
        self.assertEqual(state["conversation_history"][-1]["user_query"], "Query 12")
    
    def test_get_context_empty_history(self):
        """Test getting context from empty history."""
        context = get_context([])
        
        self.assertEqual(len(context["recent_players"]), 0)
        self.assertEqual(len(context["recent_stats"]), 0)
        self.assertEqual(len(context["recent_queries"]), 0)
        self.assertIsNone(context["last_response"])
        self.assertEqual(context["turn_count"], 0)
    
    def test_get_context_with_history(self):
        """Test getting context from conversation history."""
        # Create some conversation history
        history = []
        for i in range(5):
            turn = ConversationTurn(
                user_query=f"Query about Player{i}",
                bot_response=f"Response about Player{i}",
                mentioned_players=[f"Player{i}"],
                mentioned_stats=["yards", "touchdowns"]
            )
            history.append(turn.to_dict())
        
        context = get_context(history, max_turns=3)
        
        # Should have players from last 3 turns
        self.assertTrue(len(context["recent_players"]) > 0)
        self.assertIn("Player4", context["recent_players"])  # Most recent
        
        # Should have stats
        self.assertTrue(len(context["recent_stats"]) > 0)
        
        # Should have last response
        self.assertIsNotNone(context["last_response"])
        self.assertIn("Player4", context["last_response"])
    
    def test_clear_memory(self):
        """Test clearing conversation history."""
        state: ChatbotState = {
            "messages": [],
            "user_query": "Test query",
            "parsed_query": {},
            "retrieved_data": None,
            "generated_response": "Test response",
            "conversation_history": [{"user_query": "Old query", "bot_response": "Old response"}],
            "error": None,
            "session_id": "test-session"
        }
        
        cleared_state = clear_memory(state)
        
        self.assertEqual(len(cleared_state["conversation_history"]), 0)
    
    def test_get_memory_summary_empty(self):
        """Test memory summary with empty history."""
        summary = get_memory_summary([])
        
        self.assertEqual(summary["turn_count"], 0)
        self.assertEqual(summary["total_players"], 0)
        self.assertEqual(summary["total_stats"], 0)
        self.assertEqual(len(summary["unique_players"]), 0)
        self.assertEqual(len(summary["unique_stats"]), 0)
    
    def test_get_memory_summary_with_data(self):
        """Test memory summary with conversation data."""
        history = []
        
        # Add turns with overlapping players
        turn1 = ConversationTurn(
            user_query="Query 1",
            bot_response="Response 1",
            mentioned_players=["Patrick Mahomes", "Josh Allen"],
            mentioned_stats=["passing_yards", "touchdowns"]
        )
        turn2 = ConversationTurn(
            user_query="Query 2",
            bot_response="Response 2",
            mentioned_players=["Patrick Mahomes"],  # Repeated player
            mentioned_stats=["completion_rate"]
        )
        
        history.append(turn1.to_dict())
        history.append(turn2.to_dict())
        
        summary = get_memory_summary(history)
        
        self.assertEqual(summary["turn_count"], 2)
        self.assertEqual(summary["total_players"], 3)  # 2 + 1
        self.assertEqual(len(summary["unique_players"]), 2)  # Patrick Mahomes, Josh Allen
        self.assertIn("Patrick Mahomes", summary["unique_players"])
        self.assertIn("Josh Allen", summary["unique_players"])
    
    def test_update_memory_skips_empty_query(self):
        """Test that memory update skips when query or response is empty."""
        state: ChatbotState = {
            "messages": [],
            "user_query": "",  # Empty query
            "parsed_query": {},
            "retrieved_data": None,
            "generated_response": "Some response",
            "conversation_history": [],
            "error": None,
            "session_id": "test-session"
        }
        
        updated_state = update_memory(state)
        
        # Should not add to history
        self.assertEqual(len(updated_state["conversation_history"]), 0)
    
    def test_context_deduplication(self):
        """Test that context removes duplicate players and stats."""
        history = []
        
        # Add multiple turns mentioning same player
        for i in range(3):
            turn = ConversationTurn(
                user_query=f"Query {i}",
                bot_response=f"Response {i}",
                mentioned_players=["Patrick Mahomes"],  # Same player each time
                mentioned_stats=["passing_yards"]  # Same stat each time
            )
            history.append(turn.to_dict())
        
        context = get_context(history)
        
        # Should only have one instance of each
        self.assertEqual(len(context["recent_players"]), 1)
        self.assertEqual(context["recent_players"][0], "Patrick Mahomes")
        self.assertEqual(len(context["recent_stats"]), 1)


if __name__ == "__main__":
    unittest.main()
