from yaralyzer.util.helpers.env_helper import log_console

from pdfalyzer.util.logging import log


def ocr_text(image: "Image.Image", image_name: str) -> str | None:  # noqa F821
    """Use pytesseract to OCR the text in the image and return it as a string."""
    import pytesseract
    from PIL import Image  # noqa: F401
    text = None

    try:
        text = pytesseract.image_to_string(image)
    except pytesseract.pytesseract.TesseractError:
        log_console.print_exception()
        log.warning(f"Tesseract OCR failure '{image_name}'! No OCR text extracted...")
    except OSError as e:
        if 'truncated' in str(e):
            log.warning(f"Truncated image file '{image_name}'!")
        else:
            log_console.print_exception()
            log.error(f"Error while extracting '{image_name}'!")
            raise e
    except Exception as e:
        log_console.print_exception()
        log.error(f"Error while extracting '{image_name}'!")
        raise e

    return None if text is None else text.strip()
