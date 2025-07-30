import pytest


@pytest.fixture
def hebrew_win_1255():
    return {
        'encoding': 'Windows-1255',
        'language': 'Hebrew',
        'confidence': 0.62538832,
    }
