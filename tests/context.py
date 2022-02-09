from contextlib import contextmanager
import logging
import mango as mango
import os
import sys
import typing

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@contextmanager
def disable_logging() -> typing.Generator[None, None, None]:
    logging.disable(logging.CRITICAL)
    try:
        yield
    finally:
        logging.disable(logging.NOTSET)
