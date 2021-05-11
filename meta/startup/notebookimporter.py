# This is all taken from:
# https://jupyter-notebook.readthedocs.io/en/stable/examples/Notebook/Importing%20Notebooks.html

import io
import os
import sys
import types

from importlib.abc import MetaPathFinder
from importlib.util import spec_from_loader
from nbformat import read
from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell

ALWAYS_IMPORT = """
import datetime
import decimal
import logging
import logging.handlers
import numbers
import pandas as pd
import traceback
import typing

from IPython.display import display, HTML
"""


def find_notebook(fullname, path=None):
    """Find a notebook, given its fully qualified name and an optional path

    This turns "foo.bar" into "foo/bar.ipynb"
    and tries turning "Foo_Bar" into "Foo Bar" if Foo_Bar
    does not exist.
    """
    name = fullname.rsplit('.', 1)[-1]
    if not path:
        path = ['']
    for d in path:
        nb_path = os.path.join(d, name + ".ipynb")
        if os.path.isfile(nb_path):
            return nb_path
        # let import Notebook_Name find "Notebook Name.ipynb"
        nb_path = nb_path.replace("_", " ")
        if os.path.isfile(nb_path):
            return nb_path


class NotebookLoader(object):
    """Module Loader for Jupyter Notebooks"""

    def __init__(self, path=None):
        self.shell = InteractiveShell.instance()
        self.path = path

    def load_module(self, fullname):
        """import a notebook as a module"""
        path = find_notebook(fullname, self.path)

        # load the notebook object
        with io.open(path, 'r', encoding='utf-8') as f:
            nb = read(f, 4)

        # create the module and add it to sys.modules
        # if name in sys.modules:
        #    return sys.modules[name]
        mod = types.ModuleType(fullname)
        mod.__file__ = path
        mod.__loader__ = self
        mod.__dict__['get_ipython'] = get_ipython
        sys.modules[fullname] = mod

        # extra work to ensure that magics that would affect the user_ns
        # actually affect the notebook module's ns
        save_user_ns = self.shell.user_ns
        self.shell.user_ns = mod.__dict__

        try:
            exec(ALWAYS_IMPORT, mod.__dict__)
            for cell in nb.cells:
                if cell.cell_type == 'code':
                    # transform the input to executable Python
                    code = self.shell.input_transformer_manager.transform_cell(
                        cell.source)
                    # run the code in themodule
                    exec(code, mod.__dict__)
        finally:
            self.shell.user_ns = save_user_ns
        return mod


class NotebookFinder(MetaPathFinder):
    """Module finder that locates Jupyter Notebooks"""

    def __init__(self):
        super().__init__()

    def find_spec(self, fullname, path, target=None):
        found = False
        try:
            nb_path = find_notebook(fullname, path)
            if nb_path:
                found = True
        except Exception:
            pass

        if not found:
            return

        notebookloader = NotebookLoader(path)
        return spec_from_loader(fullname, notebookloader)


sys.meta_path.append(NotebookFinder())
