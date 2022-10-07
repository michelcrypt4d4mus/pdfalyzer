"""
String constants specified in the Adobe specs for PDFs, fonts, etc.
"""

from PyPDF2.constants import (CatalogDictionary, ImageAttributes, PageAttributes,
     PagesAttributes, Ressources as Resources)


# Fake PDF instructions used to create more explanatory tables/trees/addresses/etc.
ARRAY_ELEMENT = '/ArrayElement'
TRAILER = '/Trailer'
UNLABELED = '/UnlabeledArrayElement'

# Actual PDF instructions
AA              = CatalogDictionary.AA  # Automatic Action
ACRO_FORM       = CatalogDictionary.ACRO_FORM  # Can trigger Javascript on open
COLOR_SPACE     = Resources.COLOR_SPACE
D               = '/D'  # Destination, usually of a link or action
CONTENTS        = '/Contents'
DEST            = '/Dest'  # Similar to /D?
EXT_G_STATE     = Resources.EXT_G_STATE
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
NEXT            = '/Next'
NUMS            = '/Nums'
OBJECT_STREAM   = '/ObjStm'
OPEN_ACTION     = CatalogDictionary.OPEN_ACTION
P               = '/P'  # Equivalent of /Parent for /StructElem
PARENT          = PagesAttributes.PARENT
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

# Some references are never part of a parent/child relationship in the tree
NON_TREE_REFERENCES = [
    OPEN_ACTION,
    D,
    FIRST,
    LAST,
    NEXT,
    PREV,
]

# Adobe font instruction that begins the binary (usually encrypted) section of the font definition
CURRENTFILE_EEXEC = b'currentfile eexec'
