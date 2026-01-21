# AgentBrowser (Gemini 2.5 Edition)

A powerful, autonomous browser automation agent powered by Google's Gemini 2.5 Pro and Flash models. This project implements a sophisticated "Anthropic-style" architecture, enabling the agent to navigate the web like a human, using vision, coordinates, and DOM accessibility trees.

## Features

- **Hybrid Model Architecture**:
  - **The Brain (Gemini 2.5 Pro)**: Handles high-level reasoning, visual analysis of screenshots, and strategic planning.
  - **The Specialist (Gemini 2.5 Flash)**: Optimized for fast DOM tree analysis and finding specific element references (`ref_id`).
- **Vision-Based Navigation**: The agent "sees" the browser through screenshots, allowing it to interact with complex modern web apps.
- **DOM-Aware Targeting**: Uses a custom JavaScript-based Accessibility Tree to target elements reliably via `ref_id`, avoiding brittle coordinate-only approaches.
- **Advanced CLI Interface**: Built with `rich` for a professional, animated terminal experience including thought panels, tool call highlights, and real-time status spinners.
- **Hard Security Layer**: A built-in safety middleware that detects potentially destructive actions (deleting, buying, sending) and mandates explicit human confirmation via a "Security Intercept" prompt.
- **Smart Stabilization**: Automatic "Smart Wait" logic that ensures pages are fully loaded and stable before the agent takes its next action.

## Project Structure

```text
├── agentbrowser/
│   ├── agent/
│   │   └── logic.py       # Main Agent logic and system prompts
│   └── browser/
│       ├── manager.py     # Playwright wrapper and tool execution logic
│       └── utils/         # JS utilities for DOM and element analysis
├── main.py                # Advanced CLI Interface (Terminal)
├── tests/                 # Unit and integration tests
├── pyproject.toml         # Project dependencies
└── .env                   # Environment variables (API Key)
```

## Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Google Gemini API Key

### Setup

1. **Clone the repository**:
   ```bash
   git clone [<repository-url>](https://github.com/nikito4kv/ai-browser-use.git)
   cd AgentBrowser
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   # or
   pip install -e .
   ```

3. **Configure environment**:
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

### Running the Agent

```bash
python main.py
```

## Usage Examples

Once running, try commands like:
- "Navigate to news.ycombinator.com and give me a summary of the top 3 stories."
- "Go to Google, search for 'latest AI news', and tell me what's trending."
- "Find the login button on github.com and describe the page structure."
- "Check my email on Gmail (requires login in the browser)."

## Security & Safety

AgentBrowser includes a **Security Middleware** designed to prevent accidental data loss or unauthorized transactions.

1. **Keyword Detection**: The agent scans element text for risky keywords (Delete, Buy, Pay, Send, etc.).
2. **Human-in-the-Loop**: If a risky action is detected, the CLI will intercept the command, display a **SECURITY ALERT**, and wait for your explicit `y/n` confirmation.
3. **Sandboxed Browser**: Uses Playwright's persistent context for isolated browsing sessions.

## Architecture Highlights

**Element Targeting**: Instead of guessing pixels, the agent calls `read_page` to get a YAML-like tree of the DOM. Each element gets a unique `ref_id`. The agent then says "Click ref_42", and our JS engine finds the exact coordinates for the click.

**Timing & Stability**: We use `networkidle` states and trice-click strategies to ensure focus and stability, especially on complex Single Page Applications (SPAs).

---
*Note: This project is for educational and development purposes. Always be cautious when giving automated agents access to your personal accounts.*
