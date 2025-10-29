"""
Memory Node for NFL Player Performance Chatbot.

This module implements the Memory Node that maintains conversation context
across multiple turns, enabling reference resolution and contextual queries.

Requirements addressed:
- 3.1: Retrieve relevant conversation history for follow-up questions
- 3.2: Maintain context for at least the previous 10 conversational turns
- 3.3: Access conversation context from Memory Node during query parsing
- 3.4: Resolve pronouns and references using conversation history
- 3.5: Initialize with empty context for new sessions
"""

import logging
import re
from typing import Any, Dict, List, Optional
from datetime import datetime

from models.models import ChatbotState, ConversationTurn

logger = logging.getLogger(__name__)

# Maximum number of conversation turns to maintain
MAX_CONVERSATION_HISTORY = 10


def extract_mentioned_players(text: str, parsed_query: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Extract player names mentioned in text.
    
    Args:
        text: Text to extract player names from (query or response)
        parsed_query: Optional parsed query with extracted player names
        
    Returns:
        List of player names mentioned
    """
    players = []
    
    # First, use parsed query if available (most reliable)
    if parsed_query and 'players' in parsed_query:
        players.extend(parsed_query['players'])
    
    # Common NFL player name patterns (First Last or First Middle Last)
    # This is a simple heuristic - in production, you'd use NER or a player database
    name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b'
    potential_names = re.findall(name_pattern, text)
    
    # Filter out common false positives
    false_positives = {
        'The System', 'The Player', 'The Team', 'The Game',
        'Expected Points', 'Points Added', 'Red Zone', 'The Season',
        'The Week', 'The League', 'The NFL', 'The Stats'
    }
    
    for name in potential_names:
        if name not in false_positives and name not in players:
            # Basic validation: at least 2 words, each starting with capital
            words = name.split()
            if len(words) >= 2 and all(w[0].isupper() for w in words):
                players.append(name)
    
    return players


def extract_mentioned_stats(text: str, parsed_query: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Extract statistical categories mentioned in text.
    
    Args:
        text: Text to extract statistics from
        parsed_query: Optional parsed query with extracted statistics
        
    Returns:
        List of statistical categories mentioned
    """
    stats = []
    
    # First, use parsed query if available (most reliable)
    if parsed_query and 'statistics' in parsed_query:
        stats.extend(parsed_query['statistics'])
    
    # Common statistical terms to look for
    stat_keywords = {
        'yards': 'yards',
        'passing yards': 'passing_yards',
        'rushing yards': 'rushing_yards',
        'receiving yards': 'receiving_yards',
        'touchdowns': 'touchdowns',
        'tds': 'touchdowns',
        'completions': 'completions',
        'attempts': 'attempts',
        'completion rate': 'completion_rate',
        'completion percentage': 'completion_rate',
        'interceptions': 'interceptions',
        'picks': 'interceptions',
        'receptions': 'receptions',
        'catches': 'receptions',
        'targets': 'targets',
        'epa': 'epa',
        'expected points': 'epa',
        'yards per attempt': 'yards_per_attempt',
        'yards per reception': 'yards_per_reception',
        'yards per carry': 'yards_per_carry',
        'sacks': 'sacks',
    }
    
    text_lower = text.lower()
    
    for keyword, stat_name in stat_keywords.items():
        if keyword in text_lower and stat_name not in stats:
            stats.append(stat_name)
    
    return stats


def create_conversation_turn(
    user_query: str,
    bot_response: str,
    parsed_query: Optional[Dict[str, Any]] = None
) -> ConversationTurn:
    """
    Create a ConversationTurn object from a query-response pair.
    
    Args:
        user_query: The user's query
        bot_response: The bot's response
        parsed_query: Optional parsed query for better entity extraction
        
    Returns:
        ConversationTurn object with extracted entities
    """
    # Extract mentioned players and stats
    mentioned_players = extract_mentioned_players(user_query, parsed_query)
    mentioned_stats = extract_mentioned_stats(user_query, parsed_query)
    
    # Also check the response for additional context
    response_players = extract_mentioned_players(bot_response)
    response_stats = extract_mentioned_stats(bot_response)
    
    # Combine and deduplicate
    all_players = list(dict.fromkeys(mentioned_players + response_players))
    all_stats = list(dict.fromkeys(mentioned_stats + response_stats))
    
    return ConversationTurn(
        user_query=user_query,
        bot_response=bot_response,
        mentioned_players=all_players,
        mentioned_stats=all_stats,
        timestamp=datetime.now()
    )


def update_memory(state: ChatbotState) -> ChatbotState:
    """
    Update conversation history with the latest interaction.
    
    This is the main entry point for the Memory Node in the LangGraph workflow.
    Stores the current query-response pair and maintains a rolling window of
    the last 10 conversation turns.
    
    Args:
        state: Current chatbot state with user_query and generated_response
        
    Returns:
        Updated state with conversation_history updated
        
    Requirements:
        - 3.1: Stores conversation for retrieval in follow-up questions
        - 3.2: Maintains last 10 conversational turns
        - 3.3: Makes context accessible to Query Parser Node
        - 3.4: Extracts entities for reference resolution
    """
    try:
        user_query = state.get("user_query", "")
        generated_response = state.get("generated_response", "")
        parsed_query = state.get("parsed_query")
        conversation_history = state.get("conversation_history", [])
        
        # Skip if no query or response
        if not user_query or not generated_response:
            logger.warning("Skipping memory update: missing query or response")
            return state
        
        # Create conversation turn
        turn = create_conversation_turn(
            user_query=user_query,
            bot_response=generated_response,
            parsed_query=parsed_query
        )
        
        # Convert to dictionary for storage
        turn_dict = turn.to_dict()
        
        # Add to conversation history
        conversation_history.append(turn_dict)
        
        # Maintain maximum history size (last 10 turns)
        if len(conversation_history) > MAX_CONVERSATION_HISTORY:
            conversation_history = conversation_history[-MAX_CONVERSATION_HISTORY:]
        
        # Update state
        state["conversation_history"] = conversation_history
        
        logger.info(
            f"Memory updated: {len(conversation_history)} turns in history, "
            f"extracted {len(turn.mentioned_players)} players and {len(turn.mentioned_stats)} stats"
        )
        
        return state
        
    except Exception as e:
        logger.error(f"Error in update_memory: {e}")
        # Don't fail the workflow for memory errors
        # Just log and return state unchanged
        return state


def get_context(conversation_history: List[Dict[str, Any]], max_turns: int = 3) -> Dict[str, Any]:
    """
    Retrieve relevant context from conversation history for query parsing.
    
    This function extracts the most recent context to help resolve references
    and pronouns in follow-up queries.
    
    Args:
        conversation_history: List of conversation turn dictionaries
        max_turns: Maximum number of recent turns to consider (default: 3)
        
    Returns:
        Dictionary with aggregated context including:
        - recent_players: List of recently mentioned player names
        - recent_stats: List of recently mentioned statistics
        - recent_queries: List of recent user queries
        - last_response: The most recent bot response
        
    Requirements:
        - 3.1: Provides relevant history for follow-up questions
        - 3.3: Enables Query Parser to access conversation context
        - 3.4: Supports pronoun and reference resolution
    """
    context = {
        "recent_players": [],
        "recent_stats": [],
        "recent_queries": [],
        "last_response": None,
        "turn_count": len(conversation_history)
    }
    
    if not conversation_history:
        return context
    
    # Get the most recent turns
    recent_turns = conversation_history[-max_turns:] if len(conversation_history) >= max_turns else conversation_history
    
    # Extract entities from recent turns
    for turn in recent_turns:
        # Add mentioned players
        if "mentioned_players" in turn:
            context["recent_players"].extend(turn["mentioned_players"])
        
        # Add mentioned stats
        if "mentioned_stats" in turn:
            context["recent_stats"].extend(turn["mentioned_stats"])
        
        # Add user queries
        if "user_query" in turn:
            context["recent_queries"].append(turn["user_query"])
    
    # Remove duplicates while preserving order
    context["recent_players"] = list(dict.fromkeys(context["recent_players"]))
    context["recent_stats"] = list(dict.fromkeys(context["recent_stats"]))
    
    # Get the last response for immediate context
    if conversation_history:
        last_turn = conversation_history[-1]
        context["last_response"] = last_turn.get("bot_response")
    
    return context


def initialize_memory() -> List[Dict[str, Any]]:
    """
    Initialize an empty conversation history for a new session.
    
    Returns:
        Empty list representing a new conversation history
        
    Requirements:
        - 3.5: Initialize with empty context for new sessions
    """
    logger.info("Initializing new conversation memory")
    return []


def clear_memory(state: ChatbotState) -> ChatbotState:
    """
    Clear conversation history from the state.
    
    This can be used for session cleanup or when the user wants to start fresh.
    
    Args:
        state: Current chatbot state
        
    Returns:
        State with cleared conversation_history
        
    Requirements:
        - 3.5: Supports session cleanup
    """
    state["conversation_history"] = initialize_memory()
    logger.info("Conversation memory cleared")
    return state


def get_memory_summary(conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a summary of the conversation history.
    
    Useful for debugging and monitoring conversation state.
    
    Args:
        conversation_history: List of conversation turn dictionaries
        
    Returns:
        Dictionary with summary statistics
    """
    if not conversation_history:
        return {
            "turn_count": 0,
            "total_players": 0,
            "total_stats": 0,
            "unique_players": [],
            "unique_stats": []
        }
    
    all_players = []
    all_stats = []
    
    for turn in conversation_history:
        if "mentioned_players" in turn:
            all_players.extend(turn["mentioned_players"])
        if "mentioned_stats" in turn:
            all_stats.extend(turn["mentioned_stats"])
    
    unique_players = list(dict.fromkeys(all_players))
    unique_stats = list(dict.fromkeys(all_stats))
    
    return {
        "turn_count": len(conversation_history),
        "total_players": len(all_players),
        "total_stats": len(all_stats),
        "unique_players": unique_players,
        "unique_stats": unique_stats,
        "oldest_turn": conversation_history[0].get("timestamp") if conversation_history else None,
        "newest_turn": conversation_history[-1].get("timestamp") if conversation_history else None
    }


# Synchronous version for non-async contexts
def update_memory_sync(state: ChatbotState) -> ChatbotState:
    """
    Synchronous version of update_memory for compatibility.
    
    Args:
        state: Current chatbot state
        
    Returns:
        Updated state with conversation history
    """
    return update_memory(state)
