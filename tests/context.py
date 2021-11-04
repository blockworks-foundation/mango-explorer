from contextlib import contextmanager
import logging
import mango
import os
import sys
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")))


@contextmanager
def disable_logging():
    logging.disable(logging.CRITICAL)
    try:
        yield
    finally:
        logging.disable(logging.NOTSET)
