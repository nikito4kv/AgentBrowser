import pytest
from agentbrowser.browser.manager import BrowserManager

@pytest.mark.asyncio
async def test_extract_content():
    manager = BrowserManager()
    await manager.start()
    
    html_content = """
    <html>
    <body>
        <h1>Title</h1>
        <p>This is a paragraph of <b>important</b> text.</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
    </body>
    </html>
    """
    await manager.page.set_content(html_content)
    
    md_text = await manager.extract_content()
    
    assert "Title" in md_text
    assert "important" in md_text
    assert "Item 1" in md_text
    
    await manager.close()
