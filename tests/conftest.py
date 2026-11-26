import pytest
from unittest.mock import MagicMock, AsyncMock, patch

@pytest.fixture(autouse=True)
def mock_playwright_manager():
    """
    Automatically mocks playwright in BrowserManager to prevent 
    launching real browsers during unit tests.
    """
    with patch('agentbrowser.browser.manager.async_playwright') as mock_ap:
        # Setup the mock chain
        mock_playwright_obj = MagicMock()
        mock_ap.return_value.start = AsyncMock(return_value=mock_playwright_obj)
        mock_playwright_obj.stop = AsyncMock() # Fix: stop must be awaitable
        
        mock_context = MagicMock()
        mock_playwright_obj.chromium.launch_persistent_context = AsyncMock(return_value=mock_context)
        mock_context.close = AsyncMock() # Fix: close must be awaitable
        
        mock_page = MagicMock()
        mock_context.pages = [mock_page]
        mock_context.new_page = AsyncMock(return_value=mock_page)
        
        # Mock page methods
        mock_page.goto = AsyncMock()
        mock_page.screenshot = AsyncMock(return_value=b"fake_screenshot")
        mock_page.evaluate = AsyncMock(return_value={"success": True, "coordinates": [10, 10], "pageContent": "<html></html>"})
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.mouse.click = AsyncMock()
        mock_page.keyboard.type = AsyncMock()
        mock_page.keyboard.press = AsyncMock()
        mock_page.mouse.wheel = AsyncMock()
        mock_page.title = AsyncMock(return_value="Mock Title")

        # BrowserManager works through frames (main frame for plain refs, child
        # frames for `frame{i}_ref_N`): JS helpers run via frame.evaluate and
        # elements are driven through handles from frame.evaluate_handle.
        mock_page.main_frame = make_frame()
        mock_page.frames = [mock_page.main_frame]

        yield mock_ap


def make_handle():
    """Element handle double: every action the manager performs is awaitable."""
    handle = MagicMock()
    handle.click = AsyncMock()
    handle.type = AsyncMock()
    handle.scroll_into_view_if_needed = AsyncMock()
    return handle


def make_frame(url="https://example.test/"):
    """Frame double returning a healthy, unoccluded element and an empty page tree."""
    frame = MagicMock()
    frame.url = url
    frame.evaluate = AsyncMock(return_value={
        "success": True,
        "coordinates": [10, 10],
        "isOccluded": False,
        "occludedBy": None,
        "attributes": {"text": "Target", "ariaLabel": ""},
        "pageContent": "<html></html>",
    })
    frame.evaluate_handle = AsyncMock(return_value=make_handle())
    return frame