import argparse
import decimal
import logging
import mango

# Perform some magic around importing notebooks.
import notebookimporter  # noqa: F401

# Increased precision from 18 to 36 because for a decimal like:
# val = Decimal("17436036573.2030800")
#
# The following rounding operations would both throw decimal.InvalidOperation:
# val.quantize(Decimal('.000000001'))
# round(val, 9)
decimal.getcontext().prec = 36

default_args: argparse.Namespace = argparse.Namespace(log_level=logging.INFO, log_suppress_timestamp=False)
mango.setup_logging(default_args)
