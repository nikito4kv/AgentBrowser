# AgentBrowser

Autonomous AI agent for browser automation powered by Gemini 2.0 Flash and Playwright.

## Setup

1.  **Install dependencies:**
    ```bash
    uv sync
    ```

2.  **Configure Environment:**
    Create a `.env` file and add your Google Gemini API key:
    ```
    GEMINI_API_KEY=your_api_key_here
    ```

## Authentication (Important!)

Before running the agent for tasks requiring login (e.g., Email, Job Search), you must perform a manual login to save your session.

1.  **Run the auth setup script:**
    ```bash
    uv run python setup_auth.py
    ```
2.  **Login manually:**
    A browser window will open. Navigate to your target sites (e.g., gmail.com, hh.ru) and log in. Check "Remember me".
3.  **Close the browser:**
    Once logged in, close the browser window or stop the script. The session cookies will be saved in the `user_data_dir` folder.

## Usage

Run the agent with a task description:

```bash
uv run python main.py "Go to github.com and search for 'AgentBrowser'"
```
