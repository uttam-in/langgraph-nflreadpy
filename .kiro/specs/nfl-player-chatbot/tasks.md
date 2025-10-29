# Implementation Plan

- [x] 1. Set up project structure and dependencies
  - Create project directory structure with folders for nodes, data sources, models, and tests
  - Create requirements.txt with all necessary dependencies (chainlit, langgraph, pandas, nflreadpy, openai, python-dotenv)
  - Create .env.example file for environment variable configuration
  - Create main app.py file as Chainlit entry point
  - Note: Use nflreadpy (Python package)
  - _Requirements: 8.1, 8.2_

- [x] 2. Implement data models and state definitions
  - Create models.py with PlayerStats dataclass including all statistical fields
  - Create ConversationTurn dataclass for conversation history tracking
  - Create ChatbotState TypedDict for LangGraph state management with all required fields
  - _Requirements: 3.2, 3.5_

- [x] 3. Implement data layer foundation
  - Create abstract DataSource base class with get_player_stats method
  - Create data_sources directory for source implementations
  - Implement KaggleDataSource class with CSV loading and Pandas indexing
  - Implement NFLReadPyDataSource class using nflreadpy package
  - Implement ESPNDataSource class with HTTP client and JSON parsing
  - Add error handling and retry logic for each data source
  - _Requirements: 4.1, 4.2, 4.3, 7.1_

- [x] 4. Implement Query Parser Node
  - Create query_parser.py with parse_query function
  - Implement LLM-based query parsing using OpenAI function calling
  - Define structured output schema for parsed queries (players, statistics, time_period, filters)
  - Add logic to incorporate conversation context for reference resolution
  - Handle ambiguous queries by requesting clarification
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 5. Implement Retriever Node
  - Create retriever.py with retrieve_data function
  - Implement data source routing logic based on time period
  - Add filter application using Pandas operations
  - Implement fallback logic when primary data source fails
  - Normalize data formats across different sources
  - _Requirements: 4.3, 7.1_

- [x] 6. Implement LLM Node for insight generation
  - Create llm_node.py with generate_insights function
  - Design prompt template for generating insights from statistical data
  - Implement logic to include conversation history in prompts
  - Add formatting for comparisons with percentage changes and rankings
  - Include contextual information like league averages and trends
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 2.3_

- [x] 7. Implement Memory Node
  - Create memory.py with update_memory function
  - Implement conversation history storage (last 10 turns)
  - Add logic to extract mentioned players and statistics from each turn
  - Create get_context function to retrieve relevant history for query parsing
  - Implement session initialization and cleanup
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 8. Build LangGraph workflow
  - Create workflow.py to define the LangGraph state machine
  - Define all workflow nodes (entry, query_parser, retriever, llm, memory, exit)
  - Connect nodes with edges to create the processing pipeline
  - Add conditional edges for error handling
  - Implement state initialization and finalization
  - _Requirements: 1.3, 7.2, 7.5_

- [x] 9. Implement Chainlit interface
  - Create app.py with Chainlit decorators (@cl.on_chat_start, @cl.on_message)
  - Implement chat session initialization with LangGraph workflow
  - Add message handler to process user input through workflow
  - Implement streaming response handler to display LLM output in real-time
  - Add visual indicators for processing state
  - Store conversation history in Chainlit session
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 1.1_

- [x] 10. Implement error handling and logging
  - Create error_handler.py with centralized error handling functions
  - Add try-catch blocks in each workflow node
  - Implement user-friendly error messages for different error types
  - Add logging configuration with appropriate log levels
  - Create error recovery logic for data source failures
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 11. Add caching layer
  - Implement in-memory cache for Kaggle dataset on startup
  - Add TTL-based caching for nflreadpy data (24-hour expiration)
  - Create cache for frequently queried player statistics
  - Implement cache invalidation logic
  - _Requirements: 4.4_

- [x] 12. Create configuration and environment setup
  - Create config.py for application configuration
  - Add environment variable loading using python-dotenv
  - Configure OpenAI API key and model selection
  - Add configuration for data source priorities and timeouts
  - Create logging configuration
  - _Requirements: 4.1, 4.2_

- [x] 13. Implement data validation and normalization
  - Create validators.py for input validation
  - Add player name normalization (handle spelling variations)
  - Implement data type validation for statistics
  - Add time period validation (valid seasons, weeks)
  - Create data normalization functions for cross-source consistency
  - _Requirements: 6.4, 4.3_

- [ ]* 14. Write unit tests for core components
  - Write tests for Query Parser Node with various query types
  - Write tests for Retriever Node with mocked data sources
  - Write tests for LLM Node with sample data
  - Write tests for Memory Node operations
  - Write tests for data source implementations with mocked APIs
  - _Requirements: 6.1, 6.2, 3.1, 4.1_

- [ ]* 15. Write integration tests
  - Write tests for complete workflow execution
  - Write tests for multi-turn conversations with context
  - Write tests for error handling across nodes
  - Write tests for data source failover logic
  - _Requirements: 7.1, 7.5, 3.3_

- [ ] 16. Create documentation and examples
  - Create README.md with setup instructions and usage examples
  - Document environment variables in .env.example
  - Add inline code comments for complex logic
  - Create example queries document showing supported question types
  - _Requirements: 1.1, 1.2, 1.4_
