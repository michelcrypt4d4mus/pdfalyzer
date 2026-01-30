from rich.text import Text


PDFALYZE = 'pdfalyze'
PDFALYZER = f"{PDFALYZE}r"
PDFALYZER_UPPER = PDFALYZER.upper()

PDF_PARSER_PY = 'pdf-parser.py'
PDF_PARSER_INSTALL_SCRIPT = 'pdfalyzer_install_pdf_parser'

PIP_INSTALL_EXTRAS = f"pip install {PDFALYZER}[extract]"

# User messaging
PDF_PARSER_NOT_FOUND_MSG = Text('').append(PDF_PARSER_PY, style='light_green') + \
    Text(f" script not found, using dumb approach to verify PDF obj IDs. ") + \
    Text(f"Consider running ").append(PDF_PARSER_INSTALL_SCRIPT, style='cyan').append(f" command.")
