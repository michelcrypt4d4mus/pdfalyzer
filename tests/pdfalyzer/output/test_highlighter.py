from rich.highlighter import ReprHighlighter

from pdfalyzer.output.theme import LOG_THEME_BASE_DICT
from pdfalyzer.output.highlighter import HIGHLIGHT_PATTERNS, LogHighlighter


def test_highlighter_patterns():
    assert all('(?P<' in pattern for pattern in HIGHLIGHT_PATTERNS)

    for capture_group_label in LOG_THEME_BASE_DICT.keys():
        label = f"<{capture_group_label.removeprefix(ReprHighlighter.base_style)}>"
        assert any(label in pattern for pattern in HIGHLIGHT_PATTERNS), f"Capture group {label} not found!"


def test_get_styles():
    assert LogHighlighter.get_style('children') == 'repr.child'
