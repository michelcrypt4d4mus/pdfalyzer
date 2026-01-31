import csv
import io
from dataclasses import dataclass, field
from pathlib import Path

from yaralyzer.util.helpers.shell_helper import ShellResult

from pdfalyzer.util.helpers.filesystem_helper import DEFAULT_PDF_TOOLS_DIR

CHECK_PDF_OCR_TEXT_URL = 'https://raw.githubusercontent.com/hypothesis/pdf-text-quality/refs/heads/main/check-pdf-text.py'
CHECK_PDF_OCR_TEXT_PATH = DEFAULT_PDF_TOOLS_DIR.joinpath(CHECK_PDF_OCR_TEXT_URL.split('/')[-1])
CHECK_PDF_OCR_CMD = f'python {CHECK_PDF_OCR_TEXT_PATH} --csv'.split()


@dataclass
class PageIouScore:
    """
    "IOU" stands for Intersection over Union and indicates how well bounding boxes for words in the text layer match
    up to text found in the page image via OCR. Values above 0.7 are generally "good", values from 0.5-0.7 are "fair"
    and values below 0.5 are poor.
    From: https://github.com/hypothesis/pdf-text-quality/tree/main?tab=readme-ov-file#usage
    """
    file: Path
    page: int
    iou: float
    iou_x: float
    iou_y: float
    iou_weighted: float

    def __post_init__(self):
        self.file = Path(self.file)
        self.page = int(self.page)

        for attr, val in vars(self).items():
            if attr.startswith('iou'):
                setattr(self, attr, float(val))


@dataclass
class PdfOcrCheckManager:
    """Manage calls to check-pdf-text.py to checks whether there is already COR text that matches images in a file."""
    path_to_pdf: Path
    page_scores: dict[int, PageIouScore] = field(default_factory=dict)

    def __post_init__(self):
        result = ShellResult.from_cmd(CHECK_PDF_OCR_CMD + [self.path_to_pdf], verify_success=True)
        reader = csv.DictReader(io.StringIO(result.stdout))

        for row in list(reader):
            self.page_scores[int(row['page'])] = PageIouScore(**row)
