# Error Handling and Logging Documentation

This document describes the error handling and logging system implemented in the NFL Player Performance Chatbot.

## Overview

The chatbot implements a comprehensive error handling system that:
- Provides user-friendly error messages
- Logs errors with sufficient detail for debugging
- Implements fallback logic for data source failures
- Suggests alternative queries when appropriate
- Allows the system to continue operating after errors

## Requirements Addressed

- **7.1**: Implement fallback logic when data sources fail
- **7.2**: Provide clear error messages when errors occur
- **7.3**: Log errors with sufficient detail for debugging
- **7.4**: Suggest alternative queries when no results found
- **7.5**: Continue operating for subsequent queries after errors

## Components

### 1. Error Handler Module (`error_handler.py`)

The centralized error handling module provides:

#### Error Types

```python
class ErrorType(Enum):
    # Query parsing errors
    EMPTY_QUERY
    QUERY_PARSING_ERROR
    CLARIFICATION_NEEDED
    AMBIGUOUS_QUERY
    
    # Data retrieval errors
    DATA_SOURCE_UNAVAILABLE
    DATA_RETRIEVAL_FAILED
    NO_DATA_FOUND
    PLAYER_NOT_FOUND
    INVALID_TIME_PERIOD
    
    # LLM errors
    LLM_API_ERROR
    LLM_TIMEOUT
    LLM_RATE_LIMIT
    INSIGHT_GENERATION_ERROR
    
    # Memory errors
    MEMORY_ERROR
    
    # Workflow errors
    WORKFLOW_ERROR
    NODE_ERROR
    
    # General errors
    UNKNOWN_ERROR
    VALIDATION_ERROR
    CONFIGURATION_ERROR
```

#### ChatbotError Exception

Custom exception class that includes:
- Error type classification
- User-friendly message
- Additional details for logging
- Recoverability flag

```python
raise ChatbotError(
    error_type=ErrorType.DATA_RETRIEVAL_FAILED,
    message="Unable to retrieve player statistics",
    details={"player": "Patrick Mahomes", "season": 2023},
    recoverable=True
)
```

#### Key Functions

**`handle_error(error, context, default_error_type)`**
- Main error handling function
- Logs errors with context
- Returns user-friendly messages
- Determines if error is recoverable

**`get_user_friendly_message(error_type, custom_message, include_suggestions)`**
- Converts error types to user-friendly messages
- Includes helpful suggestions
- Customizable per error type

**`handle_data_source_error(error, source_name, player_name, season)`**
- Specialized handler for data source failures
- Implements fallback logic
- Provides context-specific suggestions

**`handle_llm_error(error, operation)`**
- Specialized handler for LLM API errors
- Detects rate limits and timeouts
- Provides appropriate retry suggestions

**`attempt_recovery(error, recovery_func, max_attempts)`**
- Implements retry logic with recovery functions
- Configurable maximum attempts
- Logs recovery attempts

### 2. Logging Configuration (`logging_config.py`)

Comprehensive logging system with:

#### Features

- **Rotating file logs**: Automatic log rotation when files reach size limit
- **Console output**: Optional console logging with configurable levels
- **Component-specific levels**: Different log levels for different modules
- **Detailed formatting**: Optional detailed format with file/line numbers
- **Context logging**: Add context (session ID, user ID) to log messages
- **Performance logging**: Track execution times and metrics

#### Configuration

```python
from logging_config import setup_logging

setup_logging(
    log_level="INFO",
    log_file="chatbot.log",
    log_dir="logs",
    console_output=True,
    detailed_format=False,
    max_bytes=10 * 1024 * 1024,  # 10 MB
    backup_count=5
)
```

#### Environment Variables

Configure logging via environment variables:
- `LOG_LEVEL`: Default log level (default: INFO)
- `LOG_FILE`: Specific log file name (optional)
- `LOG_DIR`: Directory for log files (default: logs)
- `LOG_CONSOLE`: Enable console output (default: true)
- `LOG_DETAILED`: Use detailed format (default: false)

#### Context Logger

Add context to all log messages:

```python
from logging_config import create_context_logger

logger = create_context_logger("workflow", session_id="abc123", user="john")
logger.info("Processing query")
# Output: [session_id=abc123 | user=john] Processing query
```

#### Performance Logger

Track execution times:

```python
from logging_config import create_performance_logger

perf_logger = create_performance_logger("workflow")
perf_logger.start("data_retrieval")
# ... perform operation ...
duration = perf_logger.end("data_retrieval")
# Output: Completed: data_retrieval (duration: 1.234s)
```

### 3. Workflow Integration

Error handling is integrated into all workflow nodes:

#### Entry Node
- Validates user input
- Initializes error state
- Handles empty queries

#### Query Parser Node
- Catches parsing errors
- Handles ambiguous queries
- Requests clarification when needed

#### Retriever Node
- Implements data source fallback
- Handles player not found errors
- Suggests alternative queries

#### LLM Node
- Handles API errors
- Detects rate limits and timeouts
- Provides retry suggestions

#### Memory Node
- Non-critical error handling
- Continues workflow even if memory fails
- Logs warnings for debugging

### 4. Data Source Fallback Logic

The retriever implements automatic fallback:

1. **Try primary source** based on time period
   - Current season → nflreadpy
   - Historical (1999-2023) → Kaggle
   
2. **On failure, try fallback sources** in priority order
   - Log warning for each failure
   - Continue to next source
   
3. **If all sources fail**
   - Raise ChatbotError with details
   - Provide user-friendly message
   - Suggest alternatives

```python
# Example fallback flow
try:
    data = primary_source.get_player_stats(...)
except Exception as e:
    log_error(e, context={...}, level="warning")
    for fallback_source in fallback_sources:
        try:
            data = fallback_source.get_player_stats(...)
            break  # Success!
        except Exception as e:
            log_error(e, context={...}, level="warning")
            continue
    else:
        # All sources failed
        raise ChatbotError(...)
```

## Error Messages

Each error type has a predefined user-friendly message with suggestions:

### Example: NO_DATA_FOUND

**Message:**
```
I couldn't find any statistics matching your query.
```

**Suggestions:**
- Double-check the player name spelling
- Verify the player was active during the specified time period
- Try a different season or broader time range
- Make sure the statistic is relevant for the player's position

### Example: DATA_SOURCE_UNAVAILABLE

**Message:**
```
I'm having trouble accessing the statistics database right now.
```

**Suggestions:**
- Please try again in a moment
- Try asking about a different time period
- Historical data (1999-2023) may still be available

## Usage Examples

### Raising Errors in Nodes

```python
from error_handler import ChatbotError, ErrorType

# In a node function
if not player_name:
    raise ChatbotError(
        error_type=ErrorType.VALIDATION_ERROR,
        message="No player name provided",
        details={"parsed_query": parsed_query},
        recoverable=True
    )
```

### Handling Errors in Workflow

```python
from error_handler import handle_error, ErrorType

try:
    state = parse_query_sync(state)
except ChatbotError as e:
    # Handle known errors
    error_info = handle_error(e, context={"node": "query_parser"})
    state["error"] = error_info["error_type"]
    state["generated_response"] = error_info["user_message"]
except Exception as e:
    # Handle unexpected errors
    error_info = handle_error(
        e,
        context={"node": "query_parser"},
        default_error_type=ErrorType.QUERY_PARSING_ERROR
    )
    state["error"] = error_info["error_type"]
    state["generated_response"] = error_info["user_message"]
```

### Logging Errors

```python
from error_handler import log_error

try:
    result = risky_operation()
except Exception as e:
    log_error(
        e,
        context={
            "operation": "data_retrieval",
            "player": player_name,
            "season": season
        },
        level="error"
    )
    raise
```

## Log Files

Logs are stored in the `logs/` directory with automatic rotation:

- **File naming**: `chatbot_YYYYMMDD_HHMMSS.log`
- **Rotation**: When file reaches 10 MB
- **Backup count**: 5 backup files kept
- **Format**: Timestamp, logger name, level, message

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General informational messages
- **WARNING**: Warning messages (non-critical errors)
- **ERROR**: Error messages (recoverable errors)
- **CRITICAL**: Critical errors (non-recoverable)

### Component Log Levels

Default log levels for different components:
- Root: INFO
- Workflow: INFO
- Nodes: INFO
- Data sources: INFO
- Error handler: INFO
- Chainlit: WARNING
- LangGraph: WARNING
- LangChain: WARNING
- OpenAI: WARNING

## Testing Error Handling

### Test Error Scenarios

1. **Empty query**: Submit empty string
2. **Invalid player name**: Query non-existent player
3. **Invalid time period**: Query invalid season/week
4. **Data source failure**: Simulate network error
5. **LLM API error**: Simulate rate limit
6. **Memory error**: Corrupt conversation history

### Verify Error Handling

1. Check user receives friendly message
2. Verify suggestions are provided
3. Confirm error is logged with details
4. Ensure workflow continues for next query
5. Validate fallback logic works

## Best Practices

1. **Always use ChatbotError** for known error conditions
2. **Provide context** when logging errors
3. **Include suggestions** in error messages
4. **Log at appropriate levels**:
   - DEBUG: Detailed debugging info
   - INFO: Normal operations
   - WARNING: Recoverable errors, fallbacks
   - ERROR: Errors requiring attention
   - CRITICAL: System failures
5. **Don't expose internal details** to users
6. **Test error paths** as thoroughly as success paths
7. **Monitor logs** for patterns and issues

## Monitoring and Debugging

### Key Metrics to Monitor

- Error frequency by type
- Data source failure rates
- LLM API error rates
- Average recovery attempts
- Workflow completion rates

### Debugging Tips

1. Check log files for detailed error traces
2. Look for patterns in error contexts
3. Verify environment variables are set
4. Test data source connectivity
5. Check LLM API quotas and limits
6. Review conversation history for context

## Future Enhancements

Potential improvements to error handling:

1. **Error analytics dashboard**: Visualize error patterns
2. **Automatic error reporting**: Send critical errors to monitoring service
3. **Smart retry logic**: Exponential backoff for transient errors
4. **Error recovery suggestions**: ML-based alternative query generation
5. **User feedback loop**: Learn from user responses to errors
6. **Circuit breaker pattern**: Temporarily disable failing data sources
7. **Health checks**: Proactive monitoring of data sources
8. **Error budgets**: Track error rates against SLOs
