"""
Some methods to help with the direct manipulation/processing of PyPDF2's PdfObjects
"""
from collections import namedtuple
from PyPDF2.generic import IndirectObject, PdfObject

from lib.util.exceptions import PdfWalkError
from lib.util.logging import log


# In the case of easy key/value pairs the reference_key and the reference_address are the same but
# for more complicated references the reference_address will be the reference_key plus sub references.
#   e.g. a reference_key for a /Font labeled /F1 could be '/Resources' but the reference_address
# might be '/Resources[/Font][/F1] if the /Font is a directly embedded reference instead of a remote one.
PdfObjectRef = namedtuple('PdfObjectRef', ['reference_key', 'reference_address', 'pdf_obj'])


def pdf_object_id(pdf_object):
    """Return the ID of an IndirectObject and None for everything else"""
    if isinstance(pdf_object, IndirectObject):
        return pdf_object.idnum
    else:
        return None


def does_list_have_any_references(_list):
    """Return true if any element of _list is an IndirectObject"""
    return any(isinstance(item, IndirectObject) for item in _list)


def get_references(obj: PdfObject, ref_key=None, ref_address=None) -> [PdfObjectRef]:
    """Return list of PdfObjectRefs"""
    if isinstance(obj, IndirectObject):
        if ref_key is None or ref_address is None:
            raise PdfWalkError(f"{obj} is a reference but key or address not provided")

        return [PdfObjectRef(ref_key, ref_address, obj)]
    elif isinstance(obj, list) and isinstance(obj, dict):
        raise PdfWalkError(f"PdfObject {obj} is both a dict and a list")

    return_list = []

    if isinstance(obj, list):
        for i, element in enumerate(obj):
            if not isinstance(element, (IndirectObject, list, dict)):
                continue

            _ref_key = ref_key or i
            _ref_address = f"[{i}]" if ref_address is None else f"{ref_address}[{i}]"
            return_list += get_references(element, _ref_key, _ref_address)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            _ref_key = ref_key or k
            _ref_address = k if ref_address is None else f"{ref_address}[{k}]"
            return_list += get_references(v, _ref_key, _ref_address)
    else:
        log.debug(f"Adding no references for {obj}")

    return return_list
