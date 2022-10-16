"""
Functions for miscellaneous Rich text/string operations.
"""
from PyPDF2.generic import PdfObject
from rich.text import Text

from pdfalyzer.helpers.pdf_object_helper import pypdf_class_name
from pdfalyzer.output.styles.node_colors import get_label_style, get_node_type_style


def quoted_text(
        _string: str,
        style: str = '',
        quote_char_style: str = 'white',
        quote_char: str = "'"
    ) -> Text:
    """Wrap _string in 'quote_char'. Style 'quote_char' with 'quote_char_style'."""
    quote_char_txt = Text(quote_char, style=quote_char_style)
    txt = quote_char_txt.append(_string, style=style).append_text(quote_char_txt)
    txt.justify = 'center'
    return txt


def node_label(idnum: int, label: str, pdf_object: PdfObject) -> Text:
    """Colored text representation of a PDF node. Example: <5:FontDescriptor(Dictionary)>."""
    text = Text('<', style='white')
    text.append(f'{idnum}', style='bright_white')
    text.append(':', style='white')
    text.append(label[1:], style=f'{get_label_style(label)} underline bold')
    text.append('(', style='white')
    text.append(pypdf_class_name(pdf_object), style=get_node_type_style(pdf_object))
    text.append(')', style='white')
    text.append('>')
    return text
