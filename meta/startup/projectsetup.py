import decimal
import logging
import logging.handlers
import pandas as pd

# Perform some magic around importing notebooks.
import notebookimporter  # noqa: F401

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
