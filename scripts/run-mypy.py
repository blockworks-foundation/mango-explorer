#!/usr/bin/env python3

import argparse
import importlib
import nbformat
import os
import re
import sys

from pathlib import Path
from os.path import isfile, join
from mypy import api
from nbconvert.exporters import PythonExporter

# Get the full path to this script.
script_path = Path(os.path.realpath(__file__))

# The parent of the script is the bin directory, the parent of that is the 
# notebook directory. It's this notebook directory we want.
notebook_directory = script_path.parent.parent
print(f"Running notebook files in: {notebook_directory}")

# Add the notebook directory to our import path.
sys.path.append(str(notebook_directory))
sys.path.append(str(notebook_directory / "meta" / "startup"))

# Change into the notebook directory as well so relative locations work properly.
os.chdir(notebook_directory)

# Tell the importer how to import .ipynb files.
import projectsetup

parser = argparse.ArgumentParser(description='Run MyPy for static checks.')
parser.add_argument('--filename',
                    metavar='FILENAME',
                    help="(optional) name of file to be checked")

args = parser.parse_args()
all_notebook_files = []
if args.filename:
    all_notebook_files = [args.filename]
else:
    # We want to load every notebook just to make sure the code in it is OK.
    all_notebook_files = [f for f in os.listdir(notebook_directory) if isfile(notebook_directory / f) and f.endswith(".ipynb")]
    all_notebook_files.sort()

line_pattern = re.compile('(<[a-z]+>:)\s*(\d+)\s*:\s*(.*?)\s*:\s*(.*?)$')
def print_pattern_result(message: str):
    pattern_result = line_pattern.findall(message)
    if pattern_result:
        _, line_number, category, text = pattern_result[0]
        print(f"[{category}] line {line_number}: {text}")
    elif message:
        print(message)

# Now import each notebook in turn. If there are code problems, this should show them.
# This should also run tests, if the module has any.
for module_name in all_notebook_files:
    print(f"Checking: {module_name}")
    with open(module_name, 'r') as notebook_file:
        body = notebook_file.read()

    if module_name.endswith(".ipynb"):
        notebook = nbformat.reads(body, as_version=4)
        python_exporter = PythonExporter()
        (body, resources) = python_exporter.from_notebook_node(notebook)

    warnings, errors, exit_code = api.run(['--ignore-missing-imports', '-c', body])
    if exit_code != 0:
        print(f"MyPy exited with code {exit_code} on {module_name}")
        if warnings:
            print("MyPy Issues:")
            for warning in warnings.split("\n"):
                print_pattern_result(warning)
        if errors:
            print("MyPy Errors:")
            for error in errors.split("\n"):
                print_pattern_result(error)

        break
    
print("All files checked using MyPy.")
