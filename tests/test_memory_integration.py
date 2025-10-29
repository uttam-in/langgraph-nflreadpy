"""
Integration test demonstrating Memory Node working with Query Parser.

This test shows how conversation context enables reference resolution
in follow-up queries.
"""

import unittest
from nodes.memory import update_memory, get_context, initialize_memory
from models.models import ChatbotState


class TestMemoryIntegration(unittest.TestCase):
    """Integration tests for Memory Node with other components."""
    
    def test_memory_enables_reference_resolution(self):
        """
        Test that memory provides context for resolving references in follow-up queries.
        
        Scenario:
        1. User asks: "How did Patrick Mahomes perform in 2023?"
        2. Bot responds with stats
        3. User asks: "What about Josh Allen?" (reference to same question type)
        4. Memory should provide context about previous query
        """
        # First interaction
        state: ChatbotState = {
            "messages": [],
            "user_query": "How did Patrick Mahomes perform in 2023?",
            "parsed_query": {
                "players": ["Patrick Mahomes"],
                "statistics": ["passing_yards", "touchdowns"],
                "time_period": {"season": 2023}
            },
            "retrieved_data": None,
            "generated_response": "Patrick Mahomes had 4,183 passing yards and 27 touchdowns in 2023.",
            "conversation_history": [],
            "error": None,
            "session_id": "test-session"
        }
        
        # Update memory with first interaction
        state = update_memory(state)
        
        # Verify memory was updated
        self.assertEqual(len(state["conversation_history"]), 1)
        
        # Get context for next query
        context = get_context(state["conversation_history"])
        
        # Context should include Patrick Mahomes
        self.assertIn("Patrick Mahomes", context["recent_players"])
        
        # Context should include the stats that were queried
        self.assertTrue(any('yards' in s for s in context["recent_stats"]))
        
        # Second interaction (follow-up)
        state["user_query"] = "What about Josh Allen?"
        state["parsed_query"] = {
            "players": ["Josh Allen"],
            "statistics": ["passing_yards", "touchdowns"],  # Same stats inferred from context
            "time_period": {"season": 2023}  # Same time period inferred from context
        }
        state["generated_response"] = "Josh Allen had 4,306 passing yards and 29 touchdowns in 2023."
        
        # Update memory with second interaction
        state = update_memory(state)
        
        # Verify both interactions are in memory
        self.assertEqual(len(state["conversation_history"]), 2)
        
        # Get updated context
        context = get_context(state["conversation_history"])
        
        # Context should now include both players
        self.assertIn("Patrick Mahomes", context["recent_players"])
        self.assertIn("Josh Allen", context["recent_players"])
        
        # Last response should be about Josh Allen
        self.assertIn("Josh Allen", context["last_response"])
    
    def test_pronoun_resolution_context(self):
        """
        Test that memory provides context for pronoun resolution.
        
        Scenario:
        1. User asks: "How did Patrick Mahomes perform?"
        2. User asks: "What about his completion rate?" (pronoun "his")
        3. Memory should provide Patrick Mahomes as context
        """
        state: ChatbotState = {
            "messages": [],
            "user_query": "How did Patrick Mahomes perform in 2023?",
            "parsed_query": {
                "players": ["Patrick Mahomes"],
                "statistics": ["passing_yards"]
            },
            "retrieved_data": None,
            "generated_response": "Patrick Mahomes had 4,183 passing yards in 2023.",
            "conversation_history": [],
            "error": None,
            "session_id": "test-session"
        }
        
        # First interaction
        state = update_memory(state)
        
        # Get context for pronoun resolution
        context = get_context(state["conversation_history"])
        
        # When user asks "What about his completion rate?", 
        # the Query Parser can use context to resolve "his" to "Patrick Mahomes"
        self.assertIn("Patrick Mahomes", context["recent_players"])
        self.assertEqual(len(context["recent_players"]), 1)
        
        # The most recent player is Patrick Mahomes
        most_recent_player = context["recent_players"][-1]
        self.assertEqual(most_recent_player, "Patrick Mahomes")
    
    def test_multi_turn_context_window(self):
        """
        Test that context window focuses on recent turns.
        
        Verifies that get_context returns only the most recent turns
        for efficient context resolution.
        """
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
        
        # Add 5 turns with different players
        players = ["Player1", "Player2", "Player3", "Player4", "Player5"]
        for i, player in enumerate(players):
            state["user_query"] = f"How did {player} perform?"
            state["parsed_query"] = {"players": [player], "statistics": ["yards"]}
            state["generated_response"] = f"{player} had great stats."
            state = update_memory(state)
        
        # Get context with max_turns=3
        context = get_context(state["conversation_history"], max_turns=3)
        
        # Should only include last 3 players
        self.assertIn("Player3", context["recent_players"])
        self.assertIn("Player4", context["recent_players"])
        self.assertIn("Player5", context["recent_players"])
        
        # Should not include first 2 players
        self.assertNotIn("Player1", context["recent_players"])
        self.assertNotIn("Player2", context["recent_players"])
    
    def test_session_initialization(self):
        """
        Test that new sessions start with empty memory.
        
        Verifies Requirement 3.5: Initialize with empty context for new sessions.
        """
        # Initialize new session
        history = initialize_memory()
        
        # Should be empty
        self.assertEqual(len(history), 0)
        
        # Get context from empty history
        context = get_context(history)
        
        # All context fields should be empty
        self.assertEqual(len(context["recent_players"]), 0)
        self.assertEqual(len(context["recent_stats"]), 0)
        self.assertEqual(len(context["recent_queries"]), 0)
        self.assertIsNone(context["last_response"])


if __name__ == "__main__":
    unittest.main()
