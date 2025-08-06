# BrowseMind

AI-powered browser automation agent using Google's Gemini.

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
```

Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey).

## Usage

Run the browser agent with predefined tasks or custom instructions:

```bash
# WhatsApp summary
browsemind run whatsapp_summary --chat-name "Group Name" --message-count 50

# Web search
browsemind run web_search --query "latest AI developments" --result-count 5

# Email check
browsemind run email_check --email-count 10

# Custom task
browsemind custom "Navigate to example.com and extract the main heading"
```

### Available Options

- `--browser`: Browser to use (chrome, firefox, edge, zen) [default: chrome]
- `--browser-path`: Optional path to browser executable
- `--verbose`, `-v`: Enable verbose logging
- `--log-file`: Path to save log file

### Commands

- `run <task_name>`: Run a predefined task by name
- `custom <task_description>`: Run a custom task with a provided description

### Available Predefined Tasks

- `web_search`: Search Google and summarize results
  - Required: `--query` (search query)
  - Optional: `--result-count` (number of results, default: 5)

- `whatsapp_summary`: Summarize WhatsApp chat and respond
  - Required: `--chat-name` (name of the chat)
  - Optional: `--message-count` (number of messages to analyze, default: 40)

- `email_check`: Check and summarize Gmail emails
  - Optional: `--email-count` (number of emails to check, default: 5)

## Development

Install development dependencies:

```bash
uv pip install -e ".[dev]"
```

Run linting and formatting:

```bash
uv run ruff check .
uv run black .
uv run mypy .
```

## License

MIT License