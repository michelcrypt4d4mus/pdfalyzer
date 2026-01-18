
def test_font_extraction(attachment_pdf_pdfalyzer):
    assert len(attachment_pdf_pdfalyzer.font_infos) == 3
    font1 = attachment_pdf_pdfalyzer.font_infos[0]
    assert font1._first_and_last_char() == [67, 122]
