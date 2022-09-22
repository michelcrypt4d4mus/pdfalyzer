import pytest
from rich.text import Text

from lib.chardet_manager import ChardetManager


@pytest.fixture
def hebrew_win_1255():
    return {
        'encoding': 'Windows-1255',
        'language': 'Hebrew',
        'confidence': 0.62538832,
    }


def test_tuple_builder(hebrew_win_1255):
    result = ChardetManager.build_chardet_result(hebrew_win_1255)
    assert all(isinstance(val, Text) for val in [result.encoding, result.language, result.confidence_str])
    assert result.encoding.plain == 'windows-1255'
    assert round(result.confidence, 1) == 62.5
    assert result.confidence_str.plain == '62.5% (hebrew)'
