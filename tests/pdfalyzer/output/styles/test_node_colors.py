from pdfalyzer.output.styles.node_colors import get_class_style, get_label_style


def test_get_class_style():
    assert get_class_style({'a': 1}) == 'color(64)'
    assert get_class_style([1, 2]) == 'color(143)'
    assert get_class_style(5) == 'cyan bold'


def test_get_label_style():
    assert get_label_style('/Contents') == 'medium_purple1'
