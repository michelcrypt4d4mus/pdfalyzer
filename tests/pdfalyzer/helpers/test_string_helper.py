from pdfalyzer.helpers.string_helper import (all_strings_are_same_ignoring_numbers, is_prefixed_by_any,
     has_a_common_substring, is_substring_of_longer_strings_in_list, replace_digits)

TEST_TITLE = "Jacques and Carl's Excellent Adventure"


def test_is_prefixed_by_any():
    assert is_prefixed_by_any(TEST_TITLE, ['Lacan', 'Jung', 'Freud']) is False
    assert is_prefixed_by_any(TEST_TITLE, ['Lacan', 'Jac', 'Freud']) is True


def test_replace_digits():
    assert replace_digits('abcd') == 'abcd'
    assert replace_digits('a1b2c3d4e5f6') == 'axbxcxdxexfx'


def test_all_strings_are_same_ignoring_numbers():
    assert not all_strings_are_same_ignoring_numbers(['nasir', 'jones'])
    assert all_strings_are_same_ignoring_numbers(['ny_state_of_9_mind', 'ny_state_of_5_mind'])


def test_is_substring_of_longer_strings_in_list():
    assert not is_substring_of_longer_strings_in_list('blah', ['blimp', 'blew', 'ruby'])
    assert is_substring_of_longer_strings_in_list('goforit', ['goforit', 'agoforitnow', 'goforitnowdww'])


def test_has_a_common_substring():
    assert not has_a_common_substring(['blimp', 'blew', 'ruby'])
    assert has_a_common_substring(['blimp', 'blimpiest', 'it_is_blimpiest_out'])
