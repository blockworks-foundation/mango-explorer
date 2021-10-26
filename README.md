# 🥭 Mango Explorer

## ⚠ Warning

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Run these notebooks on Binder: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/blockworks-foundation/mango-explorer/v2)


## Introduction

**I am not yet confident in the figures and calculations. Please don't rely on this code yet!**

This is a project to explore and provide useful code for [Mango Markets](https://mango.markets/).

There are some notebook pages to explore Mango account structures for your own accounts.

There is also a functional liquidator.

The goal is not to be easy to use (although that would be nice!). The goal is to show you how the system works and allow you to use some simeple code to interact with it.


## Running the liquidator

Check out the [Quickstart](Quickstart.md) documentation - it's a walkthrough of setting up and running the liquidator, from creating the account, 'balancing' the wallet across the different tokens, and running the liquidator itself.

It can take around 30 minutes to run through.

Requirements:
* A server with docker installed
* Some SOL to pay for transactions
* Some USDT to fund the liquidation wallet


## Running the notebooks

Most notebooks are currently 'runnable' - if you open them in your browser and press the 'fast-forward' button (⏩) on the toolbar


## Verify a user's account is properly set up for Mango Markets liquidators

Mango Markets should set up your account automatically for trading, but the requirements for running a liquidator can be a bit more extensive. For instance, for trading you need token accounts for both tokens in the trade but to run a liquidator you need token accounts for all tokens in the `Group`.


## Show your Mango margin accounts

To try this out, go to the [Show Account](ShowAccount.ipynb) page and enter your public key. (Note: I know you're running untrusted code, but it can't do much if you only give it your public key.)


## Show all Mango margin accounts

To try this out, go to the [Show All Margin Accounts](ShowAllMarginAccounts.ipynb) page and run the code.


## Show details of the current Mango gorup

You can use the [Show Group](ShowGroup.ipynb) page to inspect the details of the current Mango group.


## Load all margin accounts into a Pandas `DataFrame`

To try this out, go to the [Pandas](Pandas.ipynb) page and run the code.

[Pandas](https://pandas.pydata.org/) is a data analysis and manipulation tool and it's useful for sorting and slicing large data sets.

The [Pandas](Pandas.ipynb) page can currently show you:
* The total assets and liabilities currently in [Mango Markets](https://mango.markets/) margin accounts.
* The top ten margin accounts with the most assets.
* The top ten margin accounts with the most liabilities.
* The top ten margin accounts with the lowest collateralisation.


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
* [Python Observables](https://rxpy.readthedocs.io/en/latest/)
* [RxPy Backpressure](https://github.com/daliclass/rxpy-backpressure)
* [Pyston](https://www.pyston.org/)
* [Flux Aggregator](https://github.com/octopus-network/solana-flux-aggregator)


# Support

You can contact me [@OpinionatedGeek on Twitter](https://twitter.com/OpinionatedGeek).
