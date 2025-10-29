"""
Data models for the NFL Player Performance Chatbot.

This module defines the core data structures used throughout the application:
- PlayerStats: Represents NFL player statistics
- ConversationTurn: Tracks individual conversation exchanges
- ChatbotState: LangGraph state for workflow orchestration
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

import pandas as pd
from langchain_core.messages import BaseMessage


@dataclass
class PlayerStats:
    """
    Represents NFL player statistics for a given time period.
    
    Supports multiple positions with comprehensive statistical categories
    including passing, receiving, rushing, and advanced metrics.
    """
    player_name: str
    team: str
    position: str
    season: int
    week: Optional[int] = None
    
    # Passing stats
    completions: Optional[int] = None
    attempts: Optional[int] = None
    passing_yards: Optional[int] = None
    passing_touchdowns: Optional[int] = None
    interceptions: Optional[int] = None
    sacks: Optional[int] = None
    sack_yards: Optional[int] = None
    
    # Rushing stats
    rushing_attempts: Optional[int] = None
    rushing_yards: Optional[int] = None
    rushing_touchdowns: Optional[int] = None
    
    # Receiving stats
    targets: Optional[int] = None
    receptions: Optional[int] = None
    receiving_yards: Optional[int] = None
    receiving_touchdowns: Optional[int] = None
    
    # Advanced metrics
    epa: Optional[float] = None  # Expected Points Added
    completion_rate: Optional[float] = None
    yards_per_attempt: Optional[float] = None
    yards_per_reception: Optional[float] = None
    yards_per_carry: Optional[float] = None
    
    # Additional context
    games_played: Optional[int] = None
    
    def __post_init__(self):
        """Calculate derived statistics if base stats are available."""
        if self.completions is not None and self.attempts is not None and self.attempts > 0:
            if self.completion_rate is None:
                self.completion_rate = round((self.completions / self.attempts) * 100, 2)
        
        if self.passing_yards is not None and self.attempts is not None and self.attempts > 0:
            if self.yards_per_attempt is None:
                self.yards_per_attempt = round(self.passing_yards / self.attempts, 2)
        
        if self.receiving_yards is not None and self.receptions is not None and self.receptions > 0:
            if self.yards_per_reception is None:
                self.yards_per_reception = round(self.receiving_yards / self.receptions, 2)
        
        if self.rushing_yards is not None and self.rushing_attempts is not None and self.rushing_attempts > 0:
            if self.yards_per_carry is None:
                self.yards_per_carry = round(self.rushing_yards / self.rushing_attempts, 2)


@dataclass
class ConversationTurn:
    """
    Represents a single turn in the conversation between user and chatbot.
    
    Tracks the query, response, and extracted entities for context maintenance
    and reference resolution in follow-up queries.
    """
    user_query: str
    bot_response: str
    mentioned_players: List[str] = field(default_factory=list)
    mentioned_stats: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation turn to dictionary format."""
        return {
            'user_query': self.user_query,
            'bot_response': self.bot_response,
            'mentioned_players': self.mentioned_players,
            'mentioned_stats': self.mentioned_stats,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationTurn':
        """Create ConversationTurn from dictionary."""
        data_copy = data.copy()
        if 'timestamp' in data_copy and isinstance(data_copy['timestamp'], str):
            data_copy['timestamp'] = datetime.fromisoformat(data_copy['timestamp'])
        return cls(**data_copy)


class ChatbotState(TypedDict):
    """
    LangGraph state object that flows through the workflow nodes.
    
    This TypedDict defines the shared state structure used by all nodes
    in the LangGraph workflow for processing user queries and generating responses.
    """
    # LangChain messages for LLM interactions
    messages: List[BaseMessage]
    
    # Current user query being processed
    user_query: str
    
    # Parsed query structure from Query Parser Node
    parsed_query: Dict[str, Any]
    
    # Retrieved data from Retriever Node
    retrieved_data: Optional[pd.DataFrame]
    
    # Generated response from LLM Node
    generated_response: str
    
    # Conversation history from Memory Node (last 10 turns)
    conversation_history: List[Dict[str, Any]]
    
    # Error information if any node fails
    error: Optional[str]
    
    # Session identifier for tracking
    session_id: Optional[str]
