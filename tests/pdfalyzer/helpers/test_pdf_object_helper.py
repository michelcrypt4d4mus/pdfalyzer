from pdfalyzer.util.adobe_strings import has_indeterminate_prefix


def test_has_indeterminate_prefix():
    assert not has_indeterminate_prefix('/Dobbs')
    assert has_indeterminate_prefix('/Destroy')
