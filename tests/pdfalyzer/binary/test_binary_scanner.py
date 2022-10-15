def test_quote_extraction_methods(font_info):
    _check_matches(font_info.binary_scanner.extract_backtick_quoted_bytes, 163, 52840)


# def test_front_slash_quoted_bytes_extraction(font_info):
#     _check_matches(font_info.binary_scanner.extract_front_slash_quoted_bytes, 756, 167814)


def test_extract_guillemet(font_info):
    _check_matches(font_info.binary_scanner.extract_guillemet_quoted_bytes, 59, 78763)


def _check_matches(match_iterator, expected_matches: int, expected_bytes: int) -> None:
    quoted_bytes_found = 0
    quoted_sections_found = 0

    for quoted_bytes, _decoder in match_iterator():
        quoted_bytes_found += quoted_bytes.match_length
        quoted_sections_found += 1

    print(f"sections: {quoted_sections_found}, bytes: {quoted_bytes_found}")
    assert quoted_sections_found == expected_matches
    assert quoted_bytes_found == expected_bytes
