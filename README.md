# Mango Explorer

## ⚠ Warning

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Run these notebooks on Binder: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gl/OpinionatedGeek%2Fmango-explorer/HEAD)


## Introduction

**I am not yet confident in the figures and calculations. Please don't rely on this code yet!**

This is the start of a project to explore and provide useful code for [Mango Markets](https://mango.markets/).

There are some notebook pages to explore Mango account structures for your own accounts.

The goal is not to be easy to use (although that would be nice!). The goal is to show you how the system works and allow you to use some simeple code to interact with it.


## Running the notebooks

Most notebooks are currently 'runnable' - if you open them in your browser and press the 'fast-forward' button (⏩) on the toolbar


## Verify a user's account is properly set up for Mango Markets liquidators

Mango Markets should set up your account automatically for trading, but the requirements for running a liquidator can be a bit more extensive. For instance, for trading you need token accounts for both tokens in the trade but to run a liquidator you need token accounts for all tokens in the `Group`.

The [AccountScout](AccountScout.ipynb) notebook can verify any user's root account to make sure it meets the requirements of the liquidator.


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


## References

* [🥭 Mango Markets](https://mango.markets/)
  * [Docs](https://docs.mango.markets/)
  * [Discord](https://discord.gg/67jySBhxrg)
  * [Twitter](https://twitter.com/mangomarkets)
  * [Github](https://github.com/blockworks-foundation)
  * [Email](mailto:hello@blockworks.foundation)
  * [Mango On-Chain Rust Code](https://github.com/blockworks-foundation/mango)
  * [Mango TypeScript Client](https://github.com/blockworks-foundation/mango-client-ts)
  * [Mango TypeScript Liquidator](https://github.com/blockworks-foundation/liquidator)
* [PySerum](https://github.com/serum-community/pyserum/)
* [SolanaPy](https://github.com/michaelhly/solana-py/)
* [Python Decimal Class](https://docs.python.org/3/library/decimal.html)
* [Python Construct Library](https://construct.readthedocs.io/en/latest/)
* [Pyston](https://www.pyston.org/)
* [Flux Aggregator](https://github.com/octopus-network/solana-flux-aggregator)


## TODO

Still to come:
* More work on margin accounts and valuation
* Performance of code that loads all margin accounts is much too slow and needs to be improved.
* The notebooks use [hard-coded data from the Mango Client](https://raw.githubusercontent.com/blockworks-foundation/mango-client-ts/main/src/ids.json) - it would be good if it could do without that.

Don't hold your breath waiting for these!


# Support

You can contact me [@OpinionatedGeek on Twitter](https://twitter.com/OpinionatedGeek).
