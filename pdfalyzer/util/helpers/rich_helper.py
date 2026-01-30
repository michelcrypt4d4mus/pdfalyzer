"""
Functions for miscellaneous Rich text/string pretty printing operations.
"""
from rich.panel import Panel
from rich.padding import Padding
from rich.text import Text
from yaralyzer.output.console import console

ARROW_BULLET = '➤ '


def attention_getting_panel(text: Text, title: str, style: str = 'white on red') -> Padding:
    p = Panel(text, padding=(2), title=title, style=style)
    return Padding(p, pad=(1, 10, 2, 10))


def bullet_text(msg: str | Text, style: str = '') -> Text:
    if isinstance(msg, str):
        msg = Text(msg, style=style)

    return Text(ARROW_BULLET).append(msg)


def comma_join_txt(text_objs: list[Text]) -> Text:
    return Text(", ").join(text_objs)


def error_text(text: str | Text) -> Text:
    msg = Text('').append(f"ERROR", style='bright_red').append(": ")

    if isinstance(text, Text):
        return msg + text
    else:
        return msg.append(text)


def indented_bullet(msg: str | Text, style: str = '') -> Text:
    return Text('  ') + bullet_text(msg, style)


def indent_padding(indent: int) -> tuple[int, int, int, int]:
    return (0, 0, 0, indent)


def mild_warning(msg: str) -> None:
    console.print(indented_bullet(Text(msg, style='color(228) dim')))


def number_and_pct(_number: int, total: int, digits: int = 1) -> Text:
    """Return e.g. '8 (80%)'."""
    return Text(str(_number), style='bright_white').append_text(pct_txt(_number, total, digits))


def pct_txt(_number: int, total: int, digits: int = 1) -> Text:
    """Return nicely formatted percentage, e.g. '(80%)'."""
    pct = (100 * float(_number) / float(total)).__round__(digits)
    return Text(f"({pct}%)", style='blue')


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


def vertically_padded_panel(title, **kwargs) -> Padding:
    # kwargs['expand'] = False if kwargs.get('expand') is None else kwargs['expand']
    kwargs['style'] = kwargs.get('style', 'reverse')
    kwargs['width'] = kwargs.get('width', 70)
    return Padding(Panel(title, **kwargs), (2, 0, 1, 0))
