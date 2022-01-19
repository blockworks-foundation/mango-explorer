# 🥭 Mango Explorer

# 🔍‍ Marketmaking Oracles

The [Marketmaking Introduction](MarketmakingIntroduction.md) talks a bit about marketmaking generally but here we're going to focus specifically on oracles fetching prices.

Marketmakers usually want some external pricing information to derive the prices they use for bids and asks. This external price information is fetched and passed to the marketmaker by 'oracles'. An oracle is really just an external source of price information as far as the marketmaker is concerned.


# 🤔 Oracle Implementations

`mango-explorer` provides the following oracle implementations:
- `ftx` (uses [FTX](https://ftx.com) price data)
- `market` (a Serum or Mango market)
- `pyth` (uses [Pyth](https://pyth.network/) price data)
- `stub` (Mango stub oracle)

Specifics to each of these implementations are detailed later in the 'Oracle Reference' section.


# 🏷️ Fetching Prices

You can see an example of using an oracle to fetch the current price by using the following command:
```
$ show-price --market BTC/USDC --provider ftx
```
Alternatively, to get the current price of the BTC perp on Mango:
```
$ show-price --market BTC-PERP --provider market
```


# 🎽 In Practice

There's one more wrinkle. Most of the time you want the marketmaker to use the oracle for the *current* market, but that's not necessarily always the case. Where normally you could specify:
```
$ marketmaker --market ETH/USDC --oracle-provide pyth ...
```
everything would work as you expect, and it would use the Pyth oracle to fetch prices for ETH/USD.

But you might feel you have an advantage if you use Serum's BTC/USDC market for your prices on BTC-PERP. The way you could achieve that is by using the `--oracle-market` parameter. This defaults to the current market but if you specify this parameter you override this and can use a different market for pricing. For example:
```
$ marketmaker --market BTC-PERP --oracle-provider market --oracle-market BTC/USDC ...
```
**WARNING** You can also do very stupic things with this, like use ETH/USDC prices for quoting on BTC/USDC. Please be careful!


# 📖 Oracle Reference

## FTX

The FTX oracle queries FTX for the current price on the FTX market.


## Market

The Market oracle looks at a market that `mango-explorer` knows about. It can handle 3 types of market:
- Serum
- Spot
- Perp

**Note** The spot price will always be the same as the serum price, because spot markets use the underlying serum market for trades. The same is not true in reverse, because there are many more serum markets than spot markets.


## Pyth

The Pyth oracle fetches price data from Pyth's on-chain oracle system.


## Stub

The 'stub' oracle is the minimal oracle Mango uses when no other oracle data is readily available.