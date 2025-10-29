# Conversation Memory Feature

## Overview

The NFL Player Performance Chatbot now includes **conversation memory** that allows it to remember the context of your chat session and handle follow-up questions naturally.

## How It Works

### Memory Storage
- The chatbot maintains a rolling history of the **last 10 conversation turns**
- Each turn stores:
  - Your question
  - The bot's response
  - Players mentioned
  - Statistics discussed
  - Timestamp

### Context Resolution
The chatbot can now understand follow-up questions that reference previous context:

#### Pronouns
- **"he", "his", "him"** → Resolves to the last mentioned player
- **"they", "them", "their"** → Resolves to previously mentioned players

#### Implicit References
- **"What about his rushing yards?"** → Uses the player from the previous question
- **"How many touchdowns?"** → Infers the player and context from history
- **"In week 10?"** → Applies to the same player(s) from the previous query
- **"Compare them"** → Compares players mentioned in recent conversation

#### Continuation Phrases
- **"And him?"** → Adds another player to the comparison
- **"What about..."** → Continues the same topic with a variation
- **"How about..."** → Similar to "what about"

## Example Conversations

### Example 1: Basic Follow-up
```
You: What were Patrick Mahomes' passing yards in week 10 of 2024?
Bot: Patrick Mahomes threw for 320 yards in week 10 of the 2024 season...

You: How many touchdowns did he throw?
Bot: In week 10 of 2024, Patrick Mahomes threw 3 touchdowns...
     [Bot remembers "he" = Patrick Mahomes and week 10]
```

### Example 2: Stat Continuation
```
You: Show me Travis Kelce's receiving stats for 2024
Bot: Travis Kelce had 984 receiving yards with 93 receptions...

You: What about his touchdowns?
Bot: Travis Kelce scored 5 receiving touchdowns in the 2024 season...
     [Bot remembers "his" = Travis Kelce and 2024 season]
```

### Example 3: Player Comparison
```
You: Compare Patrick Mahomes and Josh Allen in 2024
Bot: Patrick Mahomes: 4,183 passing yards, Josh Allen: 3,731 yards...

You: Who had more touchdowns?
Bot: Patrick Mahomes led with 27 touchdowns compared to Josh Allen's 18...
     [Bot remembers both players and continues the comparison]
```

### Example 4: Week Progression
```
You: How did Lamar Jackson perform in week 15?
Bot: In week 15, Lamar Jackson had 252 passing yards and 2 touchdowns...

You: What about week 16?
Bot: In week 16, Lamar Jackson improved to 316 passing yards and 3 touchdowns...
     [Bot remembers the player and increments the week]

You: And week 17?
Bot: In week 17, Lamar Jackson had 289 passing yards and 2 touchdowns...
```

## Visual Indicators

When the chatbot is using conversation context, you'll see:
- **"🔍 Analyzing your question (using conversation context)..."** during processing

## Memory Limits

- **Maximum history**: 10 conversation turns
- **Context window**: Last 5 turns are used for generating responses
- **Reference resolution**: Last 3 turns are checked for player/stat references

## Session Management

### New Session
- Each time you start the chatbot, a new session begins with empty memory
- The welcome message indicates a fresh start

### Memory Persistence
- Memory persists throughout your active chat session
- Closing the browser or refreshing the page starts a new session

### Clearing Memory
- Currently, memory is automatically cleared when you start a new session
- Future versions may include a "clear context" command

## Technical Details

### Memory Node
The Memory Node (`nodes/memory.py`) handles:
- Extracting entities (players, stats) from each conversation turn
- Maintaining the rolling window of conversation history
- Providing context to other nodes for reference resolution

### Query Parser Integration
The Query Parser (`nodes/query_parser.py`) uses memory to:
- Resolve pronouns and implicit references
- Fill in missing information from context
- Determine if a query is a follow-up question

### LLM Integration
The LLM Node (`nodes/llm_node.py`) uses memory to:
- Maintain conversational continuity
- Reference previous answers when relevant
- Build upon earlier discussions

## Best Practices

### For Best Results
1. **Be natural**: Ask follow-up questions as you would in a normal conversation
2. **Use pronouns**: Feel free to say "he", "his", "them" - the bot will understand
3. **Build on topics**: Continue discussing the same player or stat across multiple questions
4. **Compare naturally**: Say "compare them" or "who had more" without repeating names

### When to Be Explicit
- When switching to a completely different topic
- When asking about a new player after discussing multiple players
- When the context might be ambiguous

## Troubleshooting

### Bot doesn't understand a reference
- Try being more explicit in your next question
- Rephrase using the full player name
- The bot will ask for clarification if truly ambiguous

### Wrong player referenced
- This can happen if multiple players were recently discussed
- Use the full name to reset the context
- The bot prioritizes the most recently mentioned player

### Memory seems lost
- Check if you refreshed the page (starts new session)
- Verify the bot's response mentions using context
- After 10 turns, oldest conversations are removed

## Future Enhancements

Planned improvements:
- Manual memory clearing command
- Ability to reference specific past turns ("like you said earlier")
- Cross-session memory for returning users
- Smarter disambiguation when multiple players are in context
- Memory summary command to see what the bot remembers
