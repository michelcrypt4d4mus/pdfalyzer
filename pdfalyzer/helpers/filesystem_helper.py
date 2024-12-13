"""
Some helpers for stuff with the local filesystem.
"""
import re
from pathlib import Path
from typing import Optional, Union

from yaralyzer.output.rich_console import console

from pdfalyzer.helpers.rich_text_helper import print_highlighted

NUMBERED_PAGE_REGEX = re.compile(r'.*_(\d+)\.\w{3,4}$')
DEFAULT_MAX_OPEN_FILES = 256  # macOS default
OPEN_FILES_BUFFER = 30        # we might have some files open already so we need to go beyond DEFAULT_MAX_OPEN_FILES
PDF_EXT = '.pdf'

# TODO: this kind of type alias is not supported until Python 3.12
#type StrOrPath = Union[str, Path]


def with_pdf_extension(file_path: Union[str, Path]) -> str:
    """Append '.pdf' to 'file_path' if it doesn't already end with '.pdf'."""
    return str(file_path) + ('' if is_pdf(file_path) else PDF_EXT)


def is_pdf(file_path: Union[str, Path]) -> bool:
    """Return True if 'file_path' ends with '.pdf'."""
    return str(file_path).endswith(PDF_EXT)


def file_exists(file_path: Union[str, Path]) -> bool:
    """Return True if 'file_path' exists."""
    return Path(file_path).exists()


def do_all_files_exist(file_paths: list[Union[str, Path]]) -> bool:
    """Print an error for each element of 'file_paths' that's not a file. Return True if all 'file_paths' exist."""
    all_files_exist = True

    for file_path in file_paths:
        if not file_exists(file_path):
            console.print(f"File not found: '{file_path}'", style='error')
            all_files_exist = False

    return all_files_exist


def extract_page_number(file_path: Union[str, Path]) -> Optional[int]:
    """Extract the page number from the end of a filename if it exists."""
    match = NUMBERED_PAGE_REGEX.match(str(file_path))
    return int(match.group(1)) if match else None


def file_size_in_mb(file_path: Union[str, Path], decimal_places: int = 2) -> float:
    """Return the size of 'file_path' in MB rounded to 2 decimal places,"""
    return round(Path(file_path).stat().st_size / 1024.0 / 1024.0, decimal_places)


def set_max_open_files(num_filehandles: int = DEFAULT_MAX_OPEN_FILES) -> tuple[Optional[int], Optional[int]]:
    """
    Sets the OS level max open files to at least 'num_filehandles'. Current value can be seen with 'ulimit -a'.
    Required when you might be opening more than DEFAULT_MAX_OPEN_FILES file handles simultaneously
    (e.g. when you are merging a lot of small images or PDFs). Equivalent of something like
    'default ulimit -n 1024' on macOS.

    NOTE: Does nothing on Windows (I think).
    NOTE: This mostly came from somewhere on stackoverflow but I lost the link.
    """
    try:
        import resource  # Windows doesn't have this package / doesn't need to bump up the ulimit (??)
    except ImportError:
        resource = None

    if resource is None:
        print_highlighted(f"No resource module; cannot set max open files on this platform...", style='yellow')
        return (None, None)
    elif num_filehandles <= DEFAULT_MAX_OPEN_FILES:
        # Then the OS max open files value is already sufficient.
        return (DEFAULT_MAX_OPEN_FILES, DEFAULT_MAX_OPEN_FILES)

    # %% (0) what is current ulimit -n setting?
    (soft, hard) = resource.getrlimit(resource.RLIMIT_NOFILE)
    num_filehandles = num_filehandles + OPEN_FILES_BUFFER

    # %% (1) increase limit (soft and even hard) if needed
    if soft < num_filehandles:
        soft = num_filehandles
        hard = max(soft, hard)
        print_highlighted(f"Increasing max open files soft & hard 'ulimit -n {soft} {hard}'...")

        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))
        except (ValueError, resource.error):
            try:
               hard = soft
               print_highlighted(f"Retrying setting max open files (soft, hard)=({soft}, {hard})", style='yellow')
               resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))
            except Exception:
               print_highlighted('Failed to set max open files / ulimit, giving up!', style='error')
               soft,hard = resource.getrlimit(resource.RLIMIT_NOFILE)

    return (soft, hard)
