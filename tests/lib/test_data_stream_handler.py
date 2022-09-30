def test_quote_regex_iterator(analyzing_malicious_documents_pdfalyzer):
    font = next(fi for fi in analyzing_malicious_documents_pdfalyzer.font_infos if fi.idnum == 5)
    quoted_bytes_found = 0
    quoted_sections_found = 0

    for quoted_bytes in font.binary_scanner.extract_backtick_quoted_bytes():
        quoted_bytes_found += quoted_bytes.capture_len
        quoted_sections_found += 1

    print(f"sections: {quoted_sections_found}, bytes: {quoted_bytes_found}")
    assert quoted_sections_found == 141
    assert quoted_bytes_found == 71739
