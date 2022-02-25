# 🥭 Mango Explorer

## ⚠ Warning

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


## Introduction

`mango-explorer` provides Python code to interface with [Mango Markets](https://mango.markets), along with a functional [marketmaker](docs/MarketmakingQuickstart.md).


## Installation

![PyPI](https://img.shields.io/pypi/v/mango-explorer)

`mango-explorer` is available as a [Python package on Pypi](https://pypi.org/project/mango-explorer) and can be installed as:

```
pip install mango-explorer
```

A simple [installation walkthrough](docs/Installation.md) is available, and of course other ways of installing it or adding it as a dependency are possible and will depend on the particular tools you are using.

`mango-explorer` is also available as a docker container with the name [opinionatedgeek/mango-explorer-v3](https://hub.docker.com/repository/docker/opinionatedgeek/mango-explorer-v3/).


## Branches

The latest version of the code is in the [main branch on Github](https://github.com/blockworks-foundation/mango-explorer).

Code to integrate with Version 2 of Mango is in the [v2 branch](https://github.com/blockworks-foundation/mango-explorer/tree/v2).


## Example

Here's a brief but complete example of how to place and cancel an order. [This example is runnable in your browser](https://mybinder.org/v2/gh/blockworks-foundation/mango-explorer-examples/HEAD?labpath=PlaceAndCancelOrders.ipynb)!

```
import decimal
import mango
import os
import time

# Load the wallet from the environment variable 'KEYPAIR'. (Other mechanisms are available.)
wallet = mango.Wallet(os.environ.get("KEYPAIR"))

# Create a 'devnet' Context
context = mango.ContextBuilder.build(cluster_name="devnet")

# Load the wallet's account
group = mango.Group.load(context)
accounts = mango.Account.load_all_for_owner(context, wallet.address, group)
account = accounts[0]

# Load the market operations
market_operations = mango.operations(context, wallet, account, "SOL-PERP", dry_run=False)

print("Initial order book:\n\t", market_operations.load_orderbook())
print("Your current orders:\n\t", market_operations.load_my_orders(include_expired=True))

# Go on - try to buy 1 SOL-PERP contract for $10.
order = mango.Order.from_values(side=mango.Side.BUY,
                                price=decimal.Decimal(10),
                                quantity=decimal.Decimal(1),
                                order_type=mango.OrderType.POST_ONLY)
placed_order = market_operations.place_order(order)
print("\n\nPlaced order:\n\t", placed_order)

print("\n\nSleeping for 10 seconds...")
time.sleep(10)

print("\n\nOrder book (including our new order):\n", market_operations.load_orderbook())
print("Your current orders:\n\t", market_operations.load_my_orders(include_expired=True))

cancellation_signatures = market_operations.cancel_order(placed_order)
print("\n\nCancellation signature:\n\t", cancellation_signatures)

print("\n\nSleeping for 10 seconds...")
time.sleep(10)

print("\n\nOrder book (without our order):\n", market_operations.load_orderbook())
print("Your current orders:\n\t", market_operations.load_my_orders(include_expired=True))

```

Many more examples are provided in a separate [Github repo](https://github.com/blockworks-foundation/mango-explorer-examples) and can be [run in your browser (no installation required!) at Binder](https://mybinder.org/v2/gh/blockworks-foundation/mango-explorer-examples/HEAD).


## Running the marketmaker

There is a [Marketmaking Quickstart](docs/MarketmakingQuickstart.md) - a walkthrough of setting up and running the marketmaker on devnet, from setting up the account, depositing tokens, to running the marketmaker itself.

It can take around 30 minutes to run through.

Requirements:
* A server with docker installed

**Note** This walkthrough is devnet-only so no actual funds are used or at-risk.

## References

* [SolanaPy](https://github.com/michaelhly/solana-py/)
* [PySerum](https://github.com/serum-community/pyserum/)
* [Python Decimal Class](https://docs.python.org/3/library/decimal.html)
* [Python Construct Library](https://construct.readthedocs.io/en/latest/)
* [Python Observables](https://rxpy.readthedocs.io/en/latest/)
* [RxPy Backpressure](https://github.com/daliclass/rxpy-backpressure)


# Support

[🥭 Mango Markets](https://mango.markets/) support is available at: [Docs](https://docs.mango.markets/) | [Discord](https://discord.gg/67jySBhxrg) | [Twitter](https://twitter.com/mangomarkets) | [Github](https://github.com/blockworks-foundation) | [Email](mailto:hello@blockworks.foundation)
