# 🥭 Mango Explorer

## ⚠ Warning

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


## 🥭 Introduction

`mango-explorer` provides Python code to integrate with [Mango Markets](https://mango.markets).

It includes some useful command-line programs, such as:
* `deposit`
* `withdraw`
* `place-order`
* `market-buy`
* `market-sell`
* `send-tokens`

There are also more complex programs such as a runnable [marketmaker](docs/MarketmakingQuickstart.md) for Serum, Spot and Perp markets.


## 📦 Installation

![PyPI](https://img.shields.io/pypi/v/mango-explorer)

`mango-explorer` is available as a [Python package on Pypi](https://pypi.org/project/mango-explorer) and can be installed as:

```
pip install mango-explorer
```

A simple [installation walkthrough](docs/Installation.md) is available, and of course other ways of installing it or adding it as a dependency are possible and will depend on the particular tools you are using.

`mango-explorer` is also available as a docker container with the name [opinionatedgeek/mango-explorer-v3](https://hub.docker.com/repository/docker/opinionatedgeek/mango-explorer-v3/).


## 🌳 Branches

The latest version of the code is in the [main branch on Github](https://github.com/blockworks-foundation/mango-explorer).

Code to integrate with Version 2 of Mango is in the [v2 branch](https://github.com/blockworks-foundation/mango-explorer/tree/v2).


## 📓 Examples

Here are some example snippets to get you started.

Many more examples are provided in a separate [Github repo](https://github.com/blockworks-foundation/mango-explorer-examples) and can be [run in your browser (no installation required!) at Binder](https://mybinder.org/v2/gh/blockworks-foundation/mango-explorer-examples/HEAD).


### 🏃 Show OrderBook
> [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/blockworks-foundation/mango-explorer-examples/HEAD?labpath=ShowOrderBook.ipynb) [Full runnable code in `mango-explorer-examples` repo](https://github.com/blockworks-foundation/mango-explorer-examples/blob/main/ShowOrderBook.ipynb)

This code will connect to the _devnet_ cluster, fetch the orderbook for BTC-PERP, and print out a summary of it:
```
import mango

with mango.ContextBuilder.build(cluster_name="devnet") as context:
    market = mango.market(context, "BTC-PERP")
    print(market.fetch_orderbook(context))
```


### 🏃 Subscribe to OrderBook
> [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/blockworks-foundation/mango-explorer-examples/HEAD?labpath=SubscribeOrderBook.ipynb) [Full runnable code in `mango-explorer-examples` repo](https://github.com/blockworks-foundation/mango-explorer-examples/blob/main/SubscribeOrderBook.ipynb)

This code will connect to the _devnet_ cluster and will print out the latest orderbook every time the orderbook changes, and will exit after 60 seconds.
```
import datetime
import mango
import time

with mango.ContextBuilder.build(cluster_name="devnet") as context:
    market = mango.market(context, "BTC-PERP")
    subscription = market.on_orderbook_change(context, lambda ob: print("\n", datetime.datetime.now(), "\n", ob))

    time.sleep(60)

    subscription.dispose()
```


### 🏃 Show Perp Fills
> [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/blockworks-foundation/mango-explorer-examples/HEAD?labpath=ShowPerpFills.ipynb) [Full runnable code in `mango-explorer-examples` repo](https://github.com/blockworks-foundation/mango-explorer-examples/blob/main/ShowPerpFills.ipynb)

A 'fill' is when a maker order from the orderbook is matched with an incoming taker order. It can be useful to see these.

This code will connect to the _devnet_ cluster and fetch all recent events. It will then show all the fill events.
```
import mango

with mango.ContextBuilder.build(cluster_name="devnet") as context:
    market = mango.market(context, "BTC-PERP")
    event_queue = mango.PerpEventQueue.load(context, market.event_queue_address, market.lot_size_converter)
    print(event_queue.fills)
```


### 🏃 Subscribe to Fills
> [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/blockworks-foundation/mango-explorer-examples/HEAD?labpath=SubscribeFills.ipynb) [Full runnable code in `mango-explorer-examples` repo](https://github.com/blockworks-foundation/mango-explorer-examples/blob/main/SubscribeFills.ipynb)

This code will connect to the _devnet_ cluster and print out every fill that happens. It will exit after 60 seconds.
```
import datetime
import mango
import time

with mango.ContextBuilder.build(cluster_name="devnet") as context:
    market = mango.market(context, "BTC-PERP")
    subscription = market.on_fill(context, lambda ob: print("\n", datetime.datetime.now(), "\n", ob))

    time.sleep(60)

    subscription.dispose()
```

### 🏃 Place Order
> [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/blockworks-foundation/mango-explorer-examples/HEAD?labpath=PlaceOrder.ipynb) [Full runnable code in `mango-explorer-examples` repo](https://github.com/blockworks-foundation/mango-explorer-examples/blob/main/PlaceOrder.ipynb)

This code will load the 'example' wallet, connect to the _devnet_ cluster, place an order and wait for the order's transaction signature to be confirmed.

The order is an IOC ('Immediate Or Cancel') order to buy 2 SOL-PERP at $1. This order is unlikely to be filled (SOL currently costs substantially more than $1), but that saves having to show order cancellation code here.

Possible `order_type` values are:
* mango.OrderType.LIMIT
* mango.OrderType.IOC
* mango.OrderType.POST_ONLY
* mango.OrderType.MARKET (it's nearly always better to use IOC and a price with acceptable slippage)
* mango.OrderType.POST_ONLY_SLIDE (only available on perp markets)
```
import decimal
import mango

from solana.publickey import PublicKey

# Use our hard-coded devnet wallet for DeekipCw5jz7UgQbtUbHQckTYGKXWaPQV4xY93DaiM6h.
# For real-world use you'd load the bytes from the environment or a file. Later we use
# its Mango Account at HhepjyhSzvVP7kivdgJH9bj32tZFncqKUwWidS1ja4xL.
wallet = mango.Wallet(bytes([67,218,68,118,140,171,228,222,8,29,48,61,255,114,49,226,239,89,151,110,29,136,149,118,97,189,163,8,23,88,246,35,187,241,107,226,47,155,40,162,3,222,98,203,176,230,34,49,45,8,253,77,136,241,34,4,80,227,234,174,103,11,124,146]))

with mango.ContextBuilder.build(cluster_name="devnet") as context:
    group = mango.Group.load(context)
    account = mango.Account.load(context, PublicKey("HhepjyhSzvVP7kivdgJH9bj32tZFncqKUwWidS1ja4xL"), group)
    market_operations = mango.operations(context, wallet, account, "SOL-PERP", dry_run=False)

    # Try to buy 2 SOL for $1.
    order = mango.Order.from_values(side=mango.Side.BUY,
                                    price=decimal.Decimal(1),
                                    quantity=decimal.Decimal(2),
                                    order_type=mango.OrderType.IOC)
    print("Placing order:", order)
    placed_order_signatures = market_operations.place_order(order)

    print("Waiting for place order transaction to confirm...\n", placed_order_signatures)
    mango.WebSocketTransactionMonitor.wait_for_all(
            context.client.cluster_ws_url, placed_order_signatures, commitment="processed"
        )
```

### 🏃 Place and Cancel Order
> [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/blockworks-foundation/mango-explorer-examples/HEAD?labpath=PlaceAndCancelOrders.ipynb) [Full runnable code in `mango-explorer-examples` repo](https://github.com/blockworks-foundation/mango-explorer-examples/blob/main/PlaceAndCancelOrders.ipynb)

This code will load the 'example' wallet, connect to the _devnet_ cluster, place an order and then cancel it.

This is a bit longer than the Place Order example but only because it performs most of the Place Order code as a setup to create the order so there's an order to cancel.

The key point is that `cancel_order()` takes an `Order` as a parameter, and that `Order` needs either the `id` or `client_id` property to be set so the Mango program can find the equivalent order data on-chain. The sample code specified 1001 as the `client_id` when the order was instantiated so it's fine for use here.
```
import decimal
import mango

from solana.publickey import PublicKey

# Use our hard-coded devnet wallet for DeekipCw5jz7UgQbtUbHQckTYGKXWaPQV4xY93DaiM6h.
# For real-world use you'd load the bytes from the environment or a file. Later we use
# its Mango Account at HhepjyhSzvVP7kivdgJH9bj32tZFncqKUwWidS1ja4xL.
wallet = mango.Wallet(bytes([67,218,68,118,140,171,228,222,8,29,48,61,255,114,49,226,239,89,151,110,29,136,149,118,97,189,163,8,23,88,246,35,187,241,107,226,47,155,40,162,3,222,98,203,176,230,34,49,45,8,253,77,136,241,34,4,80,227,234,174,103,11,124,146]))

with mango.ContextBuilder.build(cluster_name="devnet") as context:
    group = mango.Group.load(context)
    account = mango.Account.load(context, PublicKey("HhepjyhSzvVP7kivdgJH9bj32tZFncqKUwWidS1ja4xL"), group)
    market_operations = mango.operations(context, wallet, account, "SOL-PERP", dry_run=False)

    print("Orders (initial):")
    print(market_operations.load_orderbook())

    order = mango.Order.from_values(side=mango.Side.BUY,
                                    price=decimal.Decimal(10),
                                    quantity=decimal.Decimal(1),
                                    order_type=mango.OrderType.POST_ONLY)
    print("Placing order:", order)
    placed_order_signatures = market_operations.place_order(order)

    print("Waiting for place order transaction to confirm...\n", placed_order_signatures)
    mango.WebSocketTransactionMonitor.wait_for_all(
            context.client.cluster_ws_url, placed_order_signatures, commitment="processed"
        )

    print("\n\nOrders (including our new order):")
    orderbook = market_operations.load_orderbook()
    print(orderbook)

    # Order has the client ID 1001 so we can use that Order object as a parameter here.
    cancellaton_signatures = market_operations.cancel_order(order)

    print("Waiting for cancel order transaction to confirm...\n", cancellaton_signatures)
    mango.WebSocketTransactionMonitor.wait_for_all(
            context.client.cluster_ws_url, cancellaton_signatures, commitment="processed"
        )

    print("\n\nOrders (without our order):")
    print(market_operations.load_orderbook())
```


### 🏃 Refresh Orders

Solana's transaction mechanism allows for atomic cancel-and-replace of orders - either the entire transaction succeeds (old orders are cancelled, new orders are placed), or the entire transaction fails (no orders are cancelled, no orders are placed).

Neither Serum nor Mango supports 'editing' or changing an order - to change the price or quantity for an order you must cancel it and replace it with an order with updated values.

This code will loop 3 times around:
* in one transaction: cancelling all perp orders and placing bid and ask perp orders on SOL-PERP
* wait for that transaction to confirm
* pause for 5 seconds

You can verify the transaction signatures in [Solana Explorer](https://explorer.solana.com/?cluster=devnet) to see there is a single transaction containing a `CancelAllPerpOrders` instruction followed by two `PlacePerpOrder2` instructions. Since they're all in the same transaction, they will all succeed or all fail - if any instruction fails, the previous instructions are not committed to the chain, as if they never happened.
```
import decimal
import mango
import time

from solana.publickey import PublicKey

# Use our hard-coded devnet wallet for DeekipCw5jz7UgQbtUbHQckTYGKXWaPQV4xY93DaiM6h.
# For real-world use you'd load the bytes from the environment or a file. Later we use
# its Mango Account at HhepjyhSzvVP7kivdgJH9bj32tZFncqKUwWidS1ja4xL.
wallet = mango.Wallet(bytes([67,218,68,118,140,171,228,222,8,29,48,61,255,114,49,226,239,89,151,110,29,136,149,118,97,189,163,8,23,88,246,35,187,241,107,226,47,155,40,162,3,222,98,203,176,230,34,49,45,8,253,77,136,241,34,4,80,227,234,174,103,11,124,146]))

with mango.ContextBuilder.build(cluster_name="devnet") as context:
    group = mango.Group.load(context)
    account = mango.Account.load(context, PublicKey("HhepjyhSzvVP7kivdgJH9bj32tZFncqKUwWidS1ja4xL"), group)
    market_operations = mango.operations(context, wallet, account, "SOL-PERP", dry_run=False)
    market_instructions: mango.PerpMarketInstructionBuilder = mango.instruction_builder(context, wallet, account, "SOL-PERP", dry_run=False)

    signers: mango.CombinableInstructions = mango.CombinableInstructions.from_wallet(wallet)

    for counter in range(3):
        print("\n\nOrders:")
        orderbook = market_operations.load_orderbook()
        print(orderbook)

        instructions = signers
        instructions += market_instructions.build_cancel_all_orders_instructions()
        buy = mango.Order.from_values(side=mango.Side.BUY,
                                      price=orderbook.top_bid.price,
                                      quantity=decimal.Decimal(1),
                                      order_type=mango.OrderType.POST_ONLY,
                                      client_id=counter+10)
        print(buy)
        instructions += market_instructions.build_place_order_instructions(buy)
        sell = mango.Order.from_values(side=mango.Side.SELL,
                                       price=orderbook.top_ask.price,
                                       quantity=decimal.Decimal(1),
                                       order_type=mango.OrderType.POST_ONLY,
                                       client_id=counter+20)
        print(sell)
        instructions += market_instructions.build_place_order_instructions(sell)

        signatures = instructions.execute(context)

        print("Waiting for refresh order transaction to confirm...\n", signatures)
        mango.WebSocketTransactionMonitor.wait_for_all(
                context.client.cluster_ws_url, signatures, commitment="processed"
            )

        print("Sleeping for 5 seconds...")
        time.sleep(5)

print("Cleaning up...")
instructions = signers
instructions += market_instructions.build_cancel_all_orders_instructions()

cleanup_signatures = instructions.execute(context)

print("Waiting for cleanup transaction to confirm...\n", cleanup_signatures)
mango.WebSocketTransactionMonitor.wait_for_all(
        context.client.cluster_ws_url, cleanup_signatures, commitment="processed"
    )

print("Example complete.")
```

### 🏃 Show Account Data
> [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/blockworks-foundation/mango-explorer-examples/HEAD?labpath=ShowAccountDataFrame.ipynb) [Full runnable code in `mango-explorer-examples` repo](https://github.com/blockworks-foundation/mango-explorer-examples/blob/main/ShowAccountDataFrame.ipynb)

This code will connect to the _devnet_ cluster and show important data from a Mango Account.

Data on deposits, borrows and perp positions are all available in a `pandas` `DataFrame` for you to perform your own calculations upon. The `Account` class also has some methods to take this `DataFrame` and run common calculations on it, such as calculating the total value of the `Account` (using `total_value()`), the health of the account (using `init_health()` and `maint_health()`), or the account's leverage (using `leverage()`).
```
import mango

from solana.publickey import PublicKey

with mango.ContextBuilder.build(cluster_name="devnet") as context:
    group = mango.Group.load(context)
    cache: mango.Cache = mango.Cache.load(context, group.cache)

    account = mango.Account.load(context, PublicKey("HhepjyhSzvVP7kivdgJH9bj32tZFncqKUwWidS1ja4xL"), group)
    open_orders = account.load_all_spot_open_orders(context)
    frame = account.to_dataframe(group, open_orders, cache)
    print(frame)
    print(f"Init Health: {account.init_health(frame)}")
    print(f"Maint Health: {account.maint_health(frame)}")
    print(f"Total Value: {account.total_value(frame)}")
    print(f"Leverage: {account.leverage(frame):,.2f}x")
```

### 🏃 Subscribe to Account changes
> [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/blockworks-foundation/mango-explorer-examples/HEAD?labpath=SubscribeAccount.ipynb) [Full runnable code in `mango-explorer-examples` repo](https://github.com/blockworks-foundation/mango-explorer-examples/blob/main/SubscribeAccount.ipynb)

This code will connect to the _devnet_ cluster and print out the Mango `Account` every time it changes. It will exit after 60 seconds.

The `subscribe()` method takes a lambda callback as a parameter - this lambda will be called with a new `Account` object when an update is received.

This code will exit after 60 seconds.

This pattern can also be used with `Group`, `Cache` and `EventQueue` objects.

**NOTE:** This will send an updated `Account` object, including whatever updated values triggered the update. However a proper valuation of an `Account` involves several more Mango data accounts so it's important to fetch all data fresh (including `Group`, `Cache` and all `OpenOrders`) to calculate values.
```
import datetime
import mango
import time

from solana.publickey import PublicKey

with mango.ContextBuilder.build(cluster_name="devnet") as context:
    # Load our devnet Random Taker Mango Account - it should have some activity
    group = mango.Group.load(context)
    account = mango.Account.load(context, PublicKey("5JDWiJGmnvs1DZomMV3s9Ev6DAgCQ9Svxd81EHCapjnD"), group)

    manager = mango.IndividualWebSocketSubscriptionManager(context)
    subscription = account.subscribe(context, manager, lambda acc: print(datetime.datetime.now(), "\n", acc))
    manager.open()

    time.sleep(60)

    manager.dispose()
```


### 🏃 Deposit
> [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/blockworks-foundation/mango-explorer-examples/HEAD?labpath=Deposit.ipynb) [Full runnable code in `mango-explorer-examples` repo](https://github.com/blockworks-foundation/mango-explorer-examples/blob/main/Deposit.ipynb)

This code will connect to the _devnet_ cluster and deposit 0.1 SOL into a Mango `Account`.
```
import decimal
import mango

from solana.publickey import PublicKey


# Use our hard-coded devnet wallet for DeekipCw5jz7UgQbtUbHQckTYGKXWaPQV4xY93DaiM6h.
# For real-world use you'd load the bytes from the environment or a file. This wallet
# has a Mango Account at HhepjyhSzvVP7kivdgJH9bj32tZFncqKUwWidS1ja4xL.
wallet = mango.Wallet(bytes([67,218,68,118,140,171,228,222,8,29,48,61,255,114,49,226,239,89,151,110,29,136,149,118,97,189,163,8,23,88,246,35,187,241,107,226,47,155,40,162,3,222,98,203,176,230,34,49,45,8,253,77,136,241,34,4,80,227,234,174,103,11,124,146]))

with mango.ContextBuilder.build(cluster_name="devnet") as context:
    group = mango.Group.load(context)
    account = mango.Account.load(context, PublicKey("HhepjyhSzvVP7kivdgJH9bj32tZFncqKUwWidS1ja4xL"), group)
    sol_token = mango.token(context, "SOL")

    print("Wrapped SOL in account", account.slot_by_instrument(sol_token).net_value)

    deposit_value = mango.InstrumentValue(sol_token, decimal.Decimal("0.1"))
    deposit_signatures = account.deposit(context, wallet, deposit_value)
    print("Waiting for deposit transaction to confirm...", deposit_signatures)
    mango.WebSocketTransactionMonitor.wait_for_all(
            context.client.cluster_ws_url, deposit_signatures, commitment="processed"
        )

    account = mango.Account.load(context, account.address, group)
    print("Wrapped SOL after deposit", account.slot_by_instrument(sol_token).net_value)
```


### 🏃 Withdraw
> [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/blockworks-foundation/mango-explorer-examples/HEAD?labpath=Withdraw.ipynb) [Full runnable code in `mango-explorer-examples` repo](https://github.com/blockworks-foundation/mango-explorer-examples/blob/main/Withdraw.ipynb)

This code will connect to the _devnet_ cluster and withdraw 0.1 SOL from a Mango `Account`.

Unlike `deposit()`, you specify an address as the destination. You can withdraw from your Mango `Account` to anyone's wallet (be careful!). Also, you can withdraw tokens even if you don't own them (as long as you have sufficient collateral) by borrowing them - `withdraw()`'s `allow_borrow` boolean allows or prohibits borrowing tokens the `Account` doesn't own.
```
import decimal
import mango

from solana.publickey import PublicKey


# Use our hard-coded devnet wallet for DeekipCw5jz7UgQbtUbHQckTYGKXWaPQV4xY93DaiM6h.
# For real-world use you'd load the bytes from the environment or a file. This wallet
# has a Mango Account at HhepjyhSzvVP7kivdgJH9bj32tZFncqKUwWidS1ja4xL.
wallet = mango.Wallet(bytes([67,218,68,118,140,171,228,222,8,29,48,61,255,114,49,226,239,89,151,110,29,136,149,118,97,189,163,8,23,88,246,35,187,241,107,226,47,155,40,162,3,222,98,203,176,230,34,49,45,8,253,77,136,241,34,4,80,227,234,174,103,11,124,146]))

with mango.ContextBuilder.build(cluster_name="devnet") as context:
    group = mango.Group.load(context)
    account = mango.Account.load(context, PublicKey("HhepjyhSzvVP7kivdgJH9bj32tZFncqKUwWidS1ja4xL"), group)
    sol_token = mango.token(context, "SOL")

    print("Wrapped SOL in account", account.slot_by_instrument(sol_token).net_value)

    withdraw_value = mango.InstrumentValue(sol_token, decimal.Decimal("0.1"))
    withdrawal_signatures = account.withdraw(context, wallet, wallet.address, withdraw_value, False)
    print("Waiting for withdraw transaction to confirm...", withdrawal_signatures)
    mango.WebSocketTransactionMonitor.wait_for_all(
            context.client.cluster_ws_url, withdrawal_signatures, commitment="processed"
        )

    account = mango.Account.load(context, account.address, group)
    print("Wrapped SOL after withdrawal", account.slot_by_instrument(sol_token).net_value)
```


## 🏛️ Running the marketmaker

There is a [Marketmaking Quickstart](docs/MarketmakingQuickstart.md) - a walkthrough of setting up and running the marketmaker on devnet, from setting up the account, depositing tokens, to running the marketmaker itself.

It can take around 30 minutes to run through.

Requirements:
* A server with docker installed

**Note** This walkthrough is devnet-only so no actual funds are used or at-risk.

## 🔖 References

* [SolanaPy](https://github.com/michaelhly/solana-py/)
* [PySerum](https://github.com/serum-community/pyserum/)
* [Python Decimal Class](https://docs.python.org/3/library/decimal.html)
* [Python Construct Library](https://construct.readthedocs.io/en/latest/)
* [Python Observables](https://rxpy.readthedocs.io/en/latest/)
* [RxPy Backpressure](https://github.com/daliclass/rxpy-backpressure)


## 🥭 Support

[🥭 Mango Markets](https://mango.markets/) support is available at: [Docs](https://docs.mango.markets/) | [Discord](https://discord.gg/67jySBhxrg) | [Twitter](https://twitter.com/mangomarkets) | [Github](https://github.com/blockworks-foundation) | [Email](mailto:hello@blockworks.foundation)
