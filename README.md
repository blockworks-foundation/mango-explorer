# 🥭 Mango Explorer

## ⚠ Warning

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Run these notebooks on Binder: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gl/OpinionatedGeek%2Fmango-explorer/HEAD)


## Introduction

**I am not yet confident in the figures and calculations. Please don't rely on this code yet!**

There are some notebook pages to explore Mango account structures for your own accounts.

There is also a functional liquidator (in the V2 branch) and a functional marketmaker (in the main branch).


## Running the marketmaker

There is a [Marketmaking Quickstart](docs/MarketmakingQuickstart.md) - a walkthrough of setting up and running the marketmaker, from setting up the account, depositing tokens, to running the marketmaker itself.

It can take around 30 minutes to run through.

Requirements:
* A server with docker installed

**Note** This walkthrough is devnet-only so no actual funds are used or at-risk.



## Running the liquidator

There is a [Liquidator Quickstart](docs/LiquidatorQuickstart.md) - a walkthrough of setting up and running the liquidator, from creating the account, 'balancing' the wallet across the different tokens, and running the liquidator itself.

It can take around 30 minutes to run through.

Requirements:
* A server with docker installed
* Some SOL to pay for transactions
* Some USDC to fund the liquidation wallet

**Note** This is only for liquidating Mango V2. There is no Python V3 liquidator for Mango here (yet).


## References

* [🥭 Mango Markets](https://mango.markets/)
  * [Docs](https://docs.mango.markets/)
  * [Discord](https://discord.gg/67jySBhxrg)
  * [Twitter](https://twitter.com/mangomarkets)
  * [Github](https://github.com/blockworks-foundation)
  * [Email](mailto:hello@blockworks.foundation)
* [PySerum](https://github.com/serum-community/pyserum/)
* [SolanaPy](https://github.com/michaelhly/solana-py/)
* [Python Decimal Class](https://docs.python.org/3/library/decimal.html)
* [Python Construct Library](https://construct.readthedocs.io/en/latest/)
* [Python Observables](https://rxpy.readthedocs.io/en/latest/)
* [RxPy Backpressure](https://github.com/daliclass/rxpy-backpressure)


# Support

You can contact me [@OpinionatedGeek on Twitter](https://twitter.com/OpinionatedGeek).
