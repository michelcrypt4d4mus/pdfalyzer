"""
Some helpers for stuff with the local filesystem.
"""
import importlib.resources
import os
import re
from pathlib import Path

from yaralyzer.util.helpers.env_helper import stderr_notification
from yaralyzer.util.helpers.file_helper import files_in_dir, relative_path
from yaralyzer.util.logging import log

from pdfalyzer.util.constants import PDF_PARSER_PY, PDFALYZER

NUMBERED_PAGE_REGEX = re.compile(r'.*_(\d+)\.\w{3,4}$')
DEFAULT_MAX_OPEN_FILES = 256  # macOS default
OPEN_FILES_BUFFER = 30        # we might have some files open already so we need to go beyond DEFAULT_MAX_OPEN_FILES
PDF_EXT = '.pdf'

# 3rd party pdf-parser.py
PROJECT_ROOT = Path(str(importlib.resources.files(PDFALYZER))).parent
SCRIPTS_DIR = PROJECT_ROOT.joinpath('scripts')
DEFAULT_PDF_TOOLS_DIR = Path('pdf_tools')
DEFAULT_PDF_PARSER_PATH = DEFAULT_PDF_TOOLS_DIR.joinpath(PDF_PARSER_PY)


def create_dir_if_it_does_not_exist(dir: Path) -> None:
    """Like it says on the tin."""
    if dir.exists():
        return

    log.warning(f"Need to create '{dir}'")
    dir.mkdir(parents=True, exist_ok=True)


def dir_str(dir: Path) -> str:
    """Turns 'log' into 'log/' etc."""
    relative_dir = relative_path(dir)
    return str(relative_dir) + ('/' if not str(relative_dir).endswith('/') else '')


def do_all_files_exist(_file_paths: list[str | Path]) -> bool:
    """Print an error for each element of 'file_paths' that's not a file. Return True if all 'file_paths' exist."""
    file_paths = [Path(f) for f in _file_paths]
    all_files_exist = True

    for file_path in file_paths:
        if not file_path.exists():
            log.error(f"File not found: '{file_path}'")
            all_files_exist = False

    return all_files_exist


def extract_page_number(file_path: str | Path) -> int | None:
    """Extract the page number from the end of a filename if it exists."""
    match = NUMBERED_PAGE_REGEX.match(str(file_path))
    return int(match.group(1)) if match else None


def file_size_in_mb(file_path: str | Path, decimal_places: int = 2) -> float:
    """Return the size of 'file_path' in MB rounded to 2 decimal places,"""
    return round(Path(file_path).stat().st_size / 1024.0 / 1024.0, decimal_places)


def file_sizes_in_dir(dir: Path, with_extname: str | None = None) -> dict[Path, int]:
    """Returns a dict keyed by file path, values are file sizes."""
    return {Path(f): os.path.getsize(f) for f in sorted(files_in_dir(dir, with_extname))}


def insert_suffix_before_extension(file_path: Path, suffix: str, separator: str = '__') -> Path:
    """Inserting 'page 1' suffix in 'path/to/file.jpg' -> '/path/to/file__page_1.jpg'."""
    suffix = strip_bad_chars(suffix).replace(' ', '_')
    file_path_without_extension = file_path.with_suffix('')
    return Path(f"{file_path_without_extension}{separator}{suffix}{file_path.suffix}")


def is_executable(file_path: Path) -> bool:
    return os.access(file_path, os.X_OK)


def is_pdf(file_path: str | Path) -> bool:
    """Return True if 'file_path' ends with '.pdf'."""
    return str(file_path).endswith(PDF_EXT)


def set_max_open_files(num_filehandles: int = DEFAULT_MAX_OPEN_FILES) -> tuple[int | None, int | None]:
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
        log.warning(f"No resource module; cannot set max open files on this platform...")
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
        stderr_notification(f"Increasing max open files soft & hard 'ulimit -n {soft} {hard}'...")

        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))
        except (ValueError, resource.error):
            try:
                hard = soft
                log.warning(f"Retrying setting max open files (soft, hard)=({soft}, {hard})")
                resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))
            except Exception:
                log.error('Failed to set max open files / ulimit, giving up!')
                soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)

    return (soft, hard)


def strip_bad_chars(text: str) -> str:
    """Remove chars that don't work well in filenames."""
    text = ' '.join(text.splitlines()).replace('\\s+', ' ')
    text = re.sub('’', "'", text).replace('|', 'I').replace(',', ',')
    return re.sub('[^-0-9a-zA-Z@.,?_:=#\'\\$" ()]+', '_', text).replace('  ', ' ')


def with_pdf_extension(file_path: str | Path) -> Path:
    """Append `".pdf"` to `file_path` if it doesn't already end with `".pdf"`."""
    return Path(str(file_path) + ('' if is_pdf(file_path) else PDF_EXT))
