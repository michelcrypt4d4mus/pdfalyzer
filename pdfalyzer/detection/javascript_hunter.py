"""
Count the Javascript (at least the 3+ letter words, record big matches
"""
from os import path
import re

from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.detection.constants.javascript_reserved_keywords import JAVASCRIPT_RESERVED_KEYWORDS
from pdfalyzer.helpers.string_helper import count_regex_matches_in_text

JS_KEYWORDS_3_OR_MORE_LETTERS = [kw for kw in JAVASCRIPT_RESERVED_KEYWORDS if len(kw) > 2]
JS_KEYWORD_REGEX = re.compile('|'.join(JS_KEYWORDS_3_OR_MORE_LETTERS))


class JavascriptHunter:
    @classmethod
    def count_js_keywords_in_text(cls, text: str) -> int:
        return count_regex_matches_in_text(JS_KEYWORD_REGEX, text)

    @classmethod
    def js_keyword_matches(cls, text: str) -> [str]:
        return JS_KEYWORD_REGEX.findall(text)
