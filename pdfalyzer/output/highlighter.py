import re

from rich.highlighter import ReprHighlighter

from pdfalyzer.helpers.collections_helper import prefix_keys
from pdfalyzer.output.theme import NODE_COLOR_THEME_DICT, PARENT_STYLE, PDF_ARRAY_STYLE, PDF_DICTIONARY_STYLE


PYPDF_LOG_PFX_PATTERN = r"\(pypdf\)"
PYPDF_LOG_PFX = PYPDF_LOG_PFX_PATTERN.replace("\\", '')

# Copied from https://rich.readthedocs.io/en/latest/_modules/rich/highlighter.html#Highlighter
# so we can get rid of a couple of the patterns.
DEFAULT_REPR_HIGHLIGHTER_PATTERNS = [
    r"(?P<tag_start><)(?P<tag_name>[-\w.:|]*)(?P<tag_contents>[\w\W]*)(?P<tag_end>>)",
    r'(?P<attrib_name>[\w_]{1,50})=(?P<attrib_value>"?[\w_]+"?)?',
    r"(?P<brace>[][{}()])",
    "|".join([
        r"(?P<ipv4>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})",
        r"(?P<ipv6>([A-Fa-f0-9]{1,4}::?){1,7}[A-Fa-f0-9]{1,4})",
        r"(?P<eui64>(?:[0-9A-Fa-f]{1,2}-){7}[0-9A-Fa-f]{1,2}|(?:[0-9A-Fa-f]{1,2}:){7}[0-9A-Fa-f]{1,2}|(?:[0-9A-Fa-f]{4}\.){3}[0-9A-Fa-f]{4})",
        r"(?P<eui48>(?:[0-9A-Fa-f]{1,2}-){5}[0-9A-Fa-f]{1,2}|(?:[0-9A-Fa-f]{1,2}:){5}[0-9A-Fa-f]{1,2}|(?:[0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4})",
        r"(?P<uuid>[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})",
        r"(?P<call>[\w.]*?)\(",
        r"\b(?P<bool_true>True)\b|\b(?P<bool_false>False)\b|\b(?P<none>None)\b",
        r"(?P<ellipsis>\.\.\.)",
        r"(?P<number_complex>(?<!\w)(?:\-?[0-9]+\.?[0-9]*(?:e[-+]?\d+?)?)(?:[-+](?:[0-9]+\.?[0-9]*(?:e[-+]?\d+)?))?j)",
        r"(?P<number>(?<!\w)\-?[0-9]+\.?[0-9]*(e[-+]?\d+?)?\b|0x[0-9a-fA-F]*)",
        # r"(?P<path>\B(/[-\w._+]+)*\/)(?P<filename>[-\w._+]*)?",
        r"(?<![\\\w])(?P<str>b?'''.*?(?<!\\)'''|b?'.*?(?<!\\)'|b?\"\"\".*?(?<!\\)\"\"\"|b?\".*?(?<!\\)\")",
        r"(?P<url>(file|https|http|ws|wss)://[-0-9a-zA-Z$_+!`(),.?/;:&=%#~@]*)",
    ]),
]

# Our custom log highlight patterns
HIGHLIGHT_PATTERNS = DEFAULT_REPR_HIGHLIGHTER_PATTERNS + [
    r"(?P<array_obj>Array(Object)?)",
    r"(?P<child>[cC]hild(ren)?|/?Kids)",
    r"(?P<dictionary_obj>Dictionary(Object)?)",
    r"(?P<indeterminate>[Ii]ndeterminate( ?[nN]odes?)?)",
    r"(?P<indirect_object>IndirectObject)",
    r"(?P<node_type>/(Subt|T)ype\b)",
    r"(?P<parent>/?(Struct)?[pP]arents?)",
    fr"(?P<pypdf_line>{PYPDF_LOG_PFX_PATTERN} .*)",
    fr"(?P<pypdf_prefix>{PYPDF_LOG_PFX_PATTERN})",
    r"(?P<relationship>Relationship( of)?)",
    r"(?P<relationship>via symlink|parent/child|child/parent)",
    r"(?P<stream_object>((De|En)coded)?Stream(Object)?)",
]

CUSTOM_LOG_HIGHLIGHTS = {
    "array_obj": f"{PDF_ARRAY_STYLE} italic",
    "child": "orange3 bold",
    "dictionary_obj": f"{PDF_DICTIONARY_STYLE} italic",
    "indeterminate": 'bright_black',
    "indirect_object": 'light_coral',
    "node_type": 'honeydew2',
    "parent": PARENT_STYLE,
    "pypdf_line": "dim",
    "pypdf_prefix": "light_slate_gray",
    "relationship": 'light_pink4',
    "stream_object": 'light_slate_blue bold',
    # Overload default theme
    'call': 'magenta',
    'ipv4': 'cyan',
    'ipv6': 'cyan',
}

LOG_THEME_DICT = prefix_keys(
    ReprHighlighter.base_style,
    {**CUSTOM_LOG_HIGHLIGHTS, **NODE_COLOR_THEME_DICT},
)


# Augment the standard ReprHighlighter
class LogHighlighter(ReprHighlighter):
    highlights: list[re.Pattern]

    def get_style(self, for_str: str) -> str:
        """Return the first style that matches the 'for_str'."""
        for highlight in self.highlights:
            if (match := highlight.search(for_str)):
                return self.base_style + next(k for k in match.groupdict().keys())

        return ''

    @classmethod
    def add_highlight_patterns(cls, patterns: list[str]) -> None:
        cls.highlights = [
            re.compile(pattern)
            for pattern in (patterns + HIGHLIGHT_PATTERNS)
        ]


assert all('(?P<' in pattern for pattern in HIGHLIGHT_PATTERNS)

for capture_group_label in CUSTOM_LOG_HIGHLIGHTS.keys():
    label = f"<{capture_group_label.removeprefix(ReprHighlighter.base_style)}>"
    print(f" label: {label}")
    #import pdb;pdb.set_trace()
    assert any(label in pattern for pattern in HIGHLIGHT_PATTERNS), f"Capture group {label} not found!"
