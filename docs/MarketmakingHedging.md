# 🥭 Mango Explorer


# 🔥‍ Hedging Risk

The [Marketmaking Introduction](MarketmakingIntroduction.md) talks a bit about marketmaking generally but here we're going to focus specifically on hedging to reduce risk.

Marketmakers can profit in a number of ways. If they fill a succession of nicely balanced SELLs and BUYs, marketmakers may profit by keeping the spread between the BUY and SELL prices. If the market supports liquidity incentives (like Mango perp markets), marketmakers may profit by earning the liquidity incentives even if no orders are filled.

Unfortunately, SELLs and BUYs don't usually come to the market in a balanced fashion. Often, when the market has a substantial move, marketmakers end up on the worse side of every trade. This can lead to marketmakers building up a sizable, costly position in an asset actively moving against them.

One strategy to mitigate the risk of maintaining a position when the price may move against you is to 'hedge' that risk.


# 🤔 Naive Hedging Implementation

The naive strategy for perp/spot hedging in the current `marketmaker` code is straightforward:

> Every 'pulse', compare the account's perp position with the account's token balance, and make sure they are exactly opposed.

For instance, if the marketmaker has a position of 5 SOL-PERP, the hedging code will check to make sure the account also holds a short of 5 SOL/USDC. If the account doesn't hold exactly 5 SOL/USDC, the code will buy or sell SOL/USDC to bring the balance to 5 SOL/USDC.

The hedging implementation only ever changes the spot balance. It never tries to change the perp balance.

By having the perp and spot balanced like this, with one the negative of the other, changes in the price of the asset no longer affect the value of the account. If the price of SOL goes up 10%, say, the value of the 5 SOL-PERP goes up 10% and the value of the 5 SOL/USDC goes down 10%, making the account 'delta neutral'.

Sortof.

Hedging is never perfect, the values of perps and spot should move in sync but don't always, the lot sizes for perp and spot can be different (so you can't get exactly the same quantities of each) and the price paid for the SOL/USDC hedge may not match the price of the original SOL-PERP.

Hedging can reduce some of the risks, but it doesn't remove all risk.


# 🎽 In Practice

The current hedging functionality only works for a marketmaking on a perp market, hedging to a spot market.

If you specify a `--hedge-market` in your marketmaker parameters, you turn on the hedging functionality.

Every marketmaker 'pulse', after the marketmaker has cancelled+placed any orders, the hedger checks the perp position for the market's base, and the account's balance of the market's base.

For perfect hedging, these should be exactly opposite: a positive perp position should be short the same quantity of spot, and a negative perp position should be long the same quantity of spot.

If these figures (rounded to the spot market's lot sizes) are not exactly correct, the hedger will try to buy or sell to make them exactly correct.

If it needs to buy or sell on spot, it will place the appropriate Immediate Or Cancel (IOC) order (with a slippage tolerance) to trade to the correct balance.

If the trade is too big for the market (the threshold is manually configured rather than automatically derived), it is 'chunked' across multiple pulses to give the market (and the spot marketmakers) time to adjust and place fresh orders. 

The aim is that most of the time the perp position and the spot balance will be mostly mirrored.


# 📖 Parameter Reference

> Parameter: `--hedging-market`

> Example Usage: `--hedging-market SOL/USDC`

This parameter is used to specify the market used for hedging. Currently only spot markets are supported, and only for hedging when marketmaking on a perp market. In addition, the base and quote tokens of both markets must match (so it shouldn't be possible to accidentally try to hedge SOL-PERP on ETH/USDC!)

Specifying the hedging market 'switches on' the hedging functionality. If no hedging market is specified, no hedging will take place. (This is the default.)


> Parameter: `--hedging-max-price-slippage-factor`

> Example Usage: `--hedging-max-price-slippage-factor 0.005`

This parameter is used to calculate the worst price that will be paid (from the oracle's mid price) for the hedge asset.

For example, `--hedging-max-price-slippage-factor 0.05` means the hedger will pay up to 5% extra (from the oracle mid price) to trade the hedge asset.

(All hedge orders are IOC.)


> Parameter: `--hedging-max-chunk-quantity`

> Example Usage: `--hedging-max-chunk-quantity 10`

If the marketmaker is trading significant quantities, they may be more volume than the spot market can easily handle.

This parameter allows you to specify a maximum quantity to trade on a single 'pulse' of the hedger. If positions and balances are still not matching at the time of the next pulse, another order is sent and another chunk traded, until the position and balance are properly mirrored.

For example, if the marketmaker wants to hedge 50 SOL, it might be better to spread that out over 5 pulses with 10 SOL each. That gives the spot marketmakers a chance to adjust and put up fresh orders instead of just sweeping all the orders on the book.

Using this may give a better overall price than a single order, or it may introduce a new timing risk as the market moves further away while some of the position is unhedged.