import pytest
from rich.text import Text


@pytest.fixture
def hebrew_win_1255():
    return {
        'encoding': 'Windows-1255',
        'language': 'Hebrew',
        'confidence': 0.62538832,
    }
