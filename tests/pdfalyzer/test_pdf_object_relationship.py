import pytest
from PyPDF2 import PdfReader
from PyPDF2.generic import IndirectObject

from pdfalyzer.helpers.pdf_object_helper import _sort_pdf_object_refs
from pdfalyzer.pdf_object_relationship import PdfObjectRelationship
from pdfalyzer.util.adobe_strings import *

FONT_IDS = [5, 9, 11, 14, 20, 22, 24]
ANNOTS_IDS = [13, 19] + [i for i in range(26, 54)]
EXT_G_STATE_IDS = [7, 8]


@pytest.fixture(scope="session")
def pdf_reader(analyzing_malicious_pdf_path):
    pdf_file = open(analyzing_malicious_pdf_path, 'rb')
    yield PdfReader(pdf_file)
    pdf_file.close()


@pytest.fixture(scope="session")
def page_obj(pdf_reader):
    yield IndirectObject(3, 0, pdf_reader)


@pytest.fixture(scope="session")
def page_obj_direct_refs(page_obj, page_node):
    yield [
        PdfObjectRelationship(page_node, page_obj, IndirectObject(2, 0, pdf_reader), PARENT, PARENT),
        PdfObjectRelationship(page_node, page_obj, IndirectObject(4, 0, pdf_reader), CONTENTS, CONTENTS),
    ]


def test_get_references(pdf_reader, page_obj, page_node, page_obj_direct_refs):
    ext_g_state_refs = [
        PdfObjectRelationship(
            page_node,
            page_obj,
            IndirectObject(id, 0, pdf_reader),
            RESOURCES,
            f"{RESOURCES}[{EXT_G_STATE}][/GS{id}]"
        )
        for id in EXT_G_STATE_IDS
    ]

    font_refs = [
        PdfObjectRelationship(
            page_node,
            page_obj,
            IndirectObject(id, 0, pdf_reader),
            RESOURCES,
            f"{RESOURCES}[{FONT}][/F{i + 1}]"
        )
        for i, id in enumerate(FONT_IDS)
    ]

    annots_refs = [
        PdfObjectRelationship(page_node, page_obj, IndirectObject(id, 0, pdf_reader), ANNOTS, ANNOTS + f"[{i}]")
        for i, id in enumerate(ANNOTS_IDS)
    ]

    expected_refs = _sort_pdf_object_refs(page_obj_direct_refs + ext_g_state_refs + font_refs + annots_refs)
    actual_refs = _sort_pdf_object_refs(PdfObjectRelationship.get_references(from_node=page_node))
    assert actual_refs == expected_refs


def test_relationship_equality(page_obj_direct_refs):
    assert page_obj_direct_refs[0] != page_obj_direct_refs[1]
