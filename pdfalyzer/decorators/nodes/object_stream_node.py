"""
/ObjStm nodes are special nodes containing other nodes in a binary compressed format.

pypdf reads objects from these streams in PdfReader._get_object_from_stream():
    https://github.com/py-pdf/pypdf/blob/4740225eaa67ad2e032e63d0453ea6c80bcae158/pypdf/_reader.py#L343

Didier Stevens parses /ObjStm as a synthetic PDF here: https://github.com/DidierStevens/DidierStevensSuite/blob/master/pdf-parser.py#L1605
Something like:

    offset_stream_data = obj.get_data()[obj.get('/First', 0):]
    log.warning(f"Offset stream: {offset_stream_data[0:100]}")
    stream = BytesIO(offset_stream_data)
    p = PdfReader(stream)
"""
