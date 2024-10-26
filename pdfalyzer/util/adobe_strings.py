"""
String constants specified in the Adobe specs for PDFs, fonts, etc.
"""

from pypdf.constants import (CatalogDictionary, ImageAttributes, PageAttributes,
     PagesAttributes, Resources)

from pdfalyzer.helpers.string_helper import is_prefixed_by_any

# Fake PDF instructions used to create more explanatory tables/trees/addresses/etc.
ARRAY_ELEMENT = '/ArrayElement'
TRAILER = '/Trailer'
UNLABELED = '/UnlabeledArrayElement'

# Actual PDF instructions
AA              = CatalogDictionary.AA  # Automatic Action
ACRO_FORM       = CatalogDictionary.ACRO_FORM  # Can trigger Javascript on open
ANNOTS          = '/Annots'
COLOR_SPACE     = Resources.COLOR_SPACE
D               = '/D'  # Destination, usually of a link or action
CONTENTS        = '/Contents'
DEST            = '/Dest'  # Similar to /D?
ENCODING        = '/Encoding'
EXT_G_STATE     = Resources.EXT_G_STATE
FIELDS          = '/Fields'
FIRST           = '/First'
FONT            = Resources.FONT
FONT_FILE       = '/FontFile'
FONT_FILE2      = FONT_FILE + '2'
FONT_FILE3      = FONT_FILE + '3'
FONT_DESCRIPTOR = '/FontDescriptor'
GO_TO_E         = '/GoTo'  # Remote go-to action
GO_TO_R         = '/GoTo'  # Remote go-to action
GROUP           = '/Group'
IMPORT_DATA     = '/ImportData'
JAVASCRIPT      = '/JavaScript'
JS              = '/JS'
K               = '/K'  # Equivalent of /Kids for /StructElem
KIDS            = PagesAttributes.KIDS
LAST            = '/Last'
LAUNCH          = '/Launch'
NAMED           = '/Named'
NAMES           = '/Names'
NEXT            = '/Next'
NUMS            = '/Nums'
OBJECT_STREAM   = '/ObjStm'
OBJ             = '/Obj'
# TODO: /Pg refs could be the parents of /OBJR?
OBJR            = '/OBJR'  # Object reference to "an entire PDF object"
OPEN_ACTION     = CatalogDictionary.OPEN_ACTION
P               = '/P'  # Equivalent of /Parent for /StructElem
PAGE            = '/Page'
PAGES           = '/Pages'
PARENT          = PagesAttributes.PARENT
PARENT_TREE     = '/ParentTree'
PG              = '/Pg'  # Page ref for OBJR
PREV            = '/Prev'
RENDITION       = '/Rendition'
RESOURCES       = PageAttributes.RESOURCES
S               = '/S'  # Equivalent of /Subtype for /StructElem
SIZE            = '/Size'
STRUCT_ELEM     = '/StructElem'
SUBMIT_FORM     = '/SubmitForm'
SUBTYPE         = ImageAttributes.SUBTYPE
THREAD          = '/Thread'
TO_UNICODE      = '/ToUnicode'
TYPE            = PageAttributes.TYPE
TYPE1_FONT      = '/Type1'
W               = '/W'  # Equivalen of /Widths in some situations
WIDGET          = '/Widget'
WIDTHS          = '/Widths'
XOBJECT         = Resources.XOBJECT
XREF            = '/XRef'
XREF_STREAM     = '/XRefStm'

# There can be up to 3 /Length1, Length2, etc. keys depending on the type of font.
# They indicate points in the binary stream where different sections of the font definition
# can be found.
FONT_LENGTHS = [f'/Length{i + 1}' for i in range(3)]
FONT_FILE_KEYS = [FONT_FILE, FONT_FILE2, FONT_FILE3]

# Instructions to flag when scanning stream data for malicious content. The leading
# front slash will be removed when pattern matching.
DANGEROUS_PDF_KEYS = [
    # AA,  # AA is too generic; can't afford to remove the frontslash
    ACRO_FORM,
    GO_TO_E,
    GO_TO_R,
    IMPORT_DATA,
    JAVASCRIPT,
    JS,
    LAUNCH,
    OPEN_ACTION,
    RENDITION,
    THREAD,
    SUBMIT_FORM
]

# Adobe font instruction that begins the binary (usually encrypted) section of the font definition
CURRENTFILE_EEXEC = b'currentfile eexec'

# A node with this label is really just a non-tree link between nodes
# TODO: not sure these really need to be separate from NON_TREE_REFERENCES
LINK_NODE_KEYS = [
    D,
    DEST,
    NUMS
]

# Some references are never part of a parent/child relationship in the tree
NON_TREE_REFERENCES = [
    OPEN_ACTION,
    LAST,
    NEXT,
    PREV,
]

# Some PdfObjects can't be properly placed in the tree until the entire tree is parsed
INDETERMINATE_REF_KEYS = [
    ANNOTS,  # At least when it appears in a page
    COLOR_SPACE,
    D,
    DEST,
    EXT_G_STATE,
    FIELDS,   # At least for  /AcroForm
    FIRST,
    FONT,
    NAMES,
    OPEN_ACTION,
    P,   # At least for widgets...
    RESOURCES,
    XOBJECT,
    UNLABELED, # TODO: this might be wrong? maybe this is where the /Resources actually live?
]

INDETERMINATE_PREFIXES = [p for p in INDETERMINATE_REF_KEYS if len(p) > 2]
NON_TREE_KEYS = LINK_NODE_KEYS + NON_TREE_REFERENCES
PAGE_AND_PAGES = [PAGE, PAGES]

MULTI_REF_NODE_TYPES = [
    NUMS,
    PARENT_TREE
]

# Address reference keys that don't always appear (example: sometimes there is only a link to FIRST and LAST)
# and none of the NEXT/PREV nodes between FIRST and LAST.
IMPERMANENT_KEYS = [
    FIRST,
    LAST,
    NEXT,
    PREV,
]

# Address reference keys that adon't always appear or b) can appear more than once pointing at same node
NON_STANDARD_ADDRESS_NODES = IMPERMANENT_KEYS + MULTI_REF_NODE_TYPES


def has_indeterminate_prefix(address: str) -> bool:
    return is_prefixed_by_any(address, INDETERMINATE_PREFIXES)
