class PdfParserError(RuntimeError):
    """For issues with Didier Stevens's pdf-parser.py."""


class PdfWalkError(RuntimeError):
    """For errors that arise while walking the document tree."""
