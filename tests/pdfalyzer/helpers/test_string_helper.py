from pdfalyzer.helpers.string_helper import is_prefixed_by_any, replace_digits


TEST_TITLE = "Jacques and Carl's Excellent Adventure"


def test_is_prefixed_by_any():
    assert is_prefixed_by_any(TEST_TITLE, ['Lacan', 'Jung', 'Freud']) is False
    assert is_prefixed_by_any(TEST_TITLE, ['Lacan', 'Jac', 'Freud']) is True



def test_replace_digits():
    assert replace_digits('abcd') == 'abcd'
    assert replace_digits('a1b2c3d4e5f6') == 'axbxcxdxexfx'
