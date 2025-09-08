from os import path
from pathlib import Path
from typing import List, Optional, Union

from pypdf import PdfReader, PdfWriter
from yaralyzer.output.rich_console import console

from pdfalyzer.helpers.filesystem_helper import create_dir_if_it_does_not_exist, insert_suffix_before_extension
from pdfalyzer.util.page_range import PageRange


class PdfFile:
    """
    Wrapper for a PDF file path that provides useful methods and properties.
    """
    def __init__(self, file_path: Union[str, Path]) -> None:
        self.file_path: Path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(f"File '{file_path}' does not exist.")

        self.dirname = self.file_path.parent
        self.basename: str = path.basename(file_path)
        self.basename_without_ext: str = str(Path(self.basename).with_suffix(''))
        self.extname: str = self.file_path.suffix
        self.text_extraction_attempted: bool = False

    def extract_page_range(
            self,
            page_range: PageRange,
            destination_dir: Optional[Path] = None,
            extra_file_suffix: Optional[str] = None
        ) -> Path:
        """
        Extract a range of pages to a new PDF file.

        Args:
            page_range (PageRange): Range of pages to extract.
            destination_dir (Optional[Path]): Directory to save the new PDF file. Defaults to the same
                directory as the source PDF.
            extra_file_suffix (Optional[str]): An optional suffix to append to the new PDF's filename.
                Defaults to the page range suffix.
        """
        destination_dir = destination_dir or self.dirname
        create_dir_if_it_does_not_exist(destination_dir)

        if extra_file_suffix is None:
            file_suffix = page_range.file_suffix()
        else:
            file_suffix = f"{page_range.file_suffix()}__{extra_file_suffix}"

        extracted_pages_pdf_basename = insert_suffix_before_extension(self.file_path, file_suffix).name
        extracted_pages_pdf_path = destination_dir.joinpath(extracted_pages_pdf_basename)
        console.print(f"Extracting {page_range.file_suffix()} from '{self.file_path}' to '{extracted_pages_pdf_path}'...")
        pdf_writer = PdfWriter()

        with open(self.file_path, 'rb') as source_pdf:
            pdf_writer.append(fileobj=source_pdf, pages=page_range.to_tuple())

            with open(extracted_pages_pdf_path, 'wb') as extracted_pages_pdf:
                pdf_writer.write(extracted_pages_pdf)

        console.print(f"Wrote new PDF '{extracted_pages_pdf_path}'.")
        return extracted_pages_pdf_path
