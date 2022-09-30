import logging
from pdfalyzer.helpers.rich_text_helper import console


# Starting pdb.set_trace() this way kind of sucks because yr locals are messed up
def debugger():
    import pdb; pdb.set_trace(locals())

