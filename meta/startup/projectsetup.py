import datetime
import decimal
import logging
import logging.handlers
import numbers
import pandas as pd
import traceback
import typing

from IPython.display import display, HTML

# Perform some magic around importing notebooks.
import notebookimporter

pd.options.display.float_format = '{:,.8f}'.format
decimal.getcontext().prec = 18

_log_levels = {
    logging.CRITICAL: "🛑",
    logging.ERROR: "🚨",
    logging.WARNING: "⚠",
    logging.INFO: "ⓘ",
    logging.DEBUG: "🐛"
}

default_log_record_factory = logging.getLogRecordFactory()
def emojified_record_factory(*args, **kwargs):
    record = default_log_record_factory(*args, **kwargs)
    # Here's where we add our own format keywords.
    record.level_emoji = _log_levels[record.levelno]
    return record

logging.setLogRecordFactory(emojified_record_factory)

# Make logging a little more verbose than the default.
logging.basicConfig(level=logging.INFO,
                    datefmt="%Y-%m-%d %H:%M:%S",
                    format="%(asctime)s %(level_emoji)s %(name)-12.12s %(message)s")
