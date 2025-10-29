# NFL Player Performance Chatbot

A conversational AI system for querying and analyzing NFL player statistics using natural language.

## Features

- Natural language queries about NFL player statistics
- Multi-player comparisons across various metrics
- Conversation context for follow-up questions
- Access to historical (1999-2023) and current season data
- Contextual insights with league averages and trends
- **Multi-layer caching system** for improved performance
  - In-memory Kaggle dataset cache
  - TTL-based nflreadpy data cache (24-hour expiration)
  - LRU query results cache

## Technology Stack

- **Interface**: Chainlit (web-based chat UI)
- **Workflow**: LangGraph (state machine orchestration)
- **LLM**: OpenAI GPT-4
- **Data Processing**: Pandas
- **Data Sources**: Kaggle, nflreadpy, ESPN API

## Setup

### Prerequisites

- Python 3.10 or higher
- OpenAI API key

### Installation

1. Clone the repository and navigate to the project directory

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and other settings
```

4. (Optional) Download the Kaggle NFL dataset and place it in the `data/` directory

### Configuration

The application uses a centralized configuration system that loads settings from environment variables. All configuration options are documented in `.env.example`.

Key configuration areas:
- **OpenAI**: API key, model selection, temperature, timeouts
- **Data Sources**: Priorities, timeouts, retry logic
- **Caching**: Cache settings for different data sources
- **Memory**: Conversation history settings
- **Workflow**: LangGraph workflow parameters
- **Logging**: Log levels and output configuration

To view current configuration:
```bash
python config.py
```

### Running the Application

Start the Chainlit application:
```bash
chainlit run app.py
```

The application will be available at `http://localhost:8000`

## Project Structure

```
.
├── app.py                 # Chainlit application entry point
├── workflow.py            # LangGraph workflow definition
├── config.py              # Centralized configuration management
├── logging_config.py      # Logging configuration
├── cache_manager.py       # Caching layer implementation
├── cache_utils.py         # Cache management utilities
├── error_handler.py       # Error handling utilities
├── nodes/                 # LangGraph workflow nodes
├── data_sources/          # Data source implementations
├── models/                # Data models and state definitions
├── tests/                 # Test suite
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variable template
├── CACHING.md            # Caching documentation
└── README.md             # This file
```

## Caching

The chatbot includes a comprehensive caching layer to improve performance:

- **Kaggle Dataset Cache**: In-memory cache for historical data (1999-2023)
- **nflreadpy Cache**: TTL-based cache for current season data (24-hour expiration)
- **Query Results Cache**: LRU cache for frequently queried statistics (1-hour expiration)

### Cache Configuration

Configure caching via environment variables in `.env`:

```bash
# Enable Kaggle dataset caching
KAGGLE_CACHE_ENABLED=true

# Warm cache on startup (recommended)
WARM_KAGGLE_CACHE_ON_STARTUP=true

# TTL for nflreadpy data (hours)
NFLREADPY_CACHE_TTL_HOURS=24

# Query cache capacity
QUERY_CACHE_CAPACITY=100

# TTL for query results (hours)
QUERY_CACHE_TTL_HOURS=1
```

### Cache Management

View cache statistics:
```bash
python cache_utils.py stats
```

Clean up expired entries:
```bash
python cache_utils.py cleanup
```

See [CACHING.md](CACHING.md) for detailed documentation.

## Usage Examples

Ask questions like:
- "How did Patrick Mahomes perform in 2023?"
- "Compare Josh Allen and Joe Burrow passing yards"
- "Show me the top receivers by yards this season"
- "What was Travis Kelce's EPA last year?"

## Development Status

This project is currently under development. See `.kiro/specs/nfl-player-chatbot/tasks.md` for implementation progress.

## License

MIT License
