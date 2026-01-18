import pytest

from pdfalyzer.font_info import FontInfo, flag_strings


@pytest.fixture
def embedded_font(attachment_pdf_pdfalyzer) -> FontInfo:
    return attachment_pdf_pdfalyzer.font_infos[0]


def test_font_extraction(attachment_pdf_pdfalyzer, embedded_font):
    assert len(attachment_pdf_pdfalyzer.font_infos) == 3
    assert embedded_font._first_and_last_char() == [67, 122]
    assert embedded_font.flags == 70
    assert embedded_font._flag_names() == ['serif', 'symbolic', 'italic']


def test_flag_strings(attachment_pdf_pdfalyzer):
    assert flag_strings(262178) == ['serif', 'nonsymbolic', 'forcebold']
