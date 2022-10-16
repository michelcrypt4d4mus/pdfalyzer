from pdfalyzer.helpers.pdf_object_helper import (have_same_non_digit_chars,
     has_indeterminate_prefix)


def test_has_indeterminate_prefix():
    assert not has_indeterminate_prefix('/Dobbs')
    assert has_indeterminate_prefix('/Destroy')


def test_have_same_non_digit_chars():
    assert not have_same_non_digit_chars(['nasir', 'jones'])
    assert have_same_non_digit_chars(['ny_state_of_9_mind', 'ny_state_of_5_mind'])
