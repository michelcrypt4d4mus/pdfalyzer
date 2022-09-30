"""
Count the Javascript (at least the 3+ letter words, record big matches
"""
from os import path
import re

from lib.config import PdfalyzerConfig
from lib.detection.constants.javascript_reserved_keywords import JAVASCRIPT_RESERVED_KEYWORDS
from lib.helpers.file_helper import load_word_list, timestamp_for_filename
from lib.helpers.string_helper import count_regex_matches_in_text
from lib.util.filesystem_awareness import PROJECT_DIR


JS_KEYWORDS_3_OR_MORE_LETTERS = [kw for kw in JAVASCRIPT_RESERVED_KEYWORDS if len(kw) > 2]
JS_KEYWORD_REGEX = re.compile('|'.join(JS_KEYWORDS_3_OR_MORE_LETTERS))


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
        return path.join(PdfalyzerConfig.LOG_DIR, f"{cls}_{timestamp_for_filename()}.log")
