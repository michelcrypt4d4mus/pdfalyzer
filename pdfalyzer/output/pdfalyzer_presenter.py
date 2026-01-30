"""
Handles formatting of console text output for Pdfalyzer class.
"""
from collections import defaultdict, namedtuple
from dataclasses import dataclass, field
from typing import Callable

import yara
from anytree import LevelOrderIter, RenderTree, SymlinkNode
from anytree.render import DoubleStyle
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from yaralyzer.config import YaralyzerConfig
from yaralyzer.output.console import console
from yaralyzer.output.file_hashes_table import bytes_hashes_table
from yaralyzer.output.theme import BYTES_HIGHLIGHT
from yaralyzer.util.exceptions import print_fatal_error
from yaralyzer.util.helpers.rich_helper import DEFAULT_TABLE_OPTIONS, size_in_bytes_text
from yaralyzer.yara.error import yara_error_msg
from yaralyzer.yaralyzer import Yaralyzer

from pdfalyzer.binary.binary_scanner import BinaryScanner
from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.decorators.pdf_tree_node import DECODE_FAILURE_LEN, PdfTreeNode
from pdfalyzer.detection.yaralyzer_helper import get_bytes_yaralyzer, get_file_yaralyzer
from pdfalyzer.output.layout import (print_fatal_error_panel, print_section_header, print_section_subheader,
     print_section_sub_subheader)
from pdfalyzer.output.tables.decoding_stats_table import build_decoding_stats_table
from pdfalyzer.output.theme import get_label_style
from pdfalyzer.pdfalyzer import Pdfalyzer
from pdfalyzer.util.adobe_strings import DANGEROUS_PDF_KEYS, FALSE, TRUE
from pdfalyzer.util.helpers.collections_helper import safe_json
from pdfalyzer.util.helpers.string_helper import root_address
from pdfalyzer.util.logging import highlight, log

SymlinkRepresentation = namedtuple('SymlinkRepresentation', ['text', 'style'])

COUNT_LABEL_STYLE = 'navajo_white3'
HIGHLIGHT_IF = ['http', FALSE, TRUE]

count_label = lambda count_type: f"{count_type} count"
count_txt = lambda count_type: Text(count_label(count_type), style=COUNT_LABEL_STYLE)
failed_count_msg = lambda count_type: f"Failed to get {count_label(count_type)}!"


@dataclass
class PdfalyzerPresenter:
    """
    Handles formatting of console text output for Pdfalyzer class.

    Attributes:
        pdfalyzer (Pdfalyzer): Pdfalyzer for a given PDF file
        yaralyzer (Yaralyzer): Yaralyzer for a given PDF file
    """
    pdfalyzer: Pdfalyzer
    yaralyzer: Yaralyzer = field(init=False)

    def __post_init__(self):
        self.yaralyzer = get_file_yaralyzer(self.pdfalyzer.pdf_path)

    def print_everything(self) -> None:
        """Print every kind of analysis on offer to Rich console."""
        self.print_document_info()
        self.print_summary()
        self.print_tree()
        self.print_rich_table_tree()
        self.print_font_info()
        self.print_yara_results()
        self.print_non_tree_relationships()

    def print_document_info(self) -> None:
        """Print the embedded document info (author, timestamps, version, etc)."""
        print_section_header(f'Document Info for {self.pdfalyzer.pdf_basename}')
        console.print(self._metadata_table())
        console.line()
        console.print(bytes_hashes_table(self.pdfalyzer.pdf_bytes, self.pdfalyzer.pdf_basename))
        console.line()
        console.print(self._stream_objects_table())
        console.line()

    def print_tree(self) -> None:
        """Print the simple view of the PDF tree."""
        print_section_header(f'Simple tree view of {self.pdfalyzer.pdf_basename}')

        for pre, _fill, node in RenderTree(self.pdfalyzer.pdf_tree, style=DoubleStyle):
            if isinstance(node, SymlinkNode):
                symlink_rep = self._get_symlink_representation(node.parent, node)
                console.print(pre + f"[{symlink_rep.style}]{symlink_rep.text}[/{symlink_rep.style}]")
            else:
                console.print(Text(pre) + node.__rich__())

        console.print("\n\n")

    def print_rich_table_tree(self) -> None:
        """Print the rich view of the PDF tree."""
        print_section_header(f'Rich tree view of {self.pdfalyzer.pdf_basename}')
        console.print(self._generate_rich_tree(self.pdfalyzer.pdf_tree))

    def print_summary(self) -> None:
        """Print node type counts and so on."""
        print_section_header(f'PDF Node Summary for {self.pdfalyzer.pdf_basename}')
        console.print_json(safe_json(self._analyze_tree()), sort_keys=True)

    def print_font_info(self, font_idnum=None) -> None:
        """Print informatin about all fonts that appear in this PDF."""
        print_section_header(f'{len(self.pdfalyzer.font_infos)} fonts found in {self.pdfalyzer.pdf_basename}')

        if self.pdfalyzer.font_info_extraction_error:
            print_fatal_error(f"Failed to extract font information (error: {self.pdfalyzer.font_info_extraction_error})")

        for font_info in [fi for fi in self.pdfalyzer.font_infos if font_idnum is None or font_idnum == fi.idnum]:
            font_info.print_summary()

    def print_streams_analysis(self, idnum: int | None = None) -> None:
        """
        For each binary stream,
          1. Scan decompressed binary with YARA rules we applied to whole PDF (the ones in pdfalyzer/yara_rules/)
          2. Check for (and force decode) dangerous PDF instructions like /JavaScript and /OpenAction
          3. Check for (and force decode) any BOMs (byte order marks)
          4. Check for (and force decode) any sequences of bytes between quotes
        """
        print_section_header(f'Binary Stream Analysis / Extraction')
        console.print(self._stream_objects_table())

        for node in [n for n in self.pdfalyzer.stream_nodes() if idnum is None or idnum == n.idnum]:
            node_stream_bytes = node.stream_data

            if node_stream_bytes is None or node.stream_length == 0:
                print_section_sub_subheader(f"{node} stream has length 0", style='dim')
                continue

            if not isinstance(node_stream_bytes, bytes):
                log.warning(f"Stream in {node} is not bytes, it's {type(node.stream_data).__name__}. Will " \
                             "reencode for YARA but they may not be the same bytes as the original stream!")
                node_stream_bytes = node_stream_bytes.encode()

            console.line()
            print_section_subheader(f"{escape(str(node))} Summary and Analysis", style=f"{BYTES_HIGHLIGHT} reverse")
            binary_scanner = BinaryScanner(node_stream_bytes, node)
            console.print(bytes_hashes_table(binary_scanner.bytes))
            binary_scanner.print_stream_preview()
            binary_scanner.check_for_dangerous_instructions()

            if not PdfalyzerConfig.args.suppress_boms:
                binary_scanner.check_for_boms()

            if not YaralyzerConfig.args.suppress_decodes_table:
                binary_scanner.force_decode_quoted_bytes()
                console.line(2)
                console.print(build_decoding_stats_table(binary_scanner), justify='center')

    def print_yara_results(self) -> None:
        """Scan the main PDF and each individual binary stream in it with yara_rules/*.yara files."""
        try:
            print_section_header(f"YARA Scan of PDF rules for '{self.pdfalyzer.pdf_basename}'")
            YaralyzerConfig.args._yaralyzer_standalone_mode = True  # TODO: 'standalone mode' like this kind of sucks
            self.yaralyzer.yaralyze()
        except yara.Error as e:
            console.print_exception()
            print_fatal_error_panel(yara_error_msg(e))
            return

        YaralyzerConfig.args._yaralyzer_standalone_mode = False
        console.line(2)

        for node in self.pdfalyzer.stream_nodes():
            if node.stream_length == DECODE_FAILURE_LEN:
                log.warning(f"{node} binary stream could not be extracted")
            elif node.stream_length == 0 or node.stream_data is None:
                log.debug(f"No binary to scan for {node}")
            else:
                get_bytes_yaralyzer(node.stream_data, str(node)).yaralyze()
                console.line(2)

    def print_non_tree_relationships(self) -> None:
        """Print the inter-node, non-tree relationships for all nodes in the tree. Debugging method."""
        print_section_header(f"Non-tree Relationships for '{self.pdfalyzer.pdf_basename}'")

        for node in LevelOrderIter(self.pdfalyzer.pdf_tree):
            if len(node.non_tree_relationships) == 0:
                continue

            console.line(2)
            console.print(Panel(f"Non tree relationships for {node}", expand=False, **DEFAULT_TABLE_OPTIONS))
            node.print_non_tree_relationships()

    def _analyze_tree(self) -> dict:
        """Generate a dict with some basic data points about the PDF tree"""
        keys_encountered = defaultdict(int)
        node_count = 0
        node_labels = defaultdict(int)
        node_types = defaultdict(int)
        pdf_object_types = defaultdict(int)

        for node in self.pdfalyzer.node_iterator():
            node_count += 1
            node_labels[node.label] += 1
            node_types[node.type] += 1
            pdf_object_types[type(node.obj).__name__] += 1

            if isinstance(node.obj, dict):
                for k in node.obj.keys():
                    keys_encountered[k] += 1

        return {
            'keys_encountered': keys_encountered,
            'node_count': node_count,
            'node_labels': node_labels,
            'node_types': node_types,
            'pdf_object_types': pdf_object_types,
        }

    def _generate_rich_tree(self, node: PdfTreeNode, tree: Tree | None = None) -> Tree:
        """Recursively generates a rich.tree.Tree object from 'node' and its children."""
        tree = tree or Tree(node.as_tree_node_table(self.pdfalyzer))

        for child in node.children:
            if isinstance(child, SymlinkNode):
                symlink_rep = self._get_symlink_representation(node, child)
                tree.add(Panel(symlink_rep.text, style=symlink_rep.style, expand=False, **DEFAULT_TABLE_OPTIONS))
                continue

            child_branch = tree.add(child.as_tree_node_table(self.pdfalyzer))
            self._generate_rich_tree(child, child_branch)

        return tree

    def _get_symlink_representation(self, from_node: PdfTreeNode, to_node: SymlinkNode) -> SymlinkRepresentation:
        """Returns a tuple (symlink_text, style) that can be used for pretty printing, tree creation, etc"""
        reference_key = str(to_node.address_of_this_node_in_other(from_node))
        pdf_instruction = root_address(reference_key)  # In case we ended up with a [0] or similar

        if pdf_instruction in DANGEROUS_PDF_KEYS:
            symlink_style = 'red_alert'
        else:
            symlink_style = get_label_style(to_node.label) + ' dim'

        symlink_str = f"{escape(reference_key)} [bright_white]=>[/bright_white]"
        symlink_str += f" {escape(str(to_node.target))} [grey](Non Child Reference)[/grey]"
        return SymlinkRepresentation(symlink_str, symlink_style)

    def _stream_objects_table(self) -> Table:
        """Build a table of stream objects and their lengths."""
        table = Table(
            'Stream Length',
            'Node',
            title=' Embedded Streams',
            title_style='grey',
            title_justify='left',
            **DEFAULT_TABLE_OPTIONS
        )

        table.columns[0].justify = 'right'

        for node in self.pdfalyzer.stream_nodes():
            table.add_row(size_in_bytes_text(node.stream_length), node.__rich__())

        return table

    def _metadata_table(self) -> Table:
        """Build a table of metadata extracted from/computed about the PDF."""
        table = Table(
            header_style='bold',
            title=' Metadata',
            title_style='grey',
            title_justify='left',
            **DEFAULT_TABLE_OPTIONS
        )

        table.add_column('Property', justify='right')
        table.add_column('Value', min_width=40)

        if (metadata := self.pdfalyzer.pdf_reader.metadata or {}):
            for k, v in metadata.items():
                v = highlight(str(v)) if isinstance(v, str) and any(hif in v for hif in HIGHLIGHT_IF) else str(v)
                table.add_row(Text(k, style='wheat4'), v)
        else:
            table.add_row('', Text('(no formal metadata found in file)'), style='dim italic')

        def add_count_row(count_type: str, count_fxn: Callable[[], int]) -> None:
            row_label = count_txt(count_type)

            try:
                table.add_row(row_label, highlight(f"{count_fxn():,}"))
            except Exception as e:
                fail_msg = failed_count_msg(count_type)
                log.error(f"{fail_msg} {e}")
                table.add_row(row_label, Text(fail_msg, style='bright_red'))

        add_count_row('page', lambda: len(self.pdfalyzer.pdf_reader.pages))
        add_count_row('images', lambda: sum([len(p.images) for p in self.pdfalyzer.pdf_reader.pages]))
        add_count_row('revision', lambda: self.pdfalyzer.max_generation)
        return table
