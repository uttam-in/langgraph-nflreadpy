# Memory Node Usage Guide

The Memory Node maintains conversation context across multiple turns, enabling the chatbot to handle follow-up questions and resolve references to previously mentioned players and statistics.

## Core Functions

### `update_memory(state: ChatbotState) -> ChatbotState`

Updates the conversation history with the latest interaction. This should be called after each successful query-response cycle.

**Example:**
```python
from nodes.memory import update_memory

state = {
    "user_query": "How did Patrick Mahomes perform in 2023?",
    "generated_response": "Patrick Mahomes had 4,183 passing yards...",
    "parsed_query": {"players": ["Patrick Mahomes"], "statistics": ["passing_yards"]},
    "conversation_history": []
}

updated_state = update_memory(state)
# conversation_history now contains 1 turn
```

### `get_context(conversation_history: List[Dict], max_turns: int = 3) -> Dict`

Retrieves relevant context from recent conversation turns for query parsing and reference resolution.

**Example:**
```python
from nodes.memory import get_context

context = get_context(state["conversation_history"], max_turns=3)

# Context includes:
# - recent_players: ["Patrick Mahomes", "Josh Allen"]
# - recent_stats: ["passing_yards", "touchdowns"]
# - recent_queries: ["How did Patrick Mahomes perform?", ...]
# - last_response: "Josh Allen had 4,306 passing yards..."
```

### `initialize_memory() -> List`

Creates an empty conversation history for a new session.

**Example:**
```python
from nodes.memory import initialize_memory

# Start new session
conversation_history = initialize_memory()
```

### `clear_memory(state: ChatbotState) -> ChatbotState`

Clears the conversation history from the state.

**Example:**
```python
from nodes.memory import clear_memory

# User wants to start fresh
state = clear_memory(state)
```

## Integration with Query Parser

The Memory Node works seamlessly with the Query Parser to enable contextual queries:

```python
from nodes.memory import get_context, update_memory
from nodes.query_parser import parse_query

# First query
state = {
    "user_query": "How did Patrick Mahomes perform in 2023?",
    "conversation_history": []
}

# Parse and process...
state = parse_query(state)
# ... retrieve data, generate response ...
state["generated_response"] = "Patrick Mahomes had 4,183 passing yards..."

# Update memory
state = update_memory(state)

# Follow-up query with pronoun
state["user_query"] = "What about his touchdowns?"

# Get context for reference resolution
context = get_context(state["conversation_history"])
# context["recent_players"] = ["Patrick Mahomes"]

# Parse with context - Query Parser can resolve "his" to "Patrick Mahomes"
state = parse_query(state)
```

## Features

### Automatic Entity Extraction

The Memory Node automatically extracts:
- **Player names** from queries and responses
- **Statistical categories** mentioned in conversation
- **Timestamps** for each turn

### 10-Turn History Limit

The system maintains the last 10 conversation turns to:
- Keep context relevant and focused
- Manage memory efficiently
- Prevent context window overflow

### Deduplication

Context retrieval automatically deduplicates players and stats while preserving order, ensuring clean context for the Query Parser.

## Requirements Addressed

- **3.1**: Retrieves relevant conversation history for follow-up questions
- **3.2**: Maintains context for at least 10 conversational turns
- **3.3**: Provides context accessible to Query Parser Node
- **3.4**: Enables pronoun and reference resolution
- **3.5**: Initializes with empty context for new sessions

## Example Conversation Flow

```python
# Turn 1
state["user_query"] = "How did Patrick Mahomes perform in 2023?"
state = parse_query(state)
# ... process ...
state["generated_response"] = "Patrick Mahomes had 4,183 passing yards and 27 touchdowns."
state = update_memory(state)

# Turn 2 - Reference to same player
state["user_query"] = "What about his completion rate?"
context = get_context(state["conversation_history"])
# Query Parser uses context to resolve "his" -> "Patrick Mahomes"
state = parse_query(state)
# ... process ...
state["generated_response"] = "His completion rate was 67.2%."
state = update_memory(state)

# Turn 3 - Comparison with new player
state["user_query"] = "Compare him to Josh Allen"
context = get_context(state["conversation_history"])
# Query Parser uses context: "him" -> "Patrick Mahomes"
# Knows to compare same stats (completion rate, yards, touchdowns)
state = parse_query(state)
# ... process ...
state = update_memory(state)
```

## Testing

Comprehensive unit tests are available in `tests/test_memory.py` and integration tests in `tests/test_memory_integration.py`.

Run tests:
```bash
python3 -m unittest tests.test_memory -v
python3 -m unittest tests.test_memory_integration -v
```
