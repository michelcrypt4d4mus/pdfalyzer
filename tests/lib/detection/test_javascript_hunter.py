from lib.detection.javascript_hunter import JavascriptHunter

TEST_STRING = 'export then gracefully exit before finally rising to the moon'


def test_count_js_keywords_in_text():
    assert JavascriptHunter.count_js_keywords_in_text(TEST_STRING) == 3


def test_js_keyword_matches():
    assert JavascriptHunter.js_keyword_matches(TEST_STRING) == ['export', 'for', 'final']
