import pytest

def test_dependencies_installed():
    try:
        import playwright
        import google.genai
        import PIL
        import dotenv
        import rich
    except ImportError as e:
        pytest.fail(f"Dependency not installed: {e}")
