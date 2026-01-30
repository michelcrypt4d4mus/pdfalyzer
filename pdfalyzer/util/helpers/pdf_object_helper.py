"""
Some methods to help with the direct manipulation/processing of PyPDF's PdfObjects
"""
from dataclasses import dataclass

from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, PdfObject

from pdfalyzer.util.adobe_strings import TYPE
from pdfalyzer.util.logging import log

BAD_NUMBER_TREE_MSG = '/Nums tree failed to be coerced to a DictionaryObject'


@dataclass
class RefAndObj:
    ref: IndirectObject
    obj: PdfObject | None


def coerce_nums_array_to_dict(nums: PdfObject | list) -> PdfObject | dict:
    """/Nums (number trees) are dict-like pairs in an array, e.g. [0, objA, 1, objB, 4, objC]."""
    bad_nums_log_msg = f"{BAD_NUMBER_TREE_MSG}:\n{nums}"

    if not (isinstance(nums, list) and len(nums) % 2 == 0):
        log.warning(bad_nums_log_msg)
        return nums

    nums_dict = {nums[i]: nums[i + 1] for i in range(0, len(nums), 2)}

    if not all(isinstance(k, int) and isinstance(v, (PdfObject, float, int, str)) for k, v in nums_dict.items()):
        log.warning(bad_nums_log_msg)
        return nums

    log.info(f"Coerced /Nums list to a dict with {len(nums_dict)} keys")
    return nums_dict


def describe_obj(_obj: PdfObject | RefAndObj | None) -> str:
    obj = _obj.obj if isinstance(_obj, RefAndObj) else _obj
    obj_str = ''

    if isinstance(obj, DictionaryObject):
        obj_type = obj.get(TYPE)
        obj_str += f"{obj_type} " if obj_type else ''

    obj_str += f"{_obj.ref.idnum} " if isinstance(_obj, RefAndObj) else ''
    obj_str += f"({type(obj).__name__}) "

    if isinstance(obj, (ArrayObject, list)):
        obj_str += f"{len(obj)} elements"

    return obj_str.strip()


def pypdf_class_name(obj: PdfObject) -> str:
    """Shortened name of type(obj), e.g. PyPDF.generic._data_structures.ArrayObject becomes Array"""
    class_pkgs = type(obj).__name__.split('.')
    class_pkgs.reverse()
    return class_pkgs[0].removesuffix('Object')
