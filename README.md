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

## Detailed Installation & Setup Guide

### 1. Prerequisites

- **Python 3.10** or higher.
- **Google Gemini API Key**: You can get one from [Google AI Studio](https://aistudio.google.com/).
- **Git**: To clone the repository.

### 2. Clone the Repository

Open your terminal or command prompt and run:

```bash
git clone https://github.com/nikito4kv/ai-browser-use.git
cd AgentBrowser
```

### 3. Install Dependencies

We recommend using [uv](https://github.com/astral-sh/uv) for fast package management, but standard `pip` works too.

**Option A: Using `uv` (Recommended)**
```bash
# If you don't have uv installed:
pip install uv

# Sync dependencies
uv sync
```

**Option B: Using `pip`**
```bash
pip install -e .
```

### 4. Install Playwright Browsers

The agent controls a Chromium browser which must be installed:

```bash
playwright install chromium
```

### 5. Configure API Key

Create a file named `.env` in the root directory of the project (`AgentBrowser/`).
Open it with a text editor and add your key:

```env
GEMINI_API_KEY=your_actual_api_key_here
```

---

## How to Run & Use

### Starting the Agent

To start the interactive CLI:

```bash
python main.py
```

### Headed Mode & Logging In (IMPORTANT)

By default, the agent runs in **Headed Mode** (the browser window is visible). This is a feature, not a bug!

**How to log in to your accounts (Gmail, LinkedIn, GitHub, etc.):**

1.  **Run the agent**: `python main.py`
2.  The browser window will open automatically.
3.  **IGNORE the agent for a moment.** Go to the browser window yourself.
4.  Navigate to the site you want (e.g., `gmail.com`).
5.  **Log in manually** with your username and password.
6.  Once logged in, you can close the tab or just switch back to the terminal.
7.  **The session is saved!** The agent uses a persistent user profile (stored in the `user_data_dir` folder).
8.  Now you can ask the agent: *"Check my latest emails"* or *"Go to GitHub and star the AgentBrowser repo"*, and it will already be logged in.

### Usage Examples

In the CLI prompt `🤖 Command >`, try these:

- **Research**: "Navigate to news.ycombinator.com and give me a summary of the top 3 stories."
- **Search**: "Go to Google, search for 'latest AI news', and tell me what's trending."
- **Analysis**: "Find the login button on github.com and describe the page structure."
- **Personal**: "Check my unread emails on Gmail." (Requires manual login first, see above).

## Security & Safety

AgentBrowser includes a **Security Middleware** designed to prevent accidental data loss or unauthorized transactions.

1.  **Keyword Detection**: The agent scans element text for risky keywords (Delete, Buy, Pay, Send, etc.).
2.  **Human-in-the-Loop**: If a risky action is detected, the CLI will intercept the command, display a **SECURITY ALERT**, and wait for your explicit `y/n` confirmation.
3.  **Sandboxed Browser**: Uses Playwright's persistent context for isolated browsing sessions.

## Troubleshooting

-   **"Playwright not installed"**: Run `playwright install chromium`.
-   **"API Key missing"**: Check your `.env` file is in the root folder and named exactly `.env`.
-   **"Browser closes immediately"**: Ensure you aren't running inside a restricted container that blocks GUI apps.

---
*Note: This project is for educational and development purposes. Always be cautious when giving automated agents access to your personal accounts.*
