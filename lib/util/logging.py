"""
There's two possible log sinks other than STDOUT:

  1. 'log' - the application log (standard log, what goes to STDOUT with -D option)
  2. 'invocation_log' - very minal log to track the command line options provided at used at invocation time

The regular log file at APPLICATION_LOG_PATH is where the quite verbose application logs
will be written if things ever need to get that formal. For now those logs are only accessible
on STDOUT with the -D flag but the infrastructure for persistent logging exists if someone
needs/wants that sort of thing.

Logs are not normally ephemeral/not written  to files but can be configured to do so by setting
the PDFALYZER_LOG_DIR env var. See .env.example for documentation about the side effects of setting
PDFALYZER_LOG_DIR to a value.

https://docs.python.org/3/library/logging.html#logging.basicConfig
https://realpython.com/python-logging/

Python log levels for reference:
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

from lib.config import PdfalyzerConfig


def logfile_basename(label):
    return f"pdfalyzer.{label}.log"

APPLICATION_LOG_NAME = logfile_basename('run')
APPLICATION_LOG_PATH = path.join(PdfalyzerConfig.LOG_DIR, APPLICATION_LOG_NAME)
INVOCATION_LOG_NAME = logfile_basename('invocation')
INVOCATION_LOG_PATH = path.join(PdfalyzerConfig.LOG_DIR, INVOCATION_LOG_NAME)


# 'log' (the application log)
log = logging.getLogger(APPLICATION_LOG_NAME)
log.setLevel(PdfalyzerConfig.LOG_LEVEL)

# Write logs to a file if PDFALYZER_LOG_DIR is configured otherwise have Rich style logs and send them to STDOUT.
if PdfalyzerConfig.IS_LOGGING_TO_FILE:
    if not path.isdir(PdfalyzerConfig.LOG_DIR):
        raise RuntimeError(f"PDFALYZER_LOG_DIR '{PdfalyzerConfig.LOG_DIR}' doesn't exist or is not absolute")

    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    log_file_handler = logging.FileHandler(APPLICATION_LOG_PATH)
    log_file_handler.setLevel(PdfalyzerConfig.LOG_LEVEL)
    log_file_handler.setFormatter(log_formatter)
    log.addHandler(log_file_handler)
    log.info('File logging triggered by setting of PDFALYZER_LOG_DIR')
else:
    log.addHandler(RichHandler(rich_tracebacks=True))


# 'invocation_log' (a history of pdfalyzer runs containing previous commands you can cut and paste to re-run)
invocation_log = logging.getLogger(INVOCATION_LOG_NAME)
invocation_log_formatter = logging.Formatter('[%(asctime)s] %(message)s')
invocation_log_file_handler = logging.FileHandler(INVOCATION_LOG_PATH)
invocation_log_file_handler.setLevel(PdfalyzerConfig.LOG_LEVEL)
invocation_log_file_handler.setFormatter(invocation_log_formatter)
invocation_log.addHandler(invocation_log_file_handler)
invocation_log.setLevel(PdfalyzerConfig.LOG_LEVEL)


def log_and_print(msg: str, log_level='INFO'):
    """Both print and log (at INFO level) a string"""
    log.log(logging.getLevelName(log_level), msg)
    print(msg)


def log_current_config():
    """Write current state of PdfalyzerConfig object to the logs"""
    msg = f"{PdfalyzerConfig.__name__} attributes:\n"
    config_dict = {k: v for k, v in vars(PdfalyzerConfig).items() if not k.startswith('__')}

    for k in sorted(config_dict.keys()):
        msg += f"   {k: >40}  {config_dict[k]}\n"

    log.info(msg)


# Suppress annoying chardet library logs
for submodule in ['universaldetector', 'charsetprober', 'codingstatemachine']:
    logging.getLogger(f"chardet.{submodule}").setLevel(logging.WARNING)
