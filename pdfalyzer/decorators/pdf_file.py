import io
from logging import Logger
from os import path
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.errors import DependencyError, EmptyFileError, PdfStreamError
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.text import Text
from yaralyzer.output.console import console
from yaralyzer.util.helpers.env_helper import log_console
from yaralyzer.util.helpers.rich_helper import DEFAULT_TABLE_OPTIONS

from pdfalyzer.util.cli_tools.page_range import PageRange
from pdfalyzer.util.constants import PIP_INSTALL_EXTRAS
from pdfalyzer.util.helpers.filesystem_helper import create_dir_if_it_does_not_exist, insert_suffix_before_extension
from pdfalyzer.util.helpers.image_helper import ocr_text
from pdfalyzer.util.helpers.rich_helper import attention_getting_panel, error_text, mild_warning
from pdfalyzer.util.helpers.string_helper import exception_str
from pdfalyzer.util.logging import log as _log

DEPENDENCY_ERROR_MSG = f"Missing an optional dependency required to extract text. Try '{PIP_INSTALL_EXTRAS}'."
DEFAULT_PDF_ERRORS_DIR = Path.cwd().joinpath('pdf_errors')
MIN_PDF_SIZE_TO_LOG_PROGRESS_TO_STDERR = 1024 * 1024 * 20


class PdfFile:
    """
    Wrapper for a PDF file path that provides useful methods and properties.

    Attributes:
        file_path (Path): The path to the PDF file.
        basename (str): The base name of the PDF file (with extension).
        basename_without_ext (str): The base name of the PDF file (without extension).
        dirname (Path): The directory containing the PDF file.
        extname (str): The file extension of the PDF file.
        file_size (int): The size of the file in bytes.
    """

    def __init__(self, file_path: str | Path) -> None:
        """
        Args:
            file_path (str | Path): Path to the PDF file.
        """
        self.file_path: Path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(f"'{file_path}' is not a valid file or directory.")

        self.dirname = self.file_path.parent
        self.basename: str = path.basename(file_path)
        self.basename_without_ext: str = str(Path(self.basename).with_suffix(''))
        self.extname: str = self.file_path.suffix
        self.file_size = self.file_path.stat().st_size

    def extract_page_range(
        self,
        page_range: PageRange,
        destination_dir: Path | None = None,
        extra_file_suffix: str | None = None
    ) -> Path:
        """
        Extract a range of pages to a new PDF file.

        Args:
            page_range (PageRange): Range of pages to extract.
            destination_dir (Path | None): Directory to save the new PDF file. Defaults to the same
                directory as the source PDF.
            extra_file_suffix (Path | None): An optional suffix to append to the new PDF's filename.
                Defaults to the page range suffix.

        Returns:
            Path: The path to the newly created PDF file containing the extracted pages.
        """
        destination_dir = Path(destination_dir or self.dirname)
        create_dir_if_it_does_not_exist(destination_dir)
        pdf_reader = PdfReader(self.file_path)
        page_count = len(pdf_reader.pages)
        file_suffix = page_range.file_suffix()

        if page_count < (page_range.last_page - 1):
            raise ValueError(f"PDF only has {page_count} pages but you asked for pages {page_range}!")

        if extra_file_suffix is not None:
            file_suffix += f"__{extra_file_suffix}"

        extracted_pages_pdf_basename = insert_suffix_before_extension(self.file_path, file_suffix).name
        extracted_pages_pdf_path = destination_dir.joinpath(extracted_pages_pdf_basename)
        console.print(f"Extracting {page_range.file_suffix()} from '{self.file_path}' to '{extracted_pages_pdf_path}'")
        pdf_writer = PdfWriter()

        with open(self.file_path, 'rb') as source_pdf:
            pdf_writer.append(fileobj=source_pdf, pages=page_range.to_tuple())

            with open(extracted_pages_pdf_path, 'wb') as extracted_pages_pdf:
                pdf_writer.write(extracted_pages_pdf)

        console.print(f"Extracted pages to new PDF: '{extracted_pages_pdf_path}'.")
        return extracted_pages_pdf_path

    def extract_text(
        self,
        page_range: PageRange | None = None,
        logger: Logger | None = None,
        print_as_parsed: bool = False
    ) -> str | None:
        """
        Use PyPDF to extract text page by page and use Tesseract to OCR any embedded images.

        Args:
            page_range (PageRange | None, optional): If provided, only extract text from pages in this range.
                Page numbers are 1-indexed. If not provided, extract text from all pages.
            log (Logger | None, optional): If provided, log progress to this logger. Otherwise use default logger.
            print_as_parsed (bool): If True, print each page's text to STDOUT as it is parsed.

        Returns:
            str | None: The extracted text, or None if extraction failed.
        """
        from PIL import Image  # Imported here to avoid hard dependency if not using this method
        log = logger or _log
        log.debug(f"Extracting text from '{self.file_path}'...")
        self._page_numbers_of_errors: list[int] = []
        extracted_pages = []

        try:
            pdf_reader = PdfReader(self.file_path)
            page_count = len(pdf_reader.pages)
            log.debug(f"PDF Page count: {page_count}")

            for page_number, page in enumerate(pdf_reader.pages, start=1):
                if page_range and not page_range.in_range(page_number):
                    self._log_to_stderr(f"Skipping page {page_number}...")
                    continue

                self._log_to_stderr(f"Parsing page {page_number}...")
                page_buffer = Console(file=io.StringIO())
                page_buffer.print(Panel(f"PAGE {page_number}", padding=(0, 15), expand=False, **DEFAULT_TABLE_OPTIONS))
                page_buffer.print(escape(page.extract_text().strip()))
                image_number = 1

                # Extracting images is a bit fraught (lots of PIL and pypdf exceptions have come from here)
                try:
                    for image_number, image in enumerate(page.images, start=1):
                        image_name = f"Page {page_number}, Image {image_number}"
                        self._log_to_stderr(f"   OCRing {image_name}...", "dim")
                        page_buffer.print(Panel(image_name, expand=False, **DEFAULT_TABLE_OPTIONS))
                        image_obj = Image.open(io.BytesIO(image.data))
                        image_text = ocr_text(image_obj, f"{self.file_path} ({image_name})")
                        page_buffer.print(escape(image_text or '').strip())
                except (OSError, NotImplementedError, TypeError, ValueError) as e:
                    error_str = exception_str(e)
                    msg = f"{error_str} while parsing embedded image {image_number} on page {page_number}..."
                    mild_warning(msg)

                    # Dump an error PDF and encourage user to report to pypdf team.
                    if 'JBIG2Decode' not in str(e):
                        log_console.print_exception()

                        if page_number not in self._page_numbers_of_errors:
                            self._handle_extraction_error(page_number, error_str)
                            self._page_numbers_of_errors.append(page_number)

                page_text = page_buffer.file.getvalue()
                extracted_pages.append(page_text)
                log.debug(page_text)

                if print_as_parsed:
                    print(f"{page_text}")
        except DependencyError:
            log.error(DEPENDENCY_ERROR_MSG)
        except EmptyFileError:
            log.warning("Skipping empty file!")
        except PdfStreamError as e:
            log_console.print_exception()
            log.error(f"Error parsing PDF file '{self.file_path}': {e}")

        return "\n\n".join(extracted_pages).strip()

    def print_extracted_text(self, page_range: PageRange | None = None, print_as_parsed: bool = False) -> None:
        """Fancy wrapper for printing the extracted text to the screen."""
        console.print(Panel(str(self.file_path), expand=False, style='bright_white reverse', **DEFAULT_TABLE_OPTIONS))
        txt = self.extract_text(page_range=page_range, print_as_parsed=print_as_parsed)

        if not print_as_parsed:
            console.print(txt)

    def _handle_extraction_error(self, page_number: int, error_msg: str) -> None:
        """Rip the offending page to a new file and suggest that user report bug to PyPDF."""
        destination_dir = DEFAULT_PDF_ERRORS_DIR

        try:
            extracted_file = self.extract_page_range(PageRange(str(page_number)), destination_dir, error_msg)
        except Exception:
            log_console.print_exception()
            log_console.print(error_text(f"Failed to extract a page for submission to PyPDF team."))
            extracted_file = None

        blink_txt = Text('', style='bright_white')
        blink_txt.append("An error (", style='blink color(154)').append(error_msg, style='color(11) blink')
        blink_txt.append(') ', style='blink color(154)')
        blink_txt.append("was encountered while processing a PDF file.\n\n", style='blink color(154)')

        txt = Text(f"The error was of a type such that it probably came from a bug in ", style='bright_white')
        txt.append('PyPDF', style='underline bright_green').append('. It was encountered processing the file ')
        txt.append(str(self.file_path), style='file').append('. You should see a stack trace above this box.\n\n')

        txt.append('The offending page will be extracted to ', style='bright_white')
        txt.append(str(extracted_file), style='file').append('.\n\n')
        txt.append(f"Please visit 'https://github.com/py-pdf/pypdf/issues' to report a bug. ", style='bold')
        txt.append(f"Providing the devs with the extracted page and the stack trace help improve pypdf.")
        log_console.print(attention_getting_panel(blink_txt + txt, title='PyPDF Error'))

    def _log_to_stderr(self, msg: str, style: str = '') -> None:
        """When parsing very large PDFs it can be useful to log progress and other messages to STDERR."""
        if self.file_size < MIN_PDF_SIZE_TO_LOG_PROGRESS_TO_STDERR:
            return

        log_console.print(msg, style=style)
