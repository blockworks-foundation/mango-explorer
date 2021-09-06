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

Tries to place an order on the orderbook with sufficient quantity on orders between it and the mid-price.

Basically, if an order is for quantity X then this element will start at the top of the book and move down orders until the accumulated quantity from orders is greater than the quantity of the desired order.

E.g. if an order is for 1 BTC, the order will be priced so that there is at least 1 BTC's worth of orders between its price and the mid-price.



### `BiasQuoteOnPositionElement`

> Specified using: `--chain biasquoteonposition`

> Accepts parameter: `--biasquoteonposition-bias`

This can shift the price of orders based on how much inventory is held. Too much inventory: bias prices down (so it tends to buy less and sell more). Too little inventory: bias prices up (so it tends to buy more and sell less).

The default bias is 0, meaning no changes will be made to orders. You can change this using the `-biasquoteonposition-bias` parameter. This should be a small, positive number - for example 0.00003 can shift the order price significantly.


### `ConfidenceIntervalElement`

> Specified using: `--chain confidenceinterval`

> Accepts parameter: `--confidenceinterval-level`

> Accepts parameter: `--confidenceinterval-position-size-ratio`

The `ConfidenceIntervalElement` uses the ‘confidence interval’ in the oracle price to determine the spread. How aggressively this is used can be tuned by the `--confidenceinterval-level` parameter.

This 'level' is weighting to apply to the confidence interval from the oracle: e.g. 1 - use the oracle confidence interval as the spread, 2 (risk averse, default) - multiply the oracle confidence interval by 2 to get the spread, 0.5 (aggressive) halve the oracle confidence interval to get the spread.

The ‘confidence interval’ is Pyth’s expectation of how far from the current mid-price the next trade will occur. If you use a ‘confidence weighting’ parameter of 2, this confidence interval is doubled and then added to the mid-price to get the sell price for the order and subtracted from the mid-price to get the buy price for the order.

- Using a confidence weighting of 1 just uses the confidence interval to create the spread
- Using a confidence weighting of 2 (the default) doubles the width of the spread
- Using a confidence weighting of 0.5 halves the width of the spread (and so is more aggressive)

**Important note:** this can be specified multiple times on the command line, so you can have orders placed at, say, 1x, 2x and 5x the confidence interval, placing/checking 6 orders in total each pulse (3 BUYs, 3 SELLs).


### `FixedPositionSizeElement`

> Specified using: `--chain fixedpositionsize`

> Accepts parameter: `--fixedpositionsize-value`

The `FixedPositionSizeElement` overrides the position size of all orders it sees, setting them to the fixed value (in the base currency) specified in the parameter.

For example, adding:
```
--chain fixedpositionsize --fixedpositionsize-value 3
```
to a chain on ETH/USDC will force all BUY and SELL orders to have a position size of 3 ETH.


### `FixedSpreadElement`

> Specified using: `--chain fixedspread`

> Accepts parameter: `--fixedspread-value`

The `FixedSpreadElement` overrides the spread of all orders it sees, setting them to the fixed value (in the quote currency) specified in the parameter.

For example, adding:
```
--chain fixedspread --fixedspread-value 0.5
```
to a chain on ETH/USDC will force the spread on BUY and SELL orders to be 0.5 USDC, meaning the BUY price will be the mid-price *minus* half the --fixedspread-value, and the SELL price will be the mid-price *plus* half the --fixedspread-value.


### `MinimumChargeElement`

> Specified using: `--chain minimumcharge`

> Accepts parameter: `--minimumcharge-ratio`

This ensures that there’s a minimum value of spread to be paid by the taker.

It’s possible that the configuration may lead to too small a spread to be profitable. You can use the `--minimumcharge-ratio` parameter to enforce a minimum spread. The default of 0.0005 is 0.05%.


### `PreventPostOnlyCrossingBookElement`

> Specified using `--chain preventpostonlycrossingbook`

This ensures that POST_ONLY orders that would corss the orderbook (and so be cancelled instead of put on the book) are placed *just* inside the spread by 1 tick.


### `RatiosElement`

> Specified using: `--chain ratios`

> Accepts parameter: `--ratios-spread`

> Accepts parameter: `--ratios-position-size`

The `RatiosElement` builds orders using the specified ratio of available collateral for the position size and the specified ratio of the price for the spread. The position size is specified using the `--ratios-position-size` parameter, and the spread is specified using the `--ratios-spread` parameter.

It is possible to 'layer' orders by specifying the `--ratios-position-size` and `--ratios-spread` parameters multiple times. **Note**: both parameters must be specified the same number of times - for example, it is an error to specify 3 position size ratios and only 2 spread ratios.


### `RoundToLotSizeElement`

> Specified using `--chain roundtolotsize`

This ensures prices and quantities are properly rounded to lot sizes. This can make the order reconciliation process more reliable since exact matches can be found for rounded orders while non-rounded orders may need more tolerance.