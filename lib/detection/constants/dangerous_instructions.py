from lib.util.adobe_strings import DANGEROUS_PDF_KEYS
from lib.detection.constants.character_encodings import BOMS


# Remove the leading '/' from elements of DANGEROUS_PDF_KEYS and convert to bytes, except /F ("URL")
DANGEROUS_BYTES = [instruction[1:].encode() for instruction in DANGEROUS_PDF_KEYS] + [b'/F']
DANGEROUS_JAVASCRIPT_INSTRUCTIONS = [b'eval']
DANGEROUS_INSTRUCTIONS = DANGEROUS_BYTES + DANGEROUS_JAVASCRIPT_INSTRUCTIONS + list(BOMS.keys())
