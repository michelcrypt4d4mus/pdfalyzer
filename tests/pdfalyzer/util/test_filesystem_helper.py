from pathlib import Path

from pdfalyzer.util.helpers.filesystem_helper import replace_extension


def test_replace_extension():
    assert replace_extension('/nas/illmatic.pdf', 'txt') == Path('/nas/illmatic.txt')
    assert replace_extension('/nas/illmatic.pdf', '.txt') == Path('/nas/illmatic.txt')
