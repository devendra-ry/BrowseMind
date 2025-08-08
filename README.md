# BrowseMind

AI-powered browser automation agent using Google's Gemini.

## Features

- **Intelligent Automation**: Uses Google's Gemini AI to intelligently navigate and interact with web pages
- **Error Handling**: Comprehensive error handling with detailed error codes and logging
- **Logging**: Rich logging with colored output for better debugging and monitoring
- **Testing**: Full test suite with pytest for reliability and code quality
- **Type Safety**: Strict type checking with mypy for fewer runtime errors
- **Code Quality**: Follows Python best practices with linting and formatting

## Setup with uv

This project uses [uv](https://github.com/astral-sh/uv) for Python package and virtual environment management.

### Prerequisites

- [Python](https://www.python.org/downloads/) (>= 3.11)
- [uv](https://github.com/astral-sh/uv#getting-started)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd BrowseMind
   ```

2. **Create and activate virtual environment**
   ```bash
   uv venv
   # On Windows
   .venv\Scripts\activate
   # On Unix/macOS
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   uv pip install -e .
   ```

4. **Install Playwright browsers**
   ```bash
   uv run playwright install
   ```

### Environment Setup

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_api_key_here
LOG_LEVEL=INFO  # Optional: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey).

## Usage

Run the browser agent with a task description:

```bash
# Run a custom task
browsemind run "Navigate to example.com and extract the main heading"

# Search Google for information
browsemind run "Search Google for the latest developments in AI and summarize the results"

# Check a website and report findings
browsemind run "Go to github.com and find the most popular Python repository"
```

The agent will:
1. Launch a browser window
2. Process your task using the AI
3. Automatically navigate and interact with web pages
4. Return the results when finished

## Development

### Install development dependencies:

```bash
uv pip install -e ".[dev]"
```

### Run tests:

```bash
uv run pytest
```

### Run linting and formatting:

```bash
uv run ruff check .
uv run black .
uv run mypy .
```

### Run linting with auto-fix:

```bash
uv run ruff check --fix .
```

## Project Structure

```
BrowseMind/
├── src/
│   └── browsemind/
│       ├── __init__.py          # Package metadata
│       ├── agent.py             # Core agent logic
│       ├── browser.py           # Browser management
│       ├── config.py            # Configuration management
│       ├── exceptions.py        # Custom exceptions
│       ├── llm.py               # LLM interaction
│       └── main.py              # CLI entry point
├── tests/                       # Test suite
│   ├── conftest.py             # pytest configuration
│   ├── test_config.py          # Configuration tests
│   └── test_exceptions.py      # Exception tests
├── pyproject.toml              # Project configuration
├── README.md                   # This file
└── .env.example               # Example environment file
```

## Logging

The application uses structured logging with multiple levels:
- **DEBUG**: Detailed information for troubleshooting
- **INFO**: General information about the application flow
- **WARNING**: Warning messages about potential issues
- **ERROR**: Error messages for handled exceptions
- **CRITICAL**: Critical errors that may stop execution

Set the log level using the `LOG_LEVEL` environment variable.

## Error Handling

The application provides detailed error handling with specific error codes:
- **Configuration Errors**: Issues with environment setup
- **Browser Errors**: Problems with browser automation
- **LLM Errors**: Issues with AI model interactions
- **Application Errors**: General application-specific errors

Each error includes a specific error code for easier debugging and troubleshooting.

## License

MIT License