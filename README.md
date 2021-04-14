# Mango Explorer

**I am not yet confident in the figures and calculations. Please don't rely on this code yet!**

This is the start of a project to explore and provide useful code for [Mango Markets](https://mango.markets/).

There are some notebook pages to explore Mango account structures for your own accounts.

The aim is also to have, at some point, a fully-functioning liquidator.

The goal is not to be easy to use (although that would be nice!). The goal is to show you how the system works.


## Show your Mango margin accounts

To try this out, go to the [Show My Accounts](ShowMyAccounts.ipynb) page and enter your public key. (Note: I know you're running untrusted code, but it can't do much if you only give it your public key.)


## Show all Mango margin accounts

To try this out, go to the [Show All Accounts](ShowAllAccounts.ipynb) page and run the code.


## Load all margin accounts into a Pandas `DataFrame`

To try this out, go to the [Pandas](Pandas.ipynb) page and run the code.

[Pandas](https://pandas.pydata.org/) is a data analysis and manipulation tool and it's useful for sorting and slicing large data sets.

The [Pandas](Pandas.ipynb) page can currently show you:
* The total assets and liabilities currently in [Mango Markets](https://mango.markets/) margin accounts.
* The top ten margin accounts with the most assets.
* The top ten margin accounts with the most liabilities.
* The top ten margin accounts with the lowest collateralisation.


## Structure of this project

The code is (nearly) all Python in Jupyter Notebooks.

Some notebooks are more code files than useful notebooks themselves (although being able to easily run the code is still a boon):
* The [Layouts](Layouts.ipynb) notebook contains the low-level Python data structures for interpreting raw Solana program data.
* The [Classes](Classes.ipynb) notebook contains higher-level classes for loading and working with that data.

Other notebooks are more user-oriented:
* [Show My Accounts](ShowMyAccounts.ipynb) to show data pertaining to a single Mango Markets margin account.
* [Show All Accounts](ShowAllAccounts.ipynb) to show data for all Mango Markets margin accounts.
* [Pandas](Pandas.ipynb) to load data into a [Pandas](https://pandas.pydata.org/) `DataFrame` to allow for further manipulation and analysis.


## TODO

Still to come:
* More work on margin accounts and valuation
* Finding and showing liquidatable margin accounts
* A command-line tool to run a full liquidator
* Performance of code that loads all margin accounts is much too slow and needs to be improved.
* The notebooks use [hard-coded data from the Mango Client](https://raw.githubusercontent.com/blockworks-foundation/mango-client-ts/main/src/ids.json) - it would be good if it could do without that.

Don't hold your breath waiting for these!


# Support

You can contact me [@OpinionatedGeek on Twitter](https://twitter.com/OpinionatedGeek).
