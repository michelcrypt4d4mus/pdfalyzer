import csv
import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from rich.text import Text
from yaralyzer.util.helpers.env_helper import stderr_notification
from yaralyzer.util.helpers.shell_helper import ShellResult

from pdfalyzer.config import PdfalyzerConfig
from pdfalyzer.util.constants import CHECK_PDF_OCR_TEXT_BASENAME, CONSIDER_INSTALLING_EXTRAS_MSG, CONSIDER_INSTALLING_TOOLS_MSG
from pdfalyzer.util.logging import log

CHECK_PDF_OCR_CMD = f'python {PdfalyzerConfig.check_pdf_ocr_text_path} --csv'.split()


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
    has_warned: ClassVar[bool] = False

    def __post_init__(self):
        cmd = ['python', PdfalyzerConfig.check_pdf_ocr_text_path, '--csv', self.path_to_pdf]
        result = ShellResult.from_cmd(cmd, verify_success=True)
        reader = csv.DictReader(io.StringIO(result.stdout))

        for row in list(reader):
            self.page_scores[int(row['page'])] = PageIouScore(**row)

    @classmethod
    def is_available(cls) -> bool:
        """Return `True` if `check-pdf-text.py` script is available and runnable."""
        if cls.has_warned:
            return False

        warning = None
        print(f"PdfalyzerConfig.check_pdf_ocr_text_path: {PdfalyzerConfig.check_pdf_ocr_text_path }")

        if PdfalyzerConfig.check_pdf_ocr_text_path is not None and PdfalyzerConfig.check_pdf_ocr_text_path.exists():
            try:
                import numpy
            except ModuleNotFoundError:
                warning = Text(f"numpy package not installed, {CHECK_PDF_OCR_TEXT_BASENAME} script cannot be run.\n")
                warning.append(CONSIDER_INSTALLING_EXTRAS_MSG)
        else:
            warning = Text(f"{CHECK_PDF_OCR_TEXT_BASENAME} script not installed. ") + CONSIDER_INSTALLING_TOOLS_MSG

        if warning:
            stderr_notification(warning)
            cls.has_warned = True
            return False
        else:
            return True
