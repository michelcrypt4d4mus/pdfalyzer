from os import environ

from lib.config import is_env_var_set_and_not_false
from lib.helpers.dict_helper import get_dict_key_by_value

ENV_VAR_NAME = 'THE_WORLD_IS_YOURS'


def test_get_dict_key_by_value():
    arr = [1, 2, 3]
    hsh = {'a': 1, 'b': b'BYTES', 1: arr}
    assert get_dict_key_by_value(hsh, 1) == 'a'
    assert get_dict_key_by_value(hsh, b'BYTES') == 'b'
    assert get_dict_key_by_value(hsh, arr) == 1


def test_is_env_var_set_and_not_false():
    # Not set
    assert is_env_var_set_and_not_false(ENV_VAR_NAME) == False

    # Set to empty string
    environ[ENV_VAR_NAME] = ''
    assert is_env_var_set_and_not_false(ENV_VAR_NAME) == False

    # Set to FALSE
    environ[ENV_VAR_NAME] = 'FALSE'
    assert is_env_var_set_and_not_false(ENV_VAR_NAME) == False

    # Set to anything else
    environ[ENV_VAR_NAME] = 'FLASER'
    assert is_env_var_set_and_not_false(ENV_VAR_NAME) == True
