import logging
from lib.helpers.rich_text_helper import console


# Starting pdb.set_trace() this way kind of sucks because yr locals are messed up
def debugger():
    import pdb; pdb.set_trace()


def print_loggers():
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    console.print("LOGGERS!")
    console.print(loggers)
