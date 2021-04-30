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

# Make logging a little more verbose than the default.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(name)-12s %(message)s")
