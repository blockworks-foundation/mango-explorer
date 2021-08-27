# 🥭 Mango Explorer

_(This is very much a work in progress! Expect things to change frequently. The Python code shown here is available in the [Mango Explorer V3 branch](https://github.com/blockworks-foundation/mango-explorer/tree/v3).)_


# 🏛️  Marketmaking

Traders buy and sell, but it helps when there are reliable entities for them to trade against. And while an individual trader may buy or sell, they typically aren’t doing both at the same time on the same symbol. In contrast, a marketmaker places both buy and sell orders for the same symbol, producing a valuation of the symbol and saying how much they’d be willing to pay for some quantity, and how much they’d ask to part with some quantity. They _literally make a market_ by always providing a price at which someone can buy and a price at which someone can sell, and profit by the difference between the buy and sell prices - the ‘spread’.

How the marketmaker knows what prices to use, how much inventory to offer, and how to manage risk are all great questions that will not be adequately addressed here. Sorry. Successful marketmakers often guard their approaches and I just don’t know any of their secrets.

Instead, let’s look at the mechanics of marketmaking on 🥭 Mango.


# 📉 World’s Simplest Marketmaker

Let’s start with a really simple example. Here’s an [actual marketmaker](https://github.com/blockworks-foundation/mango-explorer/blob/v3/scripts/worlds-simplest-market-maker) that will cancel any existing orders, look up the current price on a market, place a BUY order below that price and a SELL order above that price, then pause, then go back to the beginning:
```
#!/usr/bin/env bash
MARKET=${1:-BTC-PERP}
FIXED_POSITION_SIZE=${2:-0.01}
FIXED_SPREAD=${3:-100}
SLEEP_BETWEEN_ORDER_PLACES=${4:-60}
ORACLE_MARKET=${MARKET//\-PERP/\/USDC}

printf "Running on market %s with position size %f and prices +/- %f from current price\nPress Control+C to stop...\n" $MARKET $FIXED_POSITION_SIZE $FIXED_SPREAD
while :
do
    cancel-my-orders --name "WSMM ${MARKET} (cancel)" --market $MARKET --log-level ERROR

    CURRENT_PRICE=$(fetch-price --provider serum --symbol $ORACLE_MARKET --log-level ERROR --cluster-name mainnet | cut -d"'" -f 2 | sed 's/,//')
    place-order --name "WSMM ${MARKET} (buy)" --market $MARKET --order-type LIMIT \
        --log-level ERROR --side BUY --quantity $FIXED_POSITION_SIZE --price $(echo "$CURRENT_PRICE - $FIXED_SPREAD" | bc)
    place-order --name "WSMM ${MARKET} (sell)" --market $MARKET --order-type LIMIT \
        --log-level ERROR --side SELL --quantity $FIXED_POSITION_SIZE --price $(echo "$CURRENT_PRICE + $FIXED_SPREAD" | bc)

    echo "Last ${MARKET} market-making action: $(date)" > /var/tmp/mango_healthcheck_worlds_simplest_market_maker
	sleep $SLEEP_BETWEEN_ORDER_PLACES
done
```
You can run this and watch it place orders!

For example this will run it on the *ETH-PERP* market, placing a BUY at the current Serum price minus $10 and a SELL at the current Serum price plus $10, both with a position size of 1 ETH. It will then pause for 30 seconds before cancelling those orders (if they haven’t been filled) and placing fresh orders:
```
mango-explorer worlds-simplest-market-maker ETH-PERP 1 10 30
```
That’s not bad for 21 lines of `bash` scripting! OK, the price-fetching is a bit contorted, but you can see it’s calling:
* `cancel-my-orders`
* `fetch-price`
* `place-order` (BUY)
* `place-order` (SELL)
* `sleep`


# 📈 A Better Simple Marketmaker

There are many obvious problems with that approach so let’s see if we can do better.

First of all let’s write it in Python instead of `bash`, and let’s put it in an object - `SimpleMarketMaker` - so that the methods can be overriddden allowing different functionality to be swapped in. Let’s try to be a bit smarter about inventory. And let’s add a check on orders to see if existing orders are OK - even though SOL is cheap there’s no point wasting money cancelling and adding identical orders.

The [full class is available](https://github.com/blockworks-foundation/mango-explorer/blob/v3/mango/simplemarketmaking/simplemarketmaker.py), but the guts of it are in this looped section:
```
try:
    # Update current state
    price = self.oracle.fetch_price(self.context)
    self.logger.info(f"Price is: {price}")
    inventory = self.fetch_inventory()

    # Calculate what we want the orders to be.
    bid, ask = self.calculate_order_prices(price)
    buy_quantity, sell_quantity = self.calculate_order_quantities(price, inventory)

    current_orders = self.market_operations.load_my_orders()
    buy_orders = [order for order in current_orders if order.side == mango.Side.BUY]
    if self.orders_require_action(buy_orders, bid, buy_quantity):
        self.logger.info("Cancelling BUY orders.")
        for order in buy_orders:
            self.market_operations.cancel_order(order)
        buy_order: mango.Order = mango.Order.from_basic_info(
            mango.Side.BUY, bid, buy_quantity, mango.OrderType.POST_ONLY)
        self.market_operations.place_order(buy_order)

    sell_orders = [order for order in current_orders if order.side == mango.Side.SELL]
    if self.orders_require_action(sell_orders, ask, sell_quantity):
        self.logger.info("Cancelling SELL orders.")
        for order in sell_orders:
            self.market_operations.cancel_order(order)
        sell_order: mango.Order = mango.Order.from_basic_info(
            mango.Side.SELL, ask, sell_quantity, mango.OrderType.POST_ONLY)
        self.market_operations.place_order(sell_order)

    self.update_health_on_successful_iteration()
except Exception as exception:
    self.logger.warning(
        f"Pausing and continuing after problem running market-making iteration: {exception} - {traceback.format_exc()}")

# Wait and hope for fills.
self.logger.info(f"Pausing for {self.pause} seconds.")
time.sleep(self.pause.seconds)
```
It’s following these steps:
* Fetch the current price
* Fetch the current inventory
* Calculate the desired price
* calculate the desired order size
* Fetch the marketmaker’s current orders
* If the desired BUY orders and existing orders don’t match, cancel and replace them
* If the desired SELL orders and existing orders don’t match, cancel and replace them
* Pause

You can see this is similar to the steps in the World’s Simplest Marketmaker (above), but it’s a bit more complete. Instead of using a fixed position size, it varies it based on inventory. Instead of blindly cancelling orders, it checks to see if the current orders are what it wants them to be.


# 🍳 A Tangent On Market Operations

It’s worth highlighting the use of a `MarketOperations` object in the `SimpleMarketMaker`. Lines like:
```
self.market_operations.place_order(buy_order)
```
show a simple interface to market actions that makes for nice, readable code.

What it hides, though, is that the marketmaker can work with 3 different market types:
* Serum
* Mango Spot
* Mango Perp

The `market_operations` object is loaded based on the desired market, so it doesn’t matter (much) to the marketmaker if the market is Spot or Serum, it still follows the same steps and the `market_operations` takes action on the right market using the right instructions.

Behind the scenes, a similar variance happens with `MarketInstructions`. The actual instructions sent to Solana vary significantly depending on market type, but by having a unified `MarketInstructions` interface those differences can be largely hidden from marketmaking code. (It’s not perfect but this commonality does help in most situations.)

This can serve as a kind of a Rosetta Stone for Mango. If you know and understand the instructions sent to Serum to place orders, cancel them, or crank the market, you can look at `SerumMarketInstructions` to see how those instructions are implemented in 🥭 Mango Explorer. Then you can compare that file with `SpotMarketInstructions` to see what bits are different for Spot markets (that require Mango Accounts) and what bits are similar. And then you can explore `PerpMarketInstructions` to see how those same actions are performed on perp markets.


# 🚀 A More Complete Marketmaker

We’ve seen a common structure in the previous marketmakers, so let’s see if we can provide a nice, common approach for actual marketmaking that allows people to write their own strategies for the interesting bits but that has most of the required code already in place.

The main design ideas behind the design are:
* every interval, a ‘pulse’ is sent to run the marketmaker code
* the marketmaker is provided with relevant ‘live’ data (like balances) but can fetch whatever other information it requires
* the main pluggable component is a ‘desired orders builder’. It looks at the state of balances, market, or other data sources, and it provides a list of BUY and SELL orders it would like to see on the orderbook.
* another component (also pluggable) compares the desired orders with any existing orders, and decides which orders need to be placed or cancelled.

Live data is provided as a `ModelState` parameter to the `pulse()` method, and it’s kept live by polling or a websocket connection that watches for changes in the underlying accounts. That doesn’t matter (much) to the marketmaker code, it can just assume the `ModelState` parameter provides up-to-date information on balances, group, prices etc.

The `pulse()` method is called, say, every 30 seconds (again, it’s configurable). The current version of it looks like this:
```
def pulse(self, context: mango.Context, model_state: ModelState):
    try:
        payer = mango.CombinableInstructions.from_wallet(self.wallet)

        desired_orders = self.desired_orders_builder.build(context, model_state)
        existing_orders = self.order_tracker.existing_orders(model_state)
        reconciled = self.order_reconciler.reconcile(model_state, existing_orders, desired_orders)

        cancellations = mango.CombinableInstructions.empty()
        for to_cancel in reconciled.to_cancel:
            self.logger.info(f"Cancelling {self.market.symbol} {to_cancel}")
            cancel = self.market_instruction_builder.build_cancel_order_instructions(to_cancel, ok_if_missing=True)
            cancellations += cancel

        place_orders = mango.CombinableInstructions.empty()
        for to_place in reconciled.to_place:
            desired_client_id: int = context.random_client_id()
            to_place_with_client_id = to_place.with_client_id(desired_client_id)
            self.order_tracker.track(to_place_with_client_id)

            self.logger.info(f"Placing {self.market.symbol} {to_place_with_client_id}")
            place_order = self.market_instruction_builder.build_place_order_instructions(to_place_with_client_id)
            place_orders += place_order

        crank = self.market_instruction_builder.build_crank_instructions([])
        settle = self.market_instruction_builder.build_settle_instructions()
        (payer + cancellations + place_orders + crank + settle).execute(context, on_exception_continue=True)

        self.pulse_complete.on_next(datetime.now())
    except Exception as exception:
        self.logger.error(f"[{context.name}] Market-maker error on pulse: {exception} - {traceback.format_exc()}")
        self.pulse_error.on_next(exception)
```
Again you can see the same steps:
* Build a list of desired orders
* Get the existing orders
* Compare them and decide what orders to place

What’s different here is:
* Desired orders are built using a `DesiredOrdersBuilder` object, and most people will probably want to provide their own version with their own strategy.
* Existing orders are tracked, rather than having to be fetched.
* Desired and existing orders are compared using an `OrderReconciler`. The default version takes a `tolerance` value and if an existing order has the same side (BUY or SELL) and both price and quantity are within the `tolerance` of a desired order, the existing order remains on the orderbook and the desired order is ignored.
* The code builds a list of instructions, and they’re executed in one step. This is faster, more efficient, and can allow cancels and places to happen in the same transaction. (Instruction szie can mean this doesn’t happen though, but the `execute()` method takes this into account and uses as many transactions as necessary.)

You can see the different parameters the marketmaker takes by running:
```
mango-explorer marketmaker --help
```
You can run a basic instance of the marketmaker against the BTC-PERP market using [Pyth](https://pyth.network/) with:
```
mango-explorer marketmaker --market BTC/USDC --oracle-provider pyth-mainnet --position-size-ratio 0.01
```


# ⏭️ Next Steps

We started by saying what prices to use, how much inventory to offer, and how to manage risk are all great questions that will not be adequately addressed here.

They’re up to you.

For now the code is in the [Mango Explorer V3 branch](https://github.com/blockworks-foundation/mango-explorer/tree/v3). Happy marketmaking!