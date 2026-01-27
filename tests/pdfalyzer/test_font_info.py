import pytest

from pdfalyzer.font_info import FontInfo
from pdfalyzer.pdfalyzer import Pdfalyzer

from ..conftest import FIXTURES_DIR


# Has a Type1 font with character map. PDF comes from pypdf repo.
@pytest.fixture(scope='session')
def attachment_pdf_pdfalyzer():
    return Pdfalyzer(FIXTURES_DIR.joinpath('attachment.pdf'))

# Has /Resources that is not an IndirectObject, also has multiple /DescendantFonts and /ObjStm
@pytest.fixture(scope='session')
def geobase_pdfalyzer():
    return Pdfalyzer(FIXTURES_DIR.joinpath('GeoBase_NHNC1_Data_Model_UML_EN.pdf'))


@pytest.fixture
def embedded_font(attachment_pdf_pdfalyzer) -> FontInfo:
    return attachment_pdf_pdfalyzer.font_infos[0]


def test_font_extraction(attachment_pdf_pdfalyzer, embedded_font, form_evince_pdfalyzer, geobase_pdfalyzer):
    assert len(attachment_pdf_pdfalyzer.font_infos) == 3
    assert embedded_font._first_and_last_char() == [67, 122]
    assert embedded_font.flags == 70
    assert embedded_font._flag_names() == ['serif', 'symbolic', 'italic']

    assert len(geobase_pdfalyzer.font_infos) == 16
    assert len(form_evince_pdfalyzer.font_infos) == 3  # Unplaced fonts
