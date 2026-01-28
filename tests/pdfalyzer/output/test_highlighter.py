from rich.highlighter import ReprHighlighter

from pdfalyzer.output.highlighter import CUSTOM_LOG_HIGHLIGHTS, HIGHLIGHT_PATTERNS


def test_highlighter_patterns():
    assert all('(?P<' in pattern for pattern in HIGHLIGHT_PATTERNS)

    for capture_group_label in CUSTOM_LOG_HIGHLIGHTS.keys():
        label = f"<{capture_group_label.removeprefix(ReprHighlighter.base_style)}>"
        print(f" label: {label}")
        #import pdb;pdb.set_trace()
        assert any(label in pattern for pattern in HIGHLIGHT_PATTERNS), f"Capture group {label} not found!"
