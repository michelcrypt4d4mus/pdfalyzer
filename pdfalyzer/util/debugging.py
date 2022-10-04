import logging


# Starting pdb.set_trace() this way kind of sucks because yr locals are messed up
def debugger():
    import pdb; pdb.set_trace(locals())

