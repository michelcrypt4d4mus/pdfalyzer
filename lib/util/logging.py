"""
There's two possible log sinks other than STDOUT:

  * log - the application log (standard log, what goes to STDOUT with -D option)
  * invocation_log - very minal log to track the command line options provided at used at invocation time

The regular log file at APPLICATION_LOG_PATH is where the quite verbose application logs
will be written if things ever need to get that formal. For now those logs are only accessible
on STDOUT with the -D flag but the infrastructure for persistent logging exists if someone
needs/wants that sort of thing.

https://docs.python.org/3/library/logging.html#logging.basicConfig
https://realpython.com/python-logging/

Python log levels:

    CRITICAL 50
    ERROR 40
    WARNING 30
    INFO 20
    DEBUG 10
    NOTSET 0
"""

import logging
from os import environ, path

from rich.logging import RichHandler
from lib.util.filesystem_awareness import LOG_DIR


def logfile_basename(label):
    return f"pdfalyzer.{label}.log"

APPLICATION_LOG_NAME = logfile_basename('run')
APPLICATION_LOG_PATH = path.join(LOG_DIR, APPLICATION_LOG_NAME)

INVOCATION_LOG_NAME = logfile_basename('invocation')
INVOCATION_LOG_PATH = path.join(LOG_DIR, INVOCATION_LOG_NAME)


# log setup
log = logging.getLogger('pdfalyzer')
log.addHandler(RichHandler(rich_tracebacks=True))


# invocation_log setup
invocation_log_formatter = logging.Formatter('[%(asctime)s] %(message)s')
invocation_log_file_handler = logging.FileHandler(INVOCATION_LOG_PATH)
invocation_log_file_handler.setLevel(logging.DEBUG)
invocation_log_file_handler.setFormatter(invocation_log_formatter)
invocation_log = logging.getLogger('pdfalyzerinvocations')
invocation_log.addHandler(invocation_log_file_handler)
invocation_log.setLevel(logging.DEBUG)
