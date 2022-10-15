from pdfalyzer.helpers.string_helper import is_prefixed_by_any

TEST_TITLE = "Jacques and Carl's Excellent Adventure"


def test_is_prefixed_by_any():
    assert is_prefixed_by_any(TEST_TITLE, ['Lacan', 'Jung', 'Freud']) is False
    assert is_prefixed_by_any(TEST_TITLE, ['Lacan', 'Jac', 'Freud']) is True
