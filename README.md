<div align="center">

# AgentBrowser

**A vision-driven autonomous browser agent: Gemini 2.5 looks at screenshots, reads a DOM accessibility tree, and drives a real Chromium through Playwright.**

[![Python](https://img.shields.io/badge/python-3.13%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Playwright](https://img.shields.io/badge/Playwright-1.57%2B-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Pro%20%2B%20Flash-4285F4?logo=googlegemini&logoColor=white)](https://ai.google.dev/)
[![Tests](https://img.shields.io/badge/tests-pytest%20(mocked%2C%20no%20API%20key)-blue?logo=pytest&logoColor=white)](#tests)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

---

## What it does

You type a goal in a terminal (`Go to news.ycombinator.com and summarise the top 3 stories`). The agent opens a visible Chromium window and repeats a loop until it calls `task_completed`:

1. **Observe** – take a JPEG screenshot (1280x800, quality 80) and, on request, a text accessibility tree of the page and its iframes.
2. **Reason** – send the whole conversation (goal, past actions, results, latest screenshot) to `gemini-2.5-pro`, which must answer with a tool call.
3. **Act** – the tool call (`browser_action`, `ask_user` or `task_completed`) is executed by a Playwright wrapper; the result string and a fresh screenshot are appended to the conversation.

### One step, concretely

The goal is `Open the first story on Hacker News`. The agent has just navigated and sees the front page screenshot. The conversation holds (message shapes are from `main.py`; the page content is illustrative):

```text
user   : GOAL: Open the first story on Hacker News  + [screenshot]
model  : browser_action(action="navigate", text="news.ycombinator.com")
user   : function_response {"result": "Navigated to https://news.ycombinator.com"}  + [screenshot]
model  : (text) "The front page loaded. I need the ref of the first story link."
         browser_action(action="read_page")
user   : function_response {"result": "=== Main Content ===\n  - link \"Show HN: ...\" [ref=ref_14] ..."}  + [screenshot]
model  : browser_action(action="left_click", ref="ref_14")      # <- the step below
```

Executing that last call (`BrowserManager.execute_action`):

```text
observe : the JS helper scrolls ref_14 into view, computes its centre point and asks the
          browser what element sits on top of that point (document.elementFromPoint)
reason  : keyword safety check on the element text / aria-label ("delete", "buy", "pay", "send", ...)
          no keyword hit, nothing covers the element -> click is allowed
act     : Playwright element-handle click  ->  "Clicked element ref_14"
          then main.py waits ~1 s, takes a new screenshot and feeds both back to Gemini
```

If something covers the element, the agent gets an actionable error instead of a silent mis-click (real output from the repo's own test page, see [Verified behaviour](#verified-behaviour)):

```text
Action Failed: Element ref_2 is occluded by 'div#overlay'. Use force=True to click anyway, or close the obstructing element.
```

## Why it's interesting

Everything below is implemented in the code and was exercised on the fixture pages in `tests/` (see the limits in [Safety & limitations](#safety--limitations)).

- **Vision first, DOM second.** The model decides from screenshots; a custom JS accessibility-tree walker (`browser_dom_script.js`, adapted from Playwright/Anthropic's reference tooling) hands it stable `ref_N` ids so it does not have to guess pixel coordinates. Coordinates are still accepted as a fallback.
- **Occlusion and overlap handling.** Before a ref-based click, `browser_element_script.js` scrolls the element to the centre and uses `elementFromPoint` to detect a covering element (cookie banner, modal, sticky header). The error names the culprit (`div#overlay`) so the model can close it. `force=True` overrides.
- **Robust typing.** Typing triple-clicks the field to select existing text, presses Backspace, then types with a 50 ms per-key delay, using a Playwright element handle so it also works inside iframes. If an overlay intercepts the click, Playwright's actionability check fails with the intercepting element in the error.
- **Iframe-aware.** `read_page` and `find` walk every frame; refs from child frames are prefixed `frame{i}_ref_N` and resolved back to the right frame when acting.
- **History pruning.** Only the latest message keeps its image; older screenshots become `[Image Removed]` and text parts over 20 000 characters become `[Large DOM Tree Removed]`, so the context does not grow with every screenshot (`Agent._prune_history`, covered by `tests/test_history_pruning.py`).
- **Two-model split.** Gemini 2.5 Pro does the reasoning; the `find` tool sends the full accessibility tree to Gemini 2.5 Flash, which returns up to 20 matching `ref` ids with reasons.
- **Prompted reasoning loop.** The system prompt enforces an ANALYZE -> LOCATE -> ACT -> VERIFY workflow, forces a tool call on every turn and tells the model to `wait` while a page loads (`tests/test_cot.py` checks that the prompt contains these sections).
- **Human-in-the-loop guard.** A click on an element whose text or aria-label contains a risky keyword (English and Russian lists: delete, buy, pay, send, confirm, order, checkout, ...) raises `SecurityRiskError`; the CLI shows a red alert and waits for `y/n` before re-running with `force=True`. The model also has an `ask_user` tool.
- **Resilient API calls.** `Agent.think` retries up to 5 times with exponential backoff on 429/503/overloaded errors and re-asks when Gemini returns a malformed function call.
- **Stealth + persistent profile.** `playwright-stealth`, a realistic Chrome user agent and `--disable-blink-features=AutomationControlled`; the browser uses a persistent profile (`user_data_dir/`) so you can log in once by hand and the agent reuses the session.
- **Scrolling.** Page scroll by pixels in four directions (default 300) or `scroll_into_view` for a given ref.

## Architecture

```text
agentbrowser/
  agent/logic.py              Agent: system prompt, tool schema, history pruning, Gemini call + retries
  browser/manager.py          BrowserManager: Playwright wrapper, action dispatch, safety + occlusion checks
  browser/utils/
    browser_dom_script.js     accessibility tree with ref ids (interactive / all)
    browser_element_script.js element lookup, scroll into view, occlusion + attributes
    browser_text_script.js    article/main text extraction helper
main.py                       Rich CLI + orchestration loop (Orchestrator)
tests/                        pytest suite and HTML fixtures (overlay / occlusion pages)
conductor/                    spec-driven development notes (tracks, specs, plans) used while building
```

```text
        +--------------------------- main.py (Orchestrator) ---------------------------+
        |                                                                              |
  goal  v                                                                              |
 +------------+  screenshot   +-------------------------+  tool call   +--------------+|
 |  Chromium  | ------------> | Agent.think()           | -----------> | BrowserManager|
 | (Playwright|               | gemini-2.5-pro          |  browser_    | execute_action|
 |  persistent|  <----------- | prune old screenshots   |  action /    |  click/type/  |
 |  profile)  |  result text  | retry on 429/503        |  ask_user /  |  scroll/      |
 +------------+  + screenshot +-------------------------+  task_       |  read_page    |
        ^                                                  completed    |  find ------> Gemini Flash
        |                                                               +--------------+|
        +---------------------- observe -> reason -> act -----------------------------+
```

## Tech stack

Python 3.13, [Playwright](https://playwright.dev/python/) (async API), [playwright-stealth](https://pypi.org/project/playwright-stealth/), [google-genai](https://pypi.org/project/google-genai/) (Gemini 2.5 Pro / Flash), [Rich](https://github.com/Textualize/rich) for the terminal UI, python-dotenv, Pillow, markdownify, pytest + pytest-asyncio. Dependencies are locked in `uv.lock`.

## Quick start

Requirements: Python 3.13+, a [Gemini API key](https://aistudio.google.com/), and a desktop session (the browser opens in headed mode).

```bash
git clone https://github.com/nikito4kv/AgentBrowser.git
cd AgentBrowser

# with uv (uses uv.lock)
uv sync
uv run playwright install chromium
```

Without uv, install the packages listed in `pyproject.toml` into a virtualenv yourself:

```bash
pip install google-genai markdownify pillow playwright playwright-stealth python-dotenv rich pytest pytest-asyncio
playwright install chromium
```

Create a `.env` file in the project root (it is git-ignored):

```env
GEMINI_API_KEY=your_api_key_here
```

## Usage

```bash
uv run python main.py        # or: python main.py inside your virtualenv
```

This opens the Chromium window and an interactive prompt (`Command >`). Type a goal in plain language; type `exit` or `quit` to leave. The terminal shows the agent's thoughts, each tool call, the (truncated) result and the final answer. Examples:

- `Navigate to news.ycombinator.com and give me a summary of the top 3 stories.`
- `Go to Google, search for "latest AI news", and tell me what's trending.`
- `Find the login button on github.com and describe the page structure.`

To use an account, log in manually in the opened browser window first; the profile is stored in `user_data_dir/` and reused on later runs. Screenshots of every step are saved to `debug_screenshots/run_<timestamp>/` and API errors go to `agent_debug.log` (both git-ignored).

## Tests

18 test functions in 16 files (`grep -c "def test_" tests/*.py`). They use a `conftest.py` fixture that mocks `async_playwright`, so no browser, network or API key is needed. Run them with:

```bash
uv run python -m pytest -q       # plain `pytest` cannot import the package: the project is not installed
```

Current result (Python 3.13, locked dependencies, no `GEMINI_API_KEY`): **12 passed, 6 failed**.

Known issue: the 6 failing tests (`test_click`, `test_type`, `test_robust_click`, `test_robust_type`, `test_occlusion`, `test_scraping`) were written against an earlier version of `BrowserManager` (page-level `mouse.click` / `page.evaluate`) and have not been updated after the move to element handles and per-frame DOM reading. The passing tests cover history pruning, the system prompt and tool schema, the browser lifecycle, screenshots, scrolling and the stealth setup.

### Verified behaviour

Because the mocked tests lag behind the code, the behaviour was also checked against the real fixture pages in `tests/` with a real Chrome (no model, no network). `read_page` + `left_click` on `test_occlusion.html` and `test_overlap.html` returned the occlusion error shown above; a `force=True` click was reported as `Clicked element ref_2` but the overlay swallowed it (the page still read "Not Clicked"); typing into the covered input of `test_overlap_type.html` failed with Playwright's "`<div id="overlay"></div>` intercepts pointer events" timeout and succeeded with `force=True`; and a button labelled "Delete account" raised `SecurityRiskError`.

## Safety & limitations

This is a hobby/portfolio project, not a hardened product.

- **It drives a real browser with real sessions.** There is no sandbox or VM: the agent uses a persistent profile, so any account you log into is available to it, and it can click, type and submit on your behalf. Use a throwaway profile or test accounts if in doubt.
- **The keyword guard is a heuristic, not a security boundary.** It only checks clicks made through a `ref` (clicks by coordinates, typing and key presses such as Enter are not checked), it matches substrings in the element text and aria-label, it only knows English and Russian words, and it fails open if the check itself errors. `force=True` bypasses it and the occlusion check.
- **No step or cost limit.** The loop runs until the model calls `task_completed`; API errors are retried indefinitely by the CLI. Watch the first runs and press Ctrl+C to interrupt.
- **Page content goes to Google.** Screenshots and the accessibility tree of whatever page is open are sent to the Gemini API. Do not point it at pages you would not want to share. It can also open `file://` URLs.
- **Stealth is best-effort.** It lowers obvious automation signals but will not beat serious bot protection, and the agent does not solve CAPTCHAs. Respect the terms of service of the sites you automate.
- **Browser support is Chromium only**, in headed mode (`headless=False` in `main.py`).
- Not implemented despite appearing in the planning notes under `conductor/`: a separate planner/actor model pair and long-term memory.

## License

MIT, see [LICENSE](LICENSE). The three scripts in `agentbrowser/browser/utils/` are adapted from Microsoft Playwright code (Apache 2.0) and keep their original notice in the file headers.

---

Built by [Nikita Lapa](https://github.com/nikito4kv) · built with an AI-assisted workflow
