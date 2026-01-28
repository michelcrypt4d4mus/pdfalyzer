"""
Deprecated old, pre-tree, more rawformat reader. Only used for debugging these days.
# TODO: move methods to pdf_object_hlper.py
"""
from io import StringIO

from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, PdfObject
from rich.console import Console
from rich.markup import escape
from yaralyzer.output.console import console_width

from pdfalyzer.util.helpers.pdf_object_helper import describe_obj, pypdf_class_name
from pdfalyzer.util.helpers.string_helper import pp, INDENT_DEPTH

INDENT_SPACES = ' ' * INDENT_DEPTH
INDENT_JOIN = "\n" + INDENT_SPACES
VALUE_WIDTH = 30
OBJ_DUMP_WIDTH = console_width() - len('                    WARNING ')

TRUNCATABLE_TYPES = (ArrayObject, DictionaryObject, list, dict)
TRUNCATE_MULTILINE = 25


def highlighted_raw_pdf_obj_str(obj: PdfObject, header: str = '', depth=0) -> str:
    """Created a formatted, color highlighted string to display properties of a Pdf object."""
    header += f" {describe_obj(obj)}"
    console = Console(file=StringIO(), width=OBJ_DUMP_WIDTH)
    box_horiz = '-' * (len(header) + 4)
    box_elements = [box_horiz, f'| {escape(header)} |', box_horiz]
    indent = INDENT_SPACES * depth
    indent_join = "\n" + indent
    console.print(f'{indent}' + indent_join.join(box_elements))
    _print_all_props(obj, console, indent=indent)
    console.line()
    return console.file.getvalue()


# Truncates large pretty print output
def _pretty_print_list_or_dict(obj: PdfObject) -> str:
    if isinstance(obj, list) and len(obj) > TRUNCATE_MULTILINE:
        truncate_msg = f'(truncated {len(obj) - TRUNCATE_MULTILINE} of {len(obj)} rows)'
        obj = obj[:TRUNCATE_MULTILINE] + [truncate_msg]

    pretty_str = pp.pformat(obj)

    if pretty_str.count("\n") > TRUNCATE_MULTILINE:
        pretty_str = "\n".join(pretty_str.split("\n")[:TRUNCATE_MULTILINE])
        pretty_str += f"{INDENT_JOIN}(...truncated...)"

    return pretty_str


def _print_all_props(pdf_obj: PdfObject, console: Console, verbose=False, indent='') -> None:
    """Print properties of a PdfObject into the 'console' argument."""
    if 'keys' not in dir(pdf_obj):
        console.print('* ' + pp.pformat(pdf_obj))
        return

    # Save large object output for last
    large_print_jobs = {}

    for k, v in pdf_obj.items():
        if (verbose and isinstance(v, IndirectObject)):
            v = v.get_object()

        k = pp.pformat(k) if isinstance(k, tuple) else k
        pretty_str = pp.pformat(v)

        if (len(pretty_str) > VALUE_WIDTH and (isinstance(v, TRUNCATABLE_TYPES))):
            large_print_jobs[k] = v
            continue

        pretty_str = '{0: <20}{1: <{vwidth}}'.format(k, pretty_str, vwidth=VALUE_WIDTH)
        console.print(indent + ' {0: <66}{1: >20}'.format(pretty_str, pypdf_class_name(v)))

    for k, v in large_print_jobs.items():
        indent_join = INDENT_JOIN + indent
        pretty_str = indent_join.join(_pretty_print_list_or_dict(v).split("\n"))
        console.print(indent + f" {k}  ({pypdf_class_name(v)})    {indent_join}{pretty_str}")
