"""
Deprecated pre-tree, more rawformat reader.
"""
from io import StringIO

from PyPDF2.generic import ArrayObject, DictionaryObject, IndirectObject
from rich.console import Console
from rich.markup import escape

from pdfalyzer.helpers.string_helper import pp, pypdf_class_name, INDENT_DEPTH


INDENT_SPACES = ' ' * INDENT_DEPTH
INDENT_JOIN = "\n" + INDENT_SPACES
VALUE_WIDTH = 30

TRUNCATABLE_TYPES = (ArrayObject, DictionaryObject, list, dict)
TRUNCATE_MULTILINE = 25


# Truncates large pretty print output
def pretty_print_list_or_dict(obj):
    if isinstance(obj, list) and len(obj) > TRUNCATE_MULTILINE:
        truncate_msg = f'(truncated {len(obj) - TRUNCATE_MULTILINE} of {len(obj)} rows)'
        obj = obj[:TRUNCATE_MULTILINE] + [truncate_msg]

    pretty_str = pp.pformat(obj)

    if pretty_str.count("\n") > TRUNCATE_MULTILINE:
        pretty_str = "\n".join(pretty_str.split("\n")[:TRUNCATE_MULTILINE])
        pretty_str += f"{INDENT_JOIN}(...truncated...)"

    return pretty_str


def print_all_props(pdf_obj, console, verbose=False, indent=''):
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
        pretty_str = indent_join.join(pretty_print_list_or_dict(v).split("\n"))
        console.print(indent + f" {k}  ({pypdf_class_name(v)})    {indent_join}{pretty_str}")


# Prints with a header of your choosing
def print_with_header(obj, header, depth=0, print_props=True, print_header=True):
    console = Console(file=StringIO())
    box_horiz = '-' * (len(header) + 4)
    box_elements = [box_horiz, f'| {escape(header)} |', box_horiz]
    indent = INDENT_SPACES * depth
    indent_join = "\n" + indent

    if print_header:
        console.print(f'{indent}' + indent_join.join(box_elements))

        if print_props:
            print_all_props(obj, console, indent=indent)

    console.print('')
    return console.file.getvalue()
