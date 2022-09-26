"""
Count the Javascript (at least the 3+ letter words, record big matches
"""
from os import path
import re

from lib.helpers.file_helper import load_word_list, timestamp_for_filename
from lib.helpers.string_helper import count_regex_matches_in_text
from lib.util.filesystem_awareness import PROJECT_DIR
from lib.util.logging import LOG_DIR

JS_KEYWORDS_FILE = path.join(PROJECT_DIR, 'config', 'javascript_reserved_keywords.txt')
JS_KEYWORDS_LIST = load_word_list(JS_KEYWORDS_FILE)
JS_KEYWORDS_3_OR_MORE_LETTERS = [kw for kw in JS_KEYWORDS_LIST if len(kw) > 2]
JS_KEYWORD_REGEX = re.compile('|'.join(JS_KEYWORDS_3_OR_MORE_LETTERS))
JS_KEYWORD_ALERT_THRESHOLD = 2


class JavascriptHunter:
    @classmethod
    def count_js_keywords_in_text(cls, text: str) -> int:
        return count_regex_matches_in_text(JS_KEYWORD_REGEX, text)

    @classmethod
    def js_keyword_matches(cls, text: str) -> [str]:
        return JS_KEYWORD_REGEX.findall(text)

    @classmethod
    def javascript_match_log_file_path(cls) -> str:
        """Get a log file unique to this run"""
        return path.join(LOG_DIR, f"{cls}_{timestamp_for_filename()}.log")
