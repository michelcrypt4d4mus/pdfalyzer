"""
Constants related to character encodings
* https://www.mit.edu/people/kenta/two/iso8859.html
* https://www.utf8-chartable.de/unicode-utf8-table.pl?utf8=dec
"""

# Bytes (TODO: why is this here?)
NEWLINE_BYTE = b"\n"

# String constants
ENCODING = 'encoding'
ASCII = 'ascii'
UTF_8 = 'utf-8'
UTF_16 = 'utf-16'
UTF_32 = 'utf-32'
ISO_8859_1 =  'iso-8859-1'
WINDOWS_1252 = 'windows-1252'


# Byte order marks
BOMS = {
    b'\x2b\x2f\x76':     'UTF-7 BOM',
    b'\xef\xbb\xbf':     'UTF-8 BOM',
    b'\xfe\xff':         'UTF-16 BOM, big-endian',
    b'\xff\xfe':         'UTF-16 BOM, little-endian',
    b'\xff\xfe\x00\x00': 'UTF-32 BOM, little-endian',
    b'\x00\x00\xfe\xff': 'UTF-32 BOM, big-endian',
    b'\x0e\xfe\xff':     'SCSU BOM',
}


# ASCII characters that either print nothing, put the cursor in a weird place, or (worst of all) actively
# delete stuff you already printed
UNPRINTABLE_ASCII = {
    0: 'NUL',
    1: 'SOH',  # 'StartHeading',
    2: 'STX',  # 'StartText',
    3: 'ETX',
    4: 'EOT',  # End of transmission
    5: 'ENQ',  # 'Enquiry',
    6: 'ACK',  # 'Acknowledgement',
    7: 'BEL',  # 'Bell',
    8: 'BS',   # 'BackSpace',
    #9:  'HT'  # 'HorizontalTab',
    #10: 'LF',  # 'LineFeed',
    11: 'VT',  # 'VerticalTab',
    12: 'FF',  # 'FormFeed', AKA 'NewPage'
    13: 'CR',  # 'CarriageReturn',
    14: 'SO',  # 'ShiftOut',
    15: 'SI',  # 'ShiftIn',
    16: 'DLE',  # 'DataLineEscape',
    17: 'DC1',  # DeviceControl1',
    18: 'DC2',  # 'DeviceControl2',
    19: 'DC3',  # 'DeviceControl3',
    20: 'DC4',  # 'DeviceControl4',
    21: 'NAK',   # NegativeAcknowledgement',
    22: 'SYN',  # 'SynchronousIdle',
    23: 'ETB',  # 'EndTransmitBlock',
    24: 'CAN',  # 'Cancel',
    25: 'EM',  # 'EndMedium',
    26: 'SUB',  # 'Substitute',
    27: 'ESC',  # 'Escape',
    28: 'FS',  # 'FileSeparator',
    29: 'GS',  #'GroupSeparator',
    30: 'RS',  #'RecordSeparator',
    31: 'US',  # 'UnitSeparator',
    127: 'DEL', # Delete
}


# Fill in a dict with integer keys/values corresponding to where a given chr encoding has no chars bc
# this range is for C1 control chars. AKA # The 'undefined' part of the character map.
def scrub_c1_control_chars(char_map):
    for i in range(128, 160):
        char_map[i] = f"C1_{i}"


# ISO-8859-1 AKA "Latin-1". Basically ASCII but using more of 128-256    http://www.gammon.com.au/unicode/
UNPRINTABLE_ISO_8859_1 = UNPRINTABLE_ASCII.copy()
scrub_c1_control_chars(UNPRINTABLE_ISO_8859_1)

UNPRINTABLE_ISO_8859_1.update({
    129: 'HOP',
    141: 'RLF',
    160: 'NBSP',
    173: 'SHY',
})


# UTF-8 Makes no use of 128-256 on their own, only as continuation bytes.
# https://en.wikipedia.org/wiki/UTF-8
UNPRINTABLE_UTF_8 = UNPRINTABLE_ASCII.copy()
# The C1 bytes can appear but only as continuations
#scrub_c1_control_chars(UNPRINTABLE_UTF_8)

# C0, C1, FE, and FF, etc. *never* appear in UTF-8
UNPRINTABLE_UTF_8.update({
    192: 'C0',
    193: 'C1',
    245: 'F5',
    246: 'F6',
    247: 'F7',
    248: 'F8',
    249: 'F9',
    250: 'FA',
    251: 'FB',
    252: 'FC',
    253: 'FD',
    254: 'FE',
    255: 'FF',
})


# Win_1252 is a lot like other 256 char encodings but they colonized the C1 char DMZ in the middle
UNPRINTABLE_WIN_1252 = UNPRINTABLE_ASCII.copy()

UNPRINTABLE_WIN_1252.update({
    129: 'HOP', # High Octet Preset
    141: 'RLF', # Reverse Line Feed
    143: 'SS3', # Single shift 3
    144: 'DCS', # Device Control String
    147: 'STS', # Set transmit state
    160: 'NBSP',
})


# ISO-8859-7     #http://www.gammon.com.au/unicode/
UNPRINTABLE_ISO_8859_7 = UNPRINTABLE_ASCII.copy()
scrub_c1_control_chars(UNPRINTABLE_ISO_8859_7)

UNPRINTABLE_ISO_8859_7.update({
    174: 'AE',
    210: 'D2',
    255: 'FF'
})


# The encodings we will attempt to actually use
# Values are the unprintable values in that encoding in a dict (keys in dict are ints)
ENCODINGS_TO_ATTEMPT = {
    ASCII:        UNPRINTABLE_ASCII,
    UTF_8:          UNPRINTABLE_UTF_8,
    UTF_16:         None,
    UTF_32:         None,  # UTF-16 and 32 are handled differently
    #'utf-7':
    ISO_8859_1:   UNPRINTABLE_ISO_8859_1,
    WINDOWS_1252: UNPRINTABLE_WIN_1252
}


SINGLE_BYTE_ENCODINGS = [ASCII, ISO_8859_1, WINDOWS_1252]

# Unused cruft (mostly Asian language encodings)
ENCODINGS = [
    'big5',
    'big5hkscs',
    'cp950',
    'gb2312',
    'gbk',
    'gb18030',
    'hz',
    'iso2022_jp_2',
    'utf-7',
    'utf-8',
    'utf-16',
]
