"""
Class to smooth some of the rough edges around the dicts returned by chardet.detect_all()
"""
from typing import Any

from rich.text import Text

from pdfalyzer.detection.constants.character_encodings import ENCODING
from pdfalyzer.helpers.rich_text_helper import (DIM_COUNTRY_THRESHOLD, console, meter_style,
     prefix_with_plain_text_obj)

CONFIDENCE = 'confidence'
LANGUAGE = 'language'


class EncodingAssessment:
    def __init__(self, assessment: dict) -> None:
        self.assessment = assessment
        self.encoding = assessment[ENCODING].lower()
        self.encoding_text = Text(self.encoding, 'encoding.header')
        self.language = self._get_dict_empty_value_as_None(LANGUAGE)
        self.language_text = None if self.language is None else Text(self.language, 'encoding.language')

        # Shift confidence from 0-1.0 scale to 0-100.0 scale
        confidence = self._get_dict_empty_value_as_None(CONFIDENCE) or 0.0
        assert isinstance(confidence, float)
        self.confidence = 100.0 * confidence
        self.confidence_text = prefix_with_plain_text_obj(f"{round(self.confidence, 1)}%", style=meter_style(self.confidence))

        # Pair the language name with the encoding name into one Text obj
        if self.language is not None:
            dim = 'dim' if confidence < DIM_COUNTRY_THRESHOLD else ''
            self.encoding_text.append(f" ({self.language.title()})", style=f"color(23) {dim}")

    @classmethod
    def dummy_encoding_assessment(cls, encoding) -> 'EncodingAssessment':
        """Generate an empty EncodingAssessment to use as a dummy when chardet gives us nothing"""
        assessment = cls({ENCODING: encoding, 'confidence': 0.0})
        assessment.confidence_text = Text('none', 'no_attempt')
        return assessment

    def __rich__(self) -> Text:
        return Text('<Chardet(', 'white') + self.encoding_text + Text(':') + self.confidence_text + Text('>')

    def __str__(self) -> str:
        return self.__rich__().plain

    def _get_dict_empty_value_as_None(self, key: str) -> Any:
        """Return None if the value at :key is an empty string, empty list, etc."""
        value = self.assessment.get(key)

        if isinstance(value, (dict, list, str)) and len(value) == 0:
            return None
        else:
            return value
