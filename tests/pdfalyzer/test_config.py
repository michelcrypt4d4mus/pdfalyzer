from os import environ
from pdfalyzer.config import PYTEST_FLAG, is_env_var_set_and_not_false

ENV_VAR_NAME = 'THE_WORLD_IS_YOURS'


def test_is_env_var_set_and_not_false():
    # Not set
    assert is_env_var_set_and_not_false(ENV_VAR_NAME) is False

    # Should be set by conftest
    assert is_env_var_set_and_not_false(PYTEST_FLAG) is True

    # Set to empty string
    environ[ENV_VAR_NAME] = ''
    assert is_env_var_set_and_not_false(ENV_VAR_NAME) is False

    # Set to FALSE
    environ[ENV_VAR_NAME] = 'FALSE'
    assert is_env_var_set_and_not_false(ENV_VAR_NAME) is False

    # Set to anything else
    environ[ENV_VAR_NAME] = 'FLASER'
    assert is_env_var_set_and_not_false(ENV_VAR_NAME) is True
