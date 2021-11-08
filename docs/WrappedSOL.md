# 🥭 Mango Explorer

# ◎ Wrapped SOL

SOL is the native token of the Solana network. [Mango Markets](https://mango.markets/) (and [Serum](https://projectserum.com/)) trade Solana's ['SPL' tokens](https://spl.solana.com/) and can't directly trade SOL.

In order to allow trading of SOL, it must first be 'wrapped' in an SPL-compatible account.

This page will show you the commands to create wrapped SOL accounts, wrap SOL, unwrap SOL, view all wrapped SOL accounts, and close wrapped SOL accounts.

(Note: commands in this page assume you have set up a `mango-explorer` command similar to how it's done in the [Quickstart](../Quickstart.md).)


# 1. ❓ What's The Problem?

'Pure' SOL can't be traded directly on [Mango Markets](https://mango.markets/) or [Serum](https://projectserum.com/). It must first be 'wrapped' in an SPL-compatible account.

Wallets can have different views on how to handle Wrapped SOL - some hide it, some transparently convert it and you never see the transient accounts, and some convert it but leave a Wrapped SOL account with a zero balance around for next time.

The liquidator keeps SOL and Wrapped SOL separate. This allows you to allocate a particular amount of Wrapped SOL to liquidating, and have it take part in rebalancing. You can see this if you run the `group-balances` command, e.g.:
```
# mango-explorer group-balances --group-name BTC_ETH_SOL_SRM_USDC
2021-06-08 13:22:01 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Balances:
        4.17700920 Pure SOL
        0.00000200 Wrapped Bitcoin (Sollet)
        0.00000000 Wrapped Ethereum (Sollet)
        0.00000000 Wrapped SOL
        0.00000000 Serum
        5.81632200 USD Coin
```


# 2. 🕵️ How Do I See What Wrapped SOL Accounts I Have?

Depending on what wallets you have used with your account, you may already have one or more 'Wrapped SOL' accounts, possibly with your Wrapped SOL shared across them. The liquidator can't use the combined balance of these accounts, so it will pick the account with the biggest balance. It's often simplest to combine these accounts so there is a single Wrapped SOL account.

You can see what Wrapped SOL accounts you have by using the `show-wrapped-sol` command, e.g.:
```
# mango-explorer show-wrapped-sol
2021-06-08 13:25:54 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Wrapped SOL:
    4dqnZ8MgT1AZksAixHha117DVPEBUJZ89V5MAgoYmzh9: « InstrumentValue:         1.00000000 Wrapped SOL »
```
If you have no wrapped SOL accounts, you'll see something like:
```
# mango-explorer show-wrapped-sol
2021-06-08 13:23:06 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

No wrapped SOL accounts.
```


# 3. 📒 How Do I Create A Wrapped SOL Account?

Creating a Wrapped SOL account is cheap and easy, as long as you have SOL in your account to wrap. Let's say these are the current balances:
```
# mango-explorer group-balances --group-name BTC_ETH_SOL_SRM_USDC
2021-06-08 13:22:01 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Balances:
        4.17700920 Pure SOL
        0.00000200 Wrapped Bitcoin (Sollet)
        0.00000000 Wrapped Ethereum (Sollet)
        0.00000000 Wrapped SOL
        0.00000000 Serum
        5.81632200 USD Coin
```
(It's an old account I'm not using for liquidations.)

Let's create a Wrapped SOL sub-account and 'wrap' 1 SOL from this account, using the `wrap-sol` command:
```
# mango-explorer wrap-sol --quantity 1
2021-06-08 13:24:02 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Wrapping SOL:
    Source: 4dgCXC4B6dnrcX3igFujgfzE1fqsEwA4JPcAdvVkysCj
    Destination: 4dqnZ8MgT1AZksAixHha117DVPEBUJZ89V5MAgoYmzh9
Waiting on transaction ID: 3PpYrSZzz9DFdEFYjZnwCiAXN43d1bASAiA9ay8UsVm1d4AUvEGznL3hsT2A6sbriywSYACfSmAJjCVttsuVmsNW
Transaction confirmed.
```

This adds to the largest Wrapped SOL sub-account that exists for the account, and will automatically create a Wrapped SOL account if none exist.

Now the Group balances are:
```
# mango-explorer group-balances --group-name BTC_ETH_SOL_SRM_USDC
2021-06-08 13:25:07 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Balances:
        3.17495992 Pure SOL
        0.00000200 Wrapped Bitcoin (Sollet)
        0.00000000 Wrapped Ethereum (Sollet)
        1.00000000 Wrapped SOL
        0.00000000 Serum
        5.81632200 USD Coin
```
You can see a Wrapped SOL account has been created and now holds exactly 1.0 Wrapped SOL.


# 4. 🎁 How Do I Wrap SOL?

Wrapping SOL when you already have a Wrapped SOL account is exactly the same as wrapping SOL when you don't have a Wrapped SOL account - you still just use the `wrap-sol` command.

For example, for an account with 1.0 Wrapped SOL:
```
# mango-explorer show-wrapped-sol
2021-06-08 13:25:54 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Wrapped SOL:
    4dqnZ8MgT1AZksAixHha117DVPEBUJZ89V5MAgoYmzh9: « InstrumentValue:         1.00000000 Wrapped SOL »
```
An additional `wrap-sol` command will just add Wrapped SOL to that same account:
```
# mango-explorer wrap-sol --quantity 1
2021-06-08 13:28:09 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Wrapping SOL:
    Temporary account: 5UJR65bqMDKHuoxFKkfzurJFVma2msk4Fps6dze7HsgF
    Source: 4dgCXC4B6dnrcX3igFujgfzE1fqsEwA4JPcAdvVkysCj
    Destination: 4dqnZ8MgT1AZksAixHha117DVPEBUJZ89V5MAgoYmzh9
Waiting on transaction ID: 4hb9hsuHUcZgNNdsYVppWeFSBW8hfjBw5b93fjMmcPJXToDe4RsdTDvxX6qm7yxYi99GMat5w1Q2Fd5W4rzvbYH9
Transaction confirmed.
```
You can verify this with the `show-wrapped-sol` command again:
```
# mango-explorer show-wrapped-sol
2021-06-08 13:29:24 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Wrapped SOL:
    4dqnZ8MgT1AZksAixHha117DVPEBUJZ89V5MAgoYmzh9: « InstrumentValue:         2.00000000 Wrapped SOL »
```
And the group balances will also reflect this:
```
# mango-explorer group-balances --group-name BTC_ETH_SOL_SRM_USDC
2021-06-08 13:30:24 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Balances:
        2.17494992 Pure SOL
        0.00000200 Wrapped Bitcoin (Sollet)
        0.00000000 Wrapped Ethereum (Sollet)
        2.00000000 Wrapped SOL
        0.00000000 Serum
        5.81632200 USD Coin
```
There are now 2.0 Wrapped SOL, and it's still using the same Wrapped SOL account address.


# 5. 📖 How Do I Unrap SOL

Unwrapping SOL is the converse of wrapping it, and the command is `unwrap-sol`. This command will remove Wrapped SOL from a Wrapped SOL account, and add it as Pure SOL to the main wallet address.

For example:
```
# mango-explorer unwrap-sol --quantity 1
2021-06-08 13:33:27 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Unwrapping SOL:
    Temporary account: 41gehVpFPxmUiyDtiP6xJEnXir3UJh7AJaYWnH5bEmg1
    Source: 4dqnZ8MgT1AZksAixHha117DVPEBUJZ89V5MAgoYmzh9
    Destination: 4dgCXC4B6dnrcX3igFujgfzE1fqsEwA4JPcAdvVkysCj
Waiting on transaction ID: wwwrC4jmpjNwS9LbUqid2SsJAGzCri8nL3hX5KgmU8otVkWzvG8cAPhevYeGhtAi9Vw5RAismJBGBFFPtW9FJzm
Transaction confirmed.
```
And you can verify the updated balances with `show-wrapped-sol`:
```
show-wrapped-sol
2021-06-08 13:34:48 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Wrapped SOL:
    4dqnZ8MgT1AZksAixHha117DVPEBUJZ89V5MAgoYmzh9: « InstrumentValue:         1.00000000 Wrapped SOL »
```
Or with `group-balances`:
```
# mango-explorer group-balances --group-name BTC_ETH_SOL_SRM_USDC
2021-06-08 13:35:23 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Balances:
        3.17493992 Pure SOL
        0.00000200 Wrapped Bitcoin (Sollet)
        0.00000000 Wrapped Ethereum (Sollet)
        1.00000000 Wrapped SOL
        0.00000000 Serum
        5.81632200 USD Coin
```

# 6. 🔥 How Do I Delete A Wrapped SOL Account?

Problems can happen and leave you with multiple Wrapped SOL accounts. Sometimes wallets create them and don't clean them up (accidentally or deliberately), sometimes programs crash.

Whatever the reason, you can see all the Wrapped SOL sub-accounts for your account by using `show-wrapped-sol`. For example, you can see here there are 2 Wrapped SOL sub-accounts:
```
# mango-explorer show-wrapped-sol
2021-06-08 13:40:27 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Wrapped SOL:
    CUE36bvBYENx4TjRZbSAnL4d5cJeCk2Ct1PcQuyL9zYZ: « InstrumentValue:         0.50000000 Wrapped SOL »
    4dqnZ8MgT1AZksAixHha117DVPEBUJZ89V5MAgoYmzh9: « InstrumentValue:         1.00000000 Wrapped SOL »
```
The liquidator is only able to effectively use one of these, so it'll pick the largest.

It's often better to remove confusion by having just one Wrapped SOL account for the liquidator account.

The `close-wrapped-sol-account` will unwrap all the SOL, transfer that Pure SOL to the main wallet account, and then close the (now empty) Wrapped SOL account.

For example, to close the above '4dqnZ8MgT1AZksAixHha117DVPEBUJZ89V5MAgoYmzh9' with 1.0 Wrapped SOL in it:
```
# mango-explorer close-wrapped-sol-account --address 4dqnZ8MgT1AZksAixHha117DVPEBUJZ89V5MAgoYmzh9
2021-06-08 13:46:44 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Closing account: 4dqnZ8MgT1AZksAixHha117DVPEBUJZ89V5MAgoYmzh9 with balance 1.000000000 lamports.
Waiting on transaction ID: 5aBA8wVwBw1TUbHFYQuiqKKrATMjogya5Y5JMNe29b3hZkbvnVGCCoGVNZSQddNkZ4naiPeSk2wpyeejzf6cysDr
Account closed.
```
And you can verify this result with `show-wrapped-sol`:
```
# mango-explorer show-wrapped-sol
2021-06-08 13:48:44 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Wrapped SOL:
    CUE36bvBYENx4TjRZbSAnL4d5cJeCk2Ct1PcQuyL9zYZ: « InstrumentValue:         0.50000000 Wrapped SOL »
```