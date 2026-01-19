from dataclasses import asdict, dataclass, field, fields
from typing import Self, cast

from pypdf._cmap import prepare_cm
from pypdf._font import Font
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, NameObject, PdfObject, StreamObject, is_null_or_none
from rich.table import Table
from rich.text import Text
from yaralyzer.output.rich_console import console
from yaralyzer.util.logging import log

from pdfalyzer.util.adobe_strings import FONT_FILE_KEYS, FONT_LENGTHS, RESOURCES, TO_UNICODE, W, WIDTHS


# Adapted from similar function in pypdf, not ultimately useful
def _get_fonts_walk(obj: DictionaryObject) -> list[Font]:
    """
    Get the set of all fonts (embedded and not embedded).

    If there is a key called 'BaseFont', that is a font that is used in the document.
    If there is a key called 'FontName' and another key in the same dictionary object
    that is called 'FontFilex' (where x is null, 2, or 3), then that fontname is
    embedded.

    Args:
        obj: Page resources dictionary
    """
    fonts: list[Font] = []

    def process_font(f: DictionaryObject) -> None:
        nonlocal fonts
        f = cast(DictionaryObject, f.get_object())  # to be sure

        if "/BaseFont" in f:
            fonts.append(Font.from_font_resource(f))
            fonts[-1].is_embedded = False  # TODO: should be a FontInfo prop

        if "/CharProcs" in f \
                or ("/FontDescriptor" in f and any(x in f["/FontDescriptor"] for x in FONT_FILE_KEYS)) \
                or ("/DescendantFonts" in f \
                    and "/FontDescriptor" in f["/DescendantFonts"][0].get_object() \
                    and any(x in f["/DescendantFonts"][0].get_object() for x in FONT_FILE_KEYS)):
            try:
                log.warning(f"Extracting font from /CharProcs or /DescendantFonts")
                fonts.append(Font.from_font_resource(f))
                fonts[-1].is_embedded = True
            except KeyError:
                log.error(f"Failed to extract font from {f}")

    if "/DR" in obj and "/Font" in cast(DictionaryObject, obj["/DR"]):
        dr_obj = cast(DictionaryObject, obj["/DR"])

        for f in cast(DictionaryObject, dr_obj["/Font"]):
            log.warning(f"Extracting font from /DR")
            process_font(f)

    if "/Resources" in obj:
        resources = cast(DictionaryObject, obj["/Resources"])

        if "/Font" in resources:
            for f in cast(DictionaryObject, resources["/Font"]).values():
                log.warning(f"Extracting font from /Resources")
                process_font(f)

        if "/XObject" in resources:
            for x in cast(DictionaryObject, resources["/XObject"]).values():
                xobject_fonts = _get_fonts_walk(cast(DictionaryObject, x.get_object()))
                fonts.extend(xobject_fonts)

                if xobject_fonts:
                    log.warning(f"Extracted {len(xobject_fonts)} fonts from /Resources/XObject")

    if "/Annots" in obj:
        for i, annot in enumerate(cast(ArrayObject, obj["/Annots"])):
            annots_fonts = _get_fonts_walk(cast(DictionaryObject, annot.get_object()))
            fonts.extend(annots_fonts)

            if annots_fonts:
                log.warning(f"Extracted {len(annots_fonts)} fonts from /Annots[{i}]")

    if "/AP" in obj and "/N" in cast(DictionaryObject, obj["/AP"]):
        n_obj = cast(DictionaryObject, cast(DictionaryObject, obj["/AP"])["/N"])

        if n_obj.get("/Type") == "/XObject":
            n_obj_fonts = _get_fonts_walk(n_obj)
            fonts.extend(n_obj_fonts)

            if n_obj_fonts:
                log.warning(f"Extracted font from /AP/N which is an /Xobject")
        else:
            for a in n_obj:
                n_obj_dict_fonts = _get_fonts_walk(cast(DictionaryObject, a))
                fonts.extend(n_obj_dict_fonts)

                if n_obj_dict_fonts:
                    log.warning(f"Extracted {len(annots_fonts)} fonts from /AP/N/{a} (not /XObject)")

    return uniquify_fonts(fonts)



def log_walked_fonts(fonts: list[Font], source: str) -> None:
    if fonts:
        fonts = uniquify_fonts(fonts)
        font_names = sorted([unique_font_string(font) for font in fonts])
        log.warning(f"Extracted {len(font_names)} walked fonts from {source}: {json.dumps(font_names, indent=4)}")


def compare_fonts(font_infos: list[FontInfo]) -> None:
    unique_font_strings = list(set([unique_font_string(fi.font_obj) for fi in font_infos]))

    for font_str in unique_font_strings:
        _font_infos = [fi for fi in font_infos if unique_font_string(fi.font_obj) == font_str]

        if len(_font_infos) == 1:
            continue

        log.warning(f"Found {len(_font_infos)} '{font_str}' fonts, comparing /Font dicts:")
        compare_dicts(_font_infos[0].font_dict, _font_infos[1].font_dict)
        log.warning(f"Comparing /FontDescriptor for '{font_str}':")
        compare_dicts(_font_infos[0].font_descriptor_dict, _font_infos[1].font_descriptor_dict)
