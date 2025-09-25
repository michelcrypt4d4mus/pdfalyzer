from typing import Optional

from yaralyzer.output.rich_console import console

from pdfalyzer.helpers.rich_text_helper import warning_text


def ocr_text(image: "Image.Image", image_name: str) -> Optional[str]:  # noqa F821
    """Use pytesseract to OCR the text in the image and return it as a string."""
    import pytesseract
    from PIL import Image
    text = None

    try:
        text = pytesseract.image_to_string(image)
    except pytesseract.pytesseract.TesseractError:
        console.print_exception()
        console.print(warning_text(f"Tesseract OCR failure '{image_name}'! No OCR text extracted..."))
    except OSError as e:
        if 'truncated' in str(e):
            console.print(warning_text(f"Truncated image file '{image_name}'!"))
        else:
            console.print_exception()
            console.print(f"Error while extracting '{image_name}'!", style='bright_red')
            raise e
    except Exception as e:
        console.print_exception()
        console.print(f"Error while extracting '{image_name}'!", style='bright_red')
        raise e

    return None if text is None else text.strip()
