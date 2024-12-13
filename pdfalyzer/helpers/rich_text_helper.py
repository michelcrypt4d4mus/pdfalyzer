"""
Functions for miscellaneous Rich text/string operations.
"""
from typing import List, Union

from pypdf.generic import PdfObject
from rich.console import Console
from rich.highlighter import RegexHighlighter, JSONHighlighter
from rich.text import Text
from yaralyzer.output.rich_console import console

from pdfalyzer.helpers.pdf_object_helper import pypdf_class_name
from pdfalyzer.output.styles.node_colors import get_label_style, get_class_style_italic

# Usually we use the yaralyzer console but that has no highlighter
pdfalyzer_console = Console(color_system='256')


def print_highlighted(msg: Union[str, Text], **kwargs) -> None:
    """Print 'msg' with Rich highlighting."""
    pdfalyzer_console.print(msg, highlight=True, **kwargs)


def quoted_text(
        _string: str,
        style: str = '',
        quote_char_style: str = 'white',
        quote_char: str = "'"
    ) -> Text:
    """Wrap _string in 'quote_char'. Style 'quote_char' with 'quote_char_style'."""
    quote_char_txt = Text(quote_char, style=quote_char_style)
    txt = quote_char_txt + Text(_string, style=style) + quote_char_txt
    txt.justify = 'center'
    return txt


def node_label(idnum: int, label: str, pdf_object: PdfObject, underline: bool = True) -> Text:
    """Colored text representation of a PDF node. Example: <5:FontDescriptor(Dictionary)>."""
    text = Text('<', style='white')
    text.append(f'{idnum}', style='bright_white')
    text.append(':', style='white')
    text.append(label[1:], style=f"{get_label_style(label)} {'underline' if underline else ''} bold")
    text.append('(', style='white')
    text.append(pypdf_class_name(pdf_object), style=get_class_style_italic(pdf_object))
    text.append(')', style='white')
    text.append('>')
    return text


def comma_join_txt(text_objs: List[Text]) -> Text:
    return Text(", ").join(text_objs)


def number_and_pct(_number: int, total: int, digits: int = 1) -> Text:
    """Return e.g. '8 (80%)'."""
    return Text(str(_number), style='bright_white').append_text(pct_txt(_number, total, digits))


def pct_txt(_number: int, total: int, digits: int = 1) -> Text:
    pct = (100 * float(_number) / float(total)).__round__(digits)
    return Text(f"({pct}%)", style='blue')
