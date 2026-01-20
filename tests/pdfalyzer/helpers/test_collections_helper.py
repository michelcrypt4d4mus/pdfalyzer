from pdfalyzer.helpers.collections_helper import get_dict_key_by_value


def test_get_dict_key_by_value():
    arr = [1, 2, 3]
    hsh = {'a': 1, 'b': b'BYTES', 1: arr}
    assert get_dict_key_by_value(hsh, 1) == 'a'
    assert get_dict_key_by_value(hsh, b'BYTES') == 'b'
    assert get_dict_key_by_value(hsh, arr) == 1
