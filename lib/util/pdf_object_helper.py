from PyPDF2.generic import IndirectObject


def pdf_object_id(pdf_object):
    """Return the ID of an IndirectObject and None for everything else"""
    if isinstance(pdf_object, IndirectObject):
        return pdf_object.idnum
    else:
        return None
