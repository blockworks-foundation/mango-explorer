# 🥭 Mango Explorer

# 🏃‍ Marketmaking Order Chain

The [Marketmaking Introduction](MarketmakingIntroduction.md) talks a bit about marketmaking generally but here we're going to focus specifically on building orders.

A marketmaker wants to ensure the orderbook contains orders with the values it wants. It does this with two phases:
1. Build a set of 'desired orders' - the orders it wants to see on the orderbook
2. Reconcile those desired orders with the existing orders on the orderbook, placing and cancelling orders as appropriate

The 'order chain' deals solely with the first part - building a set of desired orders.


## What Is An Order Chain?

An order chain is a sequence of `Element` objects, each of which, in turn, gets a chance to see and modify the desired order list before the marketmaker processes them.

The first `Element` is usually the one responsible for creating the orders for subsequent `Element`s to modify, but that's just a convention. Any `Element` can add desired orders.

`Element`s are called with a `Context`, the current `ModelState`, and the list of desired `Order`s. It performs its duties, and then returns the updated list of desired `Order`s.

When there are no more `Element`s in the `Chain`, the desired orders are passed to the `MarketMaker` itself for reconciliation with existing orders.


## The Default ‘Chain’

Usually the head of the marketmaker ‘chain’ creates some desired orders, and they may be modified by subsequent elements in the chain.

The default chain is (in order):
- `confidenceinterval`
- `biasquoteonposition`
- `minimumcharge`
- `preventpostonlycrossingbook`
- `roundtolotsize`

It's possible to specify a different `Chain` on the command line.

**Note**: it's not possbile to modify the default chain on the command line. The default chain is what is used if no chain is specified. If you specify any part of a chain, what you specify will replace the use of the default chain entirely: if you want to change any part of the default chain, you must specify the entire chain you want.


## Specifying A Different Chain

The default chain is equivalent to specifying:
```
--chain confidenceinterval --chain biasquoteonposition --chain minimumcharge --chain preventpostonlycrossingbook --chain roundtolotsize
```

To specify a different chain, you must specify on the command-line each chain element you want to use, in order.

For example, to specify a chain similar to the default chain but without the `BiasQuoteOnPosition` element, you would add the following parameters to the marketmaker command-line:
```
--chain confidenceinterval --chain minimumcharge --chain preventpostonlycrossingbook --chain roundtolotsize
```

Don't forget - if you want to change any part of the default chain, you must specify the full chain you want to use.


## Chain Heads

Currently only two elements - `ratios` and `confidenceinterval` - create orders. The remaining elements modify orders that are passed to them. Since each 'pulse' starts with no desired orders, that means the first element of the chain (or 'head of the chain') must be either `ratios` or `confidenceinterval`. Subsequent elements in the chain can modify the orders.


## Example Chain

Here's a completely different chain. This chain will specify orders with a spread of 0.5% and a position size of 2:
```
--chain ratios --ratios-spread 0.005 --chain fixedpositionsize --fixedpositionsize-value 2
```
The lack of a `roundtolotsize` element means positions won't be rounded to lot sizes when being sent to the marketmaker (so reconciling orders won't work as well as it might) but they'll be properly rounded when placed. 

The lack of a `preventpostonlycrossingbook` element means there's no specific handling of a POST_ONLY order that would cross the orderbook. That means those orders (since they're POST_ONLY) will be implicitly cancelled - this default behaviour may be exactly what you want.

Alternatively, both those elements can be added to the end to give the following chain parameters:
```
--chain ratios --ratios-spread 0.005 --chain fixedpositionsize --fixedpositionsize-value 2 --chain preventpostonlycrossingbook --chain roundtolotsize
```


## Element Reference

Here's a list of all available `Element`s and the additional configuration parameters they can take.

**Note**: In general, any parameters for a specific element have the name --*elementname*-parametername to help distinguish them and the element they operate upon.


### `AfterAccumulatedDepthElement`

> Specified using: `--chain afteraccumulateddepth`

> Accepts parameter: `--afteraccumulateddepth-depth <DECIMAL>` (optional, default: order quantity)

> Accepts parameter: `--afteraccumulateddepth-adjustment-ticks <DECIMAL>` (optional, default: 1)

Tries to place an order on the orderbook with sufficient quantity on orders between it and the mid-price.

Basically, if an order is for quantity X then this element will start at the top of the book and move down orders until the accumulated quantity from orders is greater than the quantity of the desired order.

E.g. if an order is for 1 BTC, the order will be priced so that there is at least 1 BTC's worth of orders between its price and the mid-price.

The `--afteraccumulateddepth-depth` parameter can be used to specify a fixed depth to position orders rather than the order quantity. (The order quantity is used if this parameter is not specified.)

The `--afteraccumulateddepth-adjustment-ticks` parameter allows you to specify how far (in ticks) from the accumulated depth to position the order. The default is 1 tick above for a SELL, 1 tick below for a BUY. Use 0 to specify placing the order AT the depth.


### `BiasQuantityOnPositionElement`

> Specified using: `--chain biasquantityonposition`

> Accepts parameter: `--biasquantityonposition-maximum-position <DECIMAL>` (required)

> Accepts parameter: `--biasquantityonposition-target-position <DECIMAL>` (optional, default: 0)

Varies the order quantities to favour a target position.

This `Element` looks at the _current position_, the _maximum desired position_, and the _target position_. Tries to bias the order quantity to tend towards the target position, incresing the order quantities that shift it in that direction and decreasing the order quantities that shift it away from the target.

For example(1):
* BUY quantity: 10
* SELL quantity: 10
* CURRENT position: 0
* MAXIMUM position: 50
* TARGET position: 0
* Result: no change in order quantities

For example(2):
* BUY quantity: 10
* SELL quantity: 10
* CURRENT position: 20
* MAXIMUM position: 50
* TARGET position: 0
* Result:
  * BUY quantity: 6
  * SELL quantity: 14

In example (2) you can see:
* the current position of 20 means BUY quantity has decreased and SELL quantity has increased
* the total quantity in BUY and SELL stays the same, at 20

More examples (including all data used in unit tests) are available in the [BiasQuantityOnPosition](docs/BiasQuantityOnPosition.ods) spreadsheet.


### `BiasQuoteElement`

> Specified using: `--chain biasquote`

> Accepts parameter: `--biasquote-factor <DECIMAL>` (optional, multiple allowed, default: 1)

This shifts the price of orders by a specified factor.

Prices are multiplied by the factor parameter, so a factor of less than 1 will reduce `Order` prices (tending to SELL more) and a number greater than 1 will increase `Order` prices (tending to BUY more). For example, use a factor of 1.001 to increase prices by 10 bips.

The default factor is 1, meaning no changes will be made to orders.

`--biasquote-factor` can be specified multiple times for configurations running multiple layers or levels of `Order`s.

Specifying multiple bias factors is designed to work in an intuitive way - the first BUY and SELL take the first specified bias factor, the second BUY and SELL take the second specified bias factor and so on.

To do so, this element will:
* Separate BUY and SELL `Order`s
* Sort the BUY and SELL `Order`s from closest to top-of-book to farthest from top-of-book
* Process each BUY and SELL pair using the next specified bias factor (substituting the last specified bias factor if no other one is available)

The result is if you specify `--biasquote-factor 0.0002 --biasquote-factor 0.0004` the BUY and SELL `Order`s closest to top-of-book will both use a bias factor of 0.0002, and the next BUY and SELL `Order`s will use a bias factor of 0.0004.

(In fact, in that example, the BUY and SELL nearest the mid-price will use a bias factor of 0.0002, and all other `Order`s will use a bias factor of 0.0004.)

Note that one consequence of this processing of `Order`s is that the orders returned from this `Element` may be in a different sort-order to the orders that were sent to it.


### `BiasQuoteOnPositionElement`

> Specified using: `--chain biasquoteonposition`

> Accepts parameter: `--biasquoteonposition-bias <DECIMAL>` (optional, multiple allowed, default: 0)

This can shift the price of orders based on how much inventory is held. Too much inventory: bias prices down (so it tends to buy less and sell more). Too little inventory: bias prices up (so it tends to buy more and sell less).

The default bias is 0, meaning no changes will be made to orders. You can change this using the `-biasquoteonposition-bias` parameter. This should be a small, positive number - for example 0.00003 can shift the order price significantly.

`--biasquoteonposition-bias` can be specified multiple times for configurations running multiple layers or levels of `Order`s.

Specifying multiple biases is designed to work in an intuitive way - the first BUY and SELL take the first specified bias, the second BUY and SELL take the second specified bias and so on.

To do so, this element will:
* Separate BUY and SELL `Order`s
* Sort the BUY and SELL `Order`s from closest to top-of-book to farthest from top-of-book
* Process each BUY and SELL pair using the next specified bias (substituting the last specified bias if no other one is available)

The result is if you specify `--biasquoteonposition-bias 0.0002 --biasquoteonposition-bias 0.0004` the BUY and SELL `Order`s closest to top-of-book will both use a bias of 0.0002, and the next BUY and SELL `Order`s will use a bias of 0.0004.

(In fact, in that example, the BUY and SELL nearest the mid-price will use a bias factor of 0.0002 when calculating the bias using the current position, and all other `Order`s will use a bias factor of 0.0004 when calculating the bias using the current position.)

Note that one consequence of this processing of `Order`s is that the orders returned from this `Element` may be in a different sort-order to the orders that were sent to it.


### `ConfidenceIntervalElement`

> Specified using: `--chain confidenceinterval`

> Accepts parameter: `--confidenceinterval-level <DECIMAL>`  (optional, multiple allowed, default: 2)

> Accepts parameter: `--confidenceinterval-position-size-ratio <DECIMAL>` (required)

The `ConfidenceIntervalElement` uses the ‘confidence interval’ in the oracle price to determine the spread. How aggressively this is used can be tuned by the `--confidenceinterval-level` parameter.

This 'level' is weighting to apply to the confidence interval from the oracle: e.g. 1 - use the oracle confidence interval as the spread, 2 (risk averse, default) - multiply the oracle confidence interval by 2 to get the spread, 0.5 (aggressive) halve the oracle confidence interval to get the spread.

The ‘confidence interval’ is Pyth’s expectation of how far from the current mid-price the next trade will occur. If you use a ‘confidence weighting’ parameter of 2, this confidence interval is doubled and then added to the mid-price to get the sell price for the order and subtracted from the mid-price to get the buy price for the order.

- Using a confidence weighting of 1 just uses the confidence interval to create the spread
- Using a confidence weighting of 2 (the default) doubles the width of the spread
- Using a confidence weighting of 0.5 halves the width of the spread (and so is more aggressive)

**Important note:** this can be specified multiple times on the command line, so you can have orders placed at, say, 1x, 2x and 5x the confidence interval, placing/checking 6 orders in total each pulse (3 BUYs, 3 SELLs).


### `FixedPositionSizeElement`

> Specified using: `--chain fixedpositionsize`

> Accepts parameter: `--fixedpositionsize-value <DECIMAL>` (required, multiple allowed)

The `FixedPositionSizeElement` overrides the position size of all orders it sees, setting them to the fixed value (in the base currency) specified in the parameter(s).

For example, adding:
```
--chain fixedpositionsize --fixedpositionsize-value 3
```
to a chain on ETH/USDC will force all BUY and SELL orders to have a position size of 3 ETH.

`--fixedpositionsize-value` can be specified multiple times for configurations running multiple layers or levels of `Order`s.

Specifying multiple fixed position sizes is designed to work in an intuitive way - the first BUY and SELL take the first specified position size, the second BUY and SELL take the second specified position size and so on.

To do so, this element will:
* Separate BUY and SELL `Order`s
* Sort the BUY and SELL `Order`s from closest to top-of-book to farthest from top-of-book
* Process each BUY and SELL pair using the next specified position size (substituting the last specified position size if no other one is available)

The result is if you specify `--fixedpositionsize-value 2 --fixedpositionsize-value 4` the BUY and SELL `Order`s closest to top-of-book will both be given a fixed position size of 2, and the next BUY and SELL `Order`s will be given a fixed position size of 4.

(In fact, in that example, the BUY and SELL nearest the mid-price will be given a position size of 2 and all other `Order`s will be given a position size of 4.)

Note that one consequence of this processing of `Order`s is that the orders returned from this `Element` may be in a different sort-order to the orders that were sent to it.


### `FixedSpreadElement`

> Specified using: `--chain fixedspread`

> Accepts parameter: `--fixedspread-value <DECIMAL>` (required, multiple allowed)

The `FixedSpreadElement` overrides the spread of all orders it sees, setting them to the fixed value (in the quote currency) specified in the parameter.

For example, adding:
```
--chain fixedspread --fixedspread-value 0.5
```
to a chain on ETH/USDC will force the spread on BUY and SELL orders to be 0.5 USDC, meaning the BUY price will be the mid-price *minus* half the --fixedspread-value, and the SELL price will be the mid-price *plus* half the --fixedspread-value.

`--fixedspread-value` can be specified multiple times for configurations running multiple layers or levels of `Order`s.

Specifying multiple fixed spreads is designed to work in an intuitive way - the first BUY and SELL take the first specified spread, the second BUY and SELL take the second specified spread and so on.

To do so, this element will:
* Separate BUY and SELL `Order`s
* Sort the BUY and SELL `Order`s from closest to top-of-book to farthest from top-of-book
* Process each BUY and SELL pair using the next specified spread (substituting the last specified spread if no other one is available)

The result is if you specify `--fixedspread-value 2 --fixedspread-value 4` the BUY and SELL `Order`s closest to top-of-book will both be given a fixed spread of 2, and the next BUY and SELL `Order`s will be given a fixed spread of 4.

(In fact, in that example, the BUY and SELL nearest the mid-price will be given a spread of 2 and all other `Order`s will be given a spread of 4.)

Note that one consequence of this processing of `Order`s is that the orders returned from this `Element` may be in a different sort-order to the orders that were sent to it.


### `MaximumQuantityElement`

> Specified using: `--chain maximumquantity`

> Accepts parameter: `--maximumquantity-size <DECIMAL>` (required)

> Accepts parameter: `--maximumquantity-remove` (optional, TRUE if specified otherwise FALSE)

Ensures orders' quantities are always less than the maximum. Will either:
* Remove the order if the position size is too high, or
* Set the too-high position size to the permitted maximum

This `Element` examines every order to make sure the order quantity is less than or equal to the `--maximumquantity-size`. If it is less, this `Element` takes no further action on it.

If the order quantity is greater than `--maximumquantity-size`, then either:

1. (default) the order quantity will be reduced to the value specified by `--maximumquantity-size`.
2. (if `--maximumquantity-remove` is specified) the order will be removed from further processing and so will not be placed.


### `MinimumChargeElement`

> Specified using: `--chain minimumcharge`

> Accepts parameter: `--minimumcharge-ratio <DECIMAL>` (required, multiple allowed, default: 0.0005)

> Accepts parameter: `--minimumcharge-from-bid-ask` (optional, TRUE if specified otherwise FALSE)

This ensures that there’s a minimum value of spread to be paid by the taker.

It’s possible that the configuration may lead to too small a spread to be profitable. You can use the `--minimumcharge-ratio` parameter to enforce a minimum spread. The default of 0.0005 is 0.05%.

The default is to perform calculations based on the mid price. The `--minimumcharge-from-bid-ask` parameter specifies calculations are to be performed using the bid price (for BUYs) or ask price (for SELLs), not the mid price.

`--minimumcharge-ratio` can be specified multiple times for configurations running multiple layers or levels of `Order`s.

Specifying multiple minimum charges is designed to work in an intuitive way - the first BUY and SELL take the first specified position size, the second BUY and SELL take the second specified position size and so on.

To do so, this element will:
* Separate BUY and SELL `Order`s
* Sort the BUY and SELL `Order`s from closest to top-of-book to farthest from top-of-book
* Process each BUY and SELL pair using the next specified minimum charge (substituting the last specified minimum charge if no other one is available)

The result is if you specify `--minimumcharge-ratio 2 --minimumcharge-ratio 4` the BUY and SELL `Order`s closest to top-of-book will both be given a minimum charge of 2, and the next BUY and SELL `Order`s will be given a fixed minimum charge of 4.

(In fact, in that example, the BUY and SELL nearest the mid-price will be given a minimum charge of 2 and all other `Order`s will be given a minimum charge of 4.)

Note that one consequence of this processing of `Order`s is that the orders returned from this `Element` may be in a different sort-order to the orders that were sent to it.


### `MinimumQuantityElement`

> Specified using: `--chain minimumquantity`

> Accepts parameter: `--minimumquantity-size <DECIMAL>` (required)

> Accepts parameter: `--minimumquantity-remove` (optional, TRUE if specified otherwise FALSE)

Ensures orders' quantities are always greater than the minimum. Will either:
* Remove the order if the position size is too low, or
* Set the too-low position size to the permitted minimum

This `Element` examines every order to make sure the order quantity is greater than or equal to the `--minimumquantity-size`. If it is greater, this `Element` takes no further action on it.

If the order quantity is less than `--minimumquantity-size`, then either:

1. (default) the order quantity will be increased to the value specified by `--minimumquantity-size`.
2. (if `--minimumquantity-remove` is specified) the order will be removed from further processing and so will not be placed.


### `PreventPostOnlyCrossingBookElement`

> Specified using `--chain preventpostonlycrossingbook`

This ensures that POST_ONLY orders that would corss the orderbook (and so be cancelled instead of put on the book) are placed *just* inside the spread by 1 tick.


### `QuoteSingleSideElement`

> Specified using: `--chain quotesingleside`

> Accepts parameter: `--quotesingleside-side <SIDE>` (required, side can be BUY or SELL)

Sometimes you may only want your marketmaker to place SELL orders. Or only place BUY orders. The `QuoteSingleSideElement` allows you to specify a single side, and will filter out all desired orders that are not for that side.

For example, you can set the 'order chain' to have a `RatiosElement` asking for orders with spreads at 0.5%, 0.7%, and 0.9% (which would produce 6 orders - 3 BUYs and 3 SELLs), and then use a `QuoteSingleSideElement` with a `side` of `SELL` which would remove the 3 BUYs from the desired orders leaving only the 3 SELLs.


### `RatiosElement`

> Specified using: `--chain ratios`

> Accepts parameter: `--ratios-spread <DECIMAL>` (required, multiple allowed, default: 0.01)

> Accepts parameter: `--ratios-position-size <DECIMAL>` (required, multiple allowed, default: 0.01)

> Accepts parameter: `--ratios-from-bid-ask` (optional, TRUE if specified otherwise FALSE)

The `RatiosElement` builds orders using the specified ratio of available collateral for the position size and the specified ratio of the price for the spread. The position size is specified using the `--ratios-position-size` parameter, and the spread is specified using the `--ratios-spread` parameter.

It is possible to 'layer' orders by specifying the `--ratios-position-size` and `--ratios-spread` parameters multiple times. **Note**: both parameters must be specified the same number of times - for example, it is an error to specify 3 position size ratios and only 2 spread ratios.

The default is to perform calculations based on the mid price. The `--ratios-from-bid-ask` parameter specifies spread calculations are to be performed using the bid price (for BUYs) or ask price (for SELLs), not the mid price.


### `RoundToLotSizeElement`

> Specified using `--chain roundtolotsize`

This ensures prices and quantities are properly rounded to lot sizes. This can make the order reconciliation process more reliable since exact matches can be found for rounded orders while non-rounded orders may need more tolerance.

If a `price` or `quantity` rounds to zero, the `Order` is removed. (Sending such an `Order` would generate an error and fail the whole transaction.)


### `TopOfBookElement`

> Specified using: `--chain topofbook`

> Accepts parameter: `--topofbook-adjustment-ticks <DECIMAL>` (optional, default: 1)

Tries to move the order to the top of the orderbook.

Basically, this element looks at the current orderbook for the best bid or ask that isn't owned by the current account, then it shifts the order price so it is 1 tick better than that best bid or ask.

E.g. if the top bid on an orderbook is 50, this element will shift a BUY order so it is 1 tick better with a price of 51. Similarly if the top ask on an orderbook is 60, this element will shift a SELL order so it is 1 tick better with a price of 59. (If the order on the orderbook is owned by the account running the marketmaker, it is ignored by this element so it will never try to out-do its own orders.)

The `--topofbook-adjustment-ticks` parameter allows you to specify how far (in ticks) from the current best order to position the order. The default is 1 tick - 1 tick below for a SELL, 1 tick above for a BUY. Use 0 to specify placing the order AT the current best.
