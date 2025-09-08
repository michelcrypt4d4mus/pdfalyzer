"""
Functions for miscellaneous Rich text/string pretty printing operations.
"""
from sys import stderr
from typing import List, Optional, Union

from pypdf.generic import PdfObject
from rich.console import Console
from rich.panel import Panel
from rich.padding import Padding
from rich.text import Text
from yaralyzer.output.rich_console import console

from pdfalyzer.helpers.pdf_object_helper import pypdf_class_name
from pdfalyzer.output.styles.node_colors import get_label_style, get_class_style_italic

ARROW_BULLET = '➤ '

# Usually we use the yaralyzer console but that has no highlighter
pdfalyzer_console = Console(color_system='256')
stderr_console = Console(color_system='256', file=stderr)


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


def indented_bullet(msg: Union[str, Text], style: Optional[str] = None) -> Text:
    return Text('  ') + bullet_text(msg, style)


def bullet_text(msg: Union[str, Text], style: Optional[str] = None) -> Text:
    if isinstance(msg, str):
        msg = Text(msg, style=style)

    return Text(ARROW_BULLET).append(msg)


def mild_warning(msg: str) -> None:
    console.print(indented_bullet(Text(msg, style='mild_warning')))


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
    """Return nicely formatted percentage, e.g. '(80%)'."""
    pct = (100 * float(_number) / float(total)).__round__(digits)
    return Text(f"({pct}%)", style='blue')


def warning_text(text: Union[str, Text]) -> Text:
    msg = Text('').append(f"WARNING", style='bright_yellow').append(": ")

    if isinstance(text, Text):
        return msg + text
    else:
        return msg.append(text)


def error_text(text: Union[str, Text]) -> Text:
    msg = Text('').append(f"ERROR", style='bright_red').append(": ")

    if isinstance(text, Text):
        return msg + text
    else:
        return msg.append(text)


def attention_getting_panel(text: Text, title: str, style: str = 'white on red') -> Padding:
    p = Panel(text, padding=(2), title=title, style=style)
    return Padding(p, pad=(1, 10, 2, 10))


def print_error(text: Union[str, Text]) -> Text:
    console.print(error_text(text))
