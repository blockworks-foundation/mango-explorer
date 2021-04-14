"""
From: https://github.com/knowsuchagency/jupyter-mypy/blob/master/main.py

Add mypy type-checking cell magic to jupyter/ipython.

"""

from IPython.core.magic import register_cell_magic


@register_cell_magic
def mypy(line, cell):
    """
    Run the following cell though mypy.

    Any parameters that would normally be passed to the mypy cli
    can be passed on the first line, with the exception of the
    -c flag we use to pass the code from the cell we want to execute

     i.e.

    %%mypy --something
    ...
    ...
    ...

    If mypy returns a 0 exit code nothing will be printed.
    """

    from IPython import get_ipython
    from IPython.display import display, HTML
    from mypy import api

    result = api.run(line.split() + ['--ignore-missing-imports', '-c', cell])

    # Result is a tuple with three parts:
    #  0 - mypy warnings/problems/issues.
    #  1 - mypy's stderr, for mypy problems.
    #  2 - mypy's exit code.
    if result[2] != 0:
        html = ""
        if result[0]:
            html += f"<div style='color: darkorange'>Warnings:<ul>"
            for message in result[0].split("<string>"):
                if message:
                    html += f"<li>{message}</li>"
            html += f"</ul></div>"

        if result[1]:
            html += f"<div style='color: red'>Errors:<ul>"
            for message in result[1].split("<string>"):
                if message:
                    html += f"<li>{message}</li>"
            html += f"</ul></div>"

        display(HTML(html))

    shell = get_ipython()
    shell.run_cell(cell)

# Delete these to avoid name conflicts.
del mypy

