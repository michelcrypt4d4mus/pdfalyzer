import pytest
from rich.text import Text
from lib.detection.encoding_detector import build_chardet_encoding_assessment


@pytest.fixture
def hebrew_win_1255():
    return {
        'encoding': 'Windows-1255',
        'language': 'Hebrew',
        'confidence': 0.62538832,
    }


def test_tuple_builder(hebrew_win_1255):
    result = build_chardet_encoding_assessment(hebrew_win_1255)
    assert all(isinstance(val, Text) for val in [result.encoding, result.language, result.confidence_str])
    assert result.encoding.plain == 'windows-1255'
    assert round(result.confidence, 1) == 62.5
    assert result.confidence_str.plain == '62.5% (Hebrew)'
