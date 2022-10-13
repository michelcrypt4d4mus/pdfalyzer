"""
String constants specified in the Adobe specs for PDFs, fonts, etc.
"""
import re

from PyPDF2.constants import (CatalogDictionary, ImageAttributes, PageAttributes,
     PagesAttributes, Ressources as Resources)

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
EXT_G_STATE     = Resources.EXT_G_STATE
FIELDS          = '/Fields'
FIRST           = '/First'
FONT            = Resources.FONT
FONT_FILE       = '/FontFile'
FONT_FILE2      = FONT_FILE + '2'
FONT_FILE3      = FONT_FILE + '3'
FONT_DESCRIPTOR = '/FontDescriptor'
GROUP           = '/Group'
JAVASCRIPT      = '/JavaScript'
JS              = '/JS'
K               = '/K'  # Equivalent of /Kids for /StructElem
KIDS            = PagesAttributes.KIDS
LAST            = '/Last'
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
PG              = '/Pg'  # Page ref for OBJR
PREV            = '/Prev'
RESOURCES       = PageAttributes.RESOURCES
S               = '/S'  # Equivalent of /Subtype for /StructElem
SIZE            = '/Size'
STRUCT_ELEM     = '/StructElem'
SUBTYPE         = ImageAttributes.SUBTYPE
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

# Instructions to flag when scanning stream data for malicious content.
DANGEROUS_PDF_KEYS = [
    # AA,  # AA is too generic; can't afford to remove the frontslash
    ACRO_FORM,
    JAVASCRIPT,
    JS,
    OPEN_ACTION
]

# Adobe font instruction that begins the binary (usually encrypted) section of the font definition
CURRENTFILE_EEXEC = b'currentfile eexec'

# A node with this label is really just a non-tree link between nodes
PURE_REFERENCE_NODE_LABELS = [
    D,
    DEST,
    NUMS
]

# Some references are never part of a parent/child relationship in the tree
NON_TREE_REFERENCES = [
    OPEN_ACTION,
#    D,
    LAST,
    NEXT,
    PREV,
]

# Some PdfObjects can't be properly placed in the tree until the entire tree is parsed
INDETERMINATE_REFERENCES = [
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

EXTERNAL_GRAPHICS_STATE_REGEX = re.compile('/Resources\\[/ExtGState\\]\\[/GS\\d+\\]')
