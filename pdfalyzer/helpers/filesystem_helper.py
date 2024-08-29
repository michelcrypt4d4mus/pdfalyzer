from pathlib import Path
try:
    import resource as res
except ImportError: # Windows
    res = None

from yaralyzer.output.rich_console import console

from pdfalyzer.helpers.rich_text_helper import print_highlighted

DEFAULT_MAX_OPEN_FILES = 256  # macOS default
OPEN_FILES_BUFFER = 30        # we might have some files open already so we need to go beyond DEFAULT_MAX_OPEN_FILES
PDF_EXT = '.pdf'


def set_max_open_files(max_open_files=DEFAULT_MAX_OPEN_FILES):
    """
    Sets nofile soft limit to at least max_open_files. Useful for combining many PDFs compared to bash command
    default ulimit -n 1024 or OS X El Captian 256 temporary setting extinguishing with Python session.
    """
    max_open_files = max_open_files + OPEN_FILES_BUFFER

    if res is None:
        print_highlighted(f"No resource module; cannot set max open files to {max_open_files} on this platform...", style='warning')
        return (None,) * 2
    elif max_open_files <= DEFAULT_MAX_OPEN_FILES:
        print_highlighted(f"Max open files already set to at least {max_open_files}...", style='dim')
        return (DEFAULT_MAX_OPEN_FILES, DEFAULT_MAX_OPEN_FILES)

    # %% (0) what is current ulimit -n setting?
    (soft, ohard) = res.getrlimit(res.RLIMIT_NOFILE)
    hard = ohard

    # %% (1) increase limit (soft and even hard) if needed
    if soft < max_open_files:
        soft = max_open_files
        hard = max(soft, hard)
        print_highlighted(f"Setting soft & hard 'ulimit -n {soft} {hard}'...")

        try:
            res.setrlimit(res.RLIMIT_NOFILE, (soft, hard))
        except (ValueError, res.error):
            try:
               hard = soft
               print_highlighted('Trouble with max limit, retrying with soft,hard = ({}, {})'.format(soft, hard), style='warning')
               res.setrlimit(res.RLIMIT_NOFILE, (soft, hard))
            except Exception:
               print_highlighted('Failed to set ulimit, giving up!', style='error')
               soft,hard = res.getrlimit(res.RLIMIT_NOFILE)

    return (soft, hard)


def with_pdf_extension(file_path: str|Path) -> str:
    """Append '.pdf' to 'file_path' if it doesn't already end with '.pdf'."""
    file_path = str(file_path)
    return file_path + ('' if is_pdf(file_path) else PDF_EXT)


def is_pdf(file_path: str|Path) -> bool:
    """Return True if 'file_path' ends with '.pdf'."""
    return str(file_path).endswith(PDF_EXT)
