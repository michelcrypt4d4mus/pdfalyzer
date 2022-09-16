from distutils.command.clean import clean
from lib.util.string_utils import clean_byte_string


class TestStringUtils:
    def test_clean_byte_string(self):
        assert clean_byte_string(b'\xbbJS') == '\\xbbJS'
