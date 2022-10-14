from PyPDF2 import PdfReader
from PyPDF2.generic import IndirectObject

from pdfalyzer.helpers.pdf_object_helper import PdfObjectRelationship, _sort_pdf_object_refs
from pdfalyzer.util.adobe_strings import *

FONT_IDS = [5, 9, 11, 14, 20, 22, 24]
ANNOTS_IDS = [13, 19] + [i for i in range(26, 54)]
EXT_G_STATE_IDS = [7, 8]


def test_get_references(analyzing_malicious_documents_pdf_path):
    pdf_file = open(analyzing_malicious_documents_pdf_path, 'rb')
    pdf_reader = PdfReader(pdf_file)
    pdf_obj = IndirectObject(3, 0, pdf_reader)

    direct_refs = [
        PdfObjectRelationship(pdf_obj, IndirectObject(2, 0, pdf_reader), PARENT, PARENT),
        PdfObjectRelationship(pdf_obj, IndirectObject(4, 0, pdf_reader), CONTENTS, CONTENTS),
    ]

    ext_g_state_refs = [
        PdfObjectRelationship(
            pdf_obj,
            IndirectObject(id, 0, pdf_reader),
            RESOURCES,
            f"{RESOURCES}[{EXT_G_STATE}][/GS{id}]"
        )
        for id in EXT_G_STATE_IDS
    ]

    font_refs = [
        PdfObjectRelationship(
            pdf_obj,
            IndirectObject(id, 0, pdf_reader),
            RESOURCES,
            f"{RESOURCES}[{FONT}][/F{i + 1}]"
        )
        for i, id in enumerate(FONT_IDS)
    ]

    annots_refs = [
        PdfObjectRelationship(pdf_obj, IndirectObject(id, 0, pdf_reader), ANNOTS, ANNOTS + f"[{i}]")
        for i, id in enumerate(ANNOTS_IDS)
    ]

    expected_references = _sort_pdf_object_refs(direct_refs + ext_g_state_refs + font_refs + annots_refs)
    assert _sort_pdf_object_refs(PdfObjectRelationship.get_references(pdf_obj.get_object())) == expected_references
    pdf_file.close
