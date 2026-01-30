"""
Regex patterns and a LogHighlighter that work with the rich.Highlighter approach of coloring
text output.
"""
import re

from rich.markup import escape
from rich.highlighter import ReprHighlighter
from rich.text import Text
from yaralyzer.util.logging import log_console

from pdfalyzer.util.helpers.collections_helper import prefix_keys
from pdfalyzer.util.helpers.rich_helper import vertically_padded_panel

PDF_OBJ_STYLE_PREFIX = 'pdf.'
PYPDF_LOG_PFX_PATTERN = r"\(pypdf\)"

# Styles
CHILD_STYLE = 'orange3 bold'
INDIRECT_OBJ_STYLE = 'light_coral'  # Formerly 'color(225)'
PARENT_STYLE = 'violet'
PDF_ARRAY_STYLE = 'color(143)'  # color(120)
PDF_DICTIONARY_STYLE = 'color(64)'

# Copied from https://rich.readthedocs.io/en/latest/_modules/rich/highlighter.html#Highlighter
# so we can get rid of a couple of the patterns we don't want.
DEFAULT_REPR_HIGHLIGHTER_PATTERNS = [
    r"(?P<tag_start><)(?P<tag_name>[-\w.:|]*)(?P<tag_contents>[\w\W]*)(?P<tag_end>>)",
    r'(?P<attrib_name>[\w_]{1,50})=(?P<attrib_value>"?[\w_]+"?)?',
    r"(?P<brace>[][{}()])",
    r"(?P<ipv4>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})",
    # r"(?P<ipv6>([A-Fa-f0-9]{1,4}::?){1,7}[A-Fa-f0-9]{1,4})",  # TODO: find a way to reenable this
    r"(?P<eui64>(?:[0-9A-Fa-f]{1,2}-){7}[0-9A-Fa-f]{1,2}|(?:[0-9A-Fa-f]{1,2}:){7}[0-9A-Fa-f]{1,2}|(?:[0-9A-Fa-f]{4}\.){3}[0-9A-Fa-f]{4})",
    r"(?P<eui48>(?:[0-9A-Fa-f]{1,2}-){5}[0-9A-Fa-f]{1,2}|(?:[0-9A-Fa-f]{1,2}:){5}[0-9A-Fa-f]{1,2}|(?:[0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4})",
    r"(?P<uuid>[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})",
    # r"(?P<call>[\w.]*?)\(",
    r"\b(?P<bool_true>True)\b|\b(?P<bool_false>False)\b|\b(?P<none>None)\b",
    r"(?P<ellipsis>\.\.\.)",
    r"(?P<number_complex>(?<!\w)(?:\-?[0-9]+\.?[0-9]*(?:e[-+]?\d+?)?)(?:[-+](?:[0-9]+\.?[0-9]*(?:e[-+]?\d+)?))?j)",
    r"(?P<number>(?<!\w)\-?[0-9]+\.?[0-9]*(e[-+]?\d+?)?\b|0x[0-9a-fA-F]*)",
    # r"(?P<path>\B(/[-\w._+]+)*\/)(?P<filename>[-\w._+]*)?",
    r"(?<![\\\w])(?P<str>b?'''.*?(?<!\\)'''|b?'.*?(?<!\\)'|b?\"\"\".*?(?<!\\)\"\"\"|b?\".*?(?<!\\)\")",
    r"(?P<url>(file|https|http|ws|wss)://[-0-9a-zA-Z$_+!`(),.?/;:&=%#~@]*)",
]

# Our custom log highlight patterns
LOG_HIGHLIGHT_PATTERNS = DEFAULT_REPR_HIGHLIGHTER_PATTERNS + [
    r"(?P<child>[cC]hild(ren)?)",
    r"(?P<indeterminate>[Ii]ndeterminate( ?[nN]odes?)?)",
    r"(?P<parent>[pP]arents?)",
    fr"(?P<pypdf_line>{PYPDF_LOG_PFX_PATTERN} .*)",
    fr"(?P<pypdf_prefix>{PYPDF_LOG_PFX_PATTERN})",
    r"(?P<relationship>[Rr]elationship( of)?)",
    r"(?P<relationship>via symlink|parent/child|child/parent)",
]

# Logger highlights
LOG_HIGHLIGHT_STYLES = {
    "child": CHILD_STYLE,
    "indeterminate": 'bright_black',
    "parent": PARENT_STYLE,
    "pypdf_line": "dim",
    "pypdf_prefix": "light_slate_gray",
    "relationship": 'light_pink4',
    # Overload default ReprHighlighter theme elements
    # 'call': 'magenta',
    'ipv4': 'cyan',
    # 'ipv6': 'cyan',
}


# Augment the standard ReprHighlighter
class LogHighlighter(ReprHighlighter):
    highlights: list[re.Pattern]

    @classmethod
    def get_style(cls, for_str: str) -> str:
        """Return the first style that matches the 'for_str'."""
        for highlight in cls.highlights:
            if (match := highlight.search(for_str)):
                return cls.base_style + next(k for k in match.groupdict().keys())

        return ''

    @classmethod
    def prefix_styles(cls, styles: dict[str, str]) -> dict[str, str]:
        """Prepend this highlighter's `base_style` to all keys in the `styles` dict."""
        return prefix_keys(cls.base_style, styles)

    @classmethod
    def prefixed_style(cls, style: str) -> str:
        """Prepend this highlighter's `base_style` to `style` string."""
        return cls.base_style + style

    @classmethod
    def set_highlights(cls, patterns: list[str]) -> None:
        """Compile strings to regexes."""
        cls.highlights = [re.compile(p) for p in (patterns)]

    @classmethod
    def _debug_highlight_patterns(cls):
        log_console.print(vertically_padded_panel(f"{cls.__name__}.highlights Patterns (base: '{cls.base_style}')"))

        for pattern in cls.highlights:
            log_console.print(f"   - '{escape(str(pattern))}'")


class PdfHighlighter(LogHighlighter):
    base_style = PDF_OBJ_STYLE_PREFIX

    @classmethod
    def prefixed_style(cls, style: str) -> str:
        """Prepend this highlighter's `base_style` to `style` string, removing first slash."""
        return cls.base_style + style.removeprefix('/')

    def highlight(self, text: Text) -> None:
        """Highlight both with this class's `highlights` as well as those of `LogHighlighter`."""
        highlight_regex = text.highlight_regex

        for re_highlight in self.highlights:
            highlight_regex(re_highlight, style_prefix=self.base_style)

        for log_highlight in LogHighlighter.highlights:
            highlight_regex(log_highlight, style_prefix=LogHighlighter.base_style)

            # if (match := log_highlight.search(text.plain)):
            #     print(f"matched highlight pattern: {log_highlight}, match={match}")


# Instantiate highlighters
log_highlighter = LogHighlighter()
pdf_highlighter = PdfHighlighter()
