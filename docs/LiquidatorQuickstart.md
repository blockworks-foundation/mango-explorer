# 🥭 Mango Explorer

# 🏃‍ Liquidator Quickstart

Let’s assume you have a server set up already, with [docker](https://www.docker.com/) installed. This Quickstart will guide you through setting up and running [mango-explorer](https://gitlab.com/OpinionatedGeek/mango-explorer) to run a liquidator on [Mango Markets](https://mango.markets/). (You’ll need to provide your own funds for the liquidator though!)

Throughout this guide you’ll see the private key, accounts and transaction IDs as well as the commands and parameters that are used. (Funds will be removed from this account before this is published. Remember - sharing your private key is usually a Very Bad Idea!)


## 0.1 ☠️ Risks

OK, now is the time to question if you should really do this. No-one here is going to take any responsibility for your actions. It’s all on you. Are you certain you want to do this? Are you sure you want to run this code? Have you even checked it to make sure it’s not going to steal your money? Are you aware of the risks from markets in general, plus bugs, developer incompetence, malfeasance and lots of other bad stuff?


## 0.2 🦺 Prerequisites

To run this quickstart you’ll need:
* A server set up with [docker](https://www.docker.com/) or [podman](https://podman.io/) installed and configured.
* Some SOL for transaction costs.
* Some Solana-based USDC (we'll convert USDC to other tokens in this Quickstart).


# 1. ❓ Why Run A Liquidator?

Liquidation is the process that provides security to [Mango Markets](https://mango.markets/). Any accounts that borrow funds create the risk that they may not be able to pay those borrowed funds back. Accounts must provide collateral before they borrow funds, but the value of that collateral can vary with the price of the collateral tokens and the borrowed tokens.

If the value of the borrowed funds were to exceed the value of the provided collateral, all [Mango Markets](https://mango.markets/) users would have to cover those losses.

To prevent this, accounts have to provide collateral worth more than they borrow. Values are allowed to vary a little, but if the value of the collateral falls to lower than a specified threshold of what the account borrowed, that account can be 'liquidated'. (Current values for these thresholds are: you must provide collateral worth over 120% of your borrowings, and if the value of your collateral falls below 110% you can be liquidated.)

Being 'liquidated' means someone - anyone - can 'pay off' some of the borrowed tokens, in return for some of the collateral tokens. This 'paying off' earns the liquidator a premium of 5% - that is, 5% more collateral tokens are returned than the value of the borrowed tokens, making it a worthwhile task for the liquidator.


# 2. 💵 How Much Money?

This Quickstart will use 1,000USDC as the starting point. Is this enough? Too much? It all depends on you, how much you have, and how much you want to allocate to the liquidator.

1,000USDC seemed a nice starting point for this guide, but how much you use is up to you. Adjust the figures below where necessary.


# 3. 📂 Directories And Files

Our server will keep all its files under `/var/mango-explorer`, so run the following commands to set up the necessary directories and files:

```
# mkdir /var/mango-explorer
# touch /var/mango-explorer/id.json
# chown 1000:1000 /var/mango-explorer/id.json
```
(Don’t type the # prompt - that’s to show you the unix prompt where the command starts.)


# 4. 📜 'mango-explorer' Alias

Next, we'll set up an `alias` to make running the container easier. There are a lot of parameters to the
`docker` command and they're the same every time so to save typing them over and over, run:
```
# alias mango-explorer="docker run --rm -it --name=mango-explorer \
    -v /var/mango-explorer/id.json:/home/jovyan/work/id.json \
    opinionatedgeek/mango-explorer:latest"
```
_Alternatively_ if you're using `podman` instead of `docker`, run this:
```
# alias mango-explorer="podman run --rm -it --name=mango-explorer --security-opt label=disable \
    -v /var/mango-explorer/id.json:/home/jovyan/work/id.json \
    opinionatedgeek/mango-explorer:latest"
```


# 5. 👛 Create The Wallet

Run the following command to create your wallet:
```
# solana-keygen new --force --outfile /var/mango-explorer/id.json
```
This will ask you for a passphrase to protect your wallet - just press ENTER for no passphrase (`mango-explorer` doesn't work with passphrases on key files yet and no-one has asked for it).

The output will be something like the following:
```
Generating a new keypair

For added security, enter a BIP39 passphrase

NOTE! This passphrase improves security of the recovery seed phrase NOT the
keypair file itself, which is stored as insecure plain text

BIP39 Passphrase (empty for none):

Wrote new keypair to /Users/geoff/idx.json
=========================================================================
pubkey: uVBU7j2VGqNKLrYFfCcbU71sopkD4nW58Rk7CTyEYFm
=========================================================================
Save this seed phrase to recover your new keypair:
artist stadium topple few dawn quit group worry mother banner shadow term
=========================================================================
```
That's what a successful run of the command looks like.

This will create a Solana wallet and write its secret key to /var/mango-explorer/id.json. **Looking after this file is entirely your responsibility. If you lose this file, you lose the private key for all the funds in the wallet. If you give it to someone else you give them the entire contents of your wallet.**

Once successfully created, if you look at the file you’ll see the bytes of your private key. **Keep this secret!**

It should look something like this, but with different numbers:
```
# cat /var/mango-explorer/id.json
[110,49,211,169,16,1,52,50,225,133,73,175,67,185,69,124,79,194,153,3,53,41,204,180,255,80,44,140,43,222,6,53,13,114,16,218,159,70,85,72,57,243,132,149,4,117,23,61,10,101,43,62,61,1,216,197,55,59,237,8,106,171,135,60]
```
Yes, that's the actual secret key of the account.

# 6. 💰 Add Some SOL

Transfer some SOL into the account just created. SOL tokens are needed for running operations on the Solana blockchain, similar to the way ether is used on Ethereum.

How you transfer the SOL is up to you, and dependent on where you actually have SOL.

I used [sollet](https://sollet.io) to transfer 1 SOL to **48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB**, the address shown above when creating the wallet. When the transfer completes (it’s very fast!) it appears in the wallet and you can check that using the `group-balances` command:
```
# mango-explorer group-balances
2021-05-08 14:15:51 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Balances:
    SOL balance:         1.00000000
    BTC balance:         0.00000000
    ETH balance:         0.00000000
    SOL balance:         0.00000000
    SRM balance:         0.00000000
   USDC balance:         0.00000000
```

This shows 1 SOL and 0 BTC, 0 ETH, 0 SOL, 0 SRM, and 0 USDC, as you'd expect (since we haven't sent any of those yet).

These five tokens - BTC, ETH, USDC - are the five tokens of the default 'group' of cross-margined tokens we're using. If you want to use a different group, you can pass the `--group-name` parameter to commands.


# 7. ✅ Validate Account

Now let's examine our account with the `Account Scout`. This tool is used to verify things on liquidator startup, and it's useful to run from time to time.

If you run it without parameters it will check the current wallet address, but you can check a different address by passing the `--address` parameter.
```
# mango-explorer account-scout
2021-05-08 14:07:30 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

« ScoutReport [48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB]:
    Summary:
        Found 3 error(s) and 2 warning(s).

    Errors:
        Account '48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB' has no account for token 'BTC', mint '9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E'.
        Account '48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB' has no account for token 'ETH', mint '2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk'.
        Account '48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB' has no account for token 'SOL', mint 'So11111111111111111111111111111111111111112'.
        Account '48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB' has no account for token 'SRM', mint 'SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt'.
        Account '48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB' has no account for token 'USDC', mint 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'.

    Warnings:
        No Serum open orders account for market 'BTC/USDC' [A8YFbxQYFVqKZaoYJLLUVcQiWP7G2MeEgW5wsAQgMvFw]'.
        No Serum open orders account for market 'ETH/USDC' [4tSvZvnbyzHXLMTiFonMyxZoHmFqau1XArcRCVHLZ5gX]'.
        No Serum open orders account for market 'SOL/USDC' [9wFFyRfZBsuAha4YcuxcXLKwMxJR43S7fPfQLusDBzvT]'.
        No Serum open orders account for market 'SRM/USDC' [ByRys5tuUWDgL73G8JBAEfkdFf8JWBzPBDHsBVQ5vbQA]'.

    Details:
        Account '48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB' has no Mango Markets margin accounts.
»
```
So, we have 5 errors - no token accounts for BTC, ETH, SOL, SRM, or USDC. That's expected - we haven't added any of those tokens yet. Let's start that now.


# 8. 💸 Add USDC

Transfer some USDC to the new account. Again I'm using [sollet](https://sollet.io) for this but you use whatever you're comfortable with. I transferred 1,000 USDC to **48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB**.

When you've transferred the USDC, a re-run of the `group-balances` should show something like:
```
# mango-explorer group-balances
2021-05-08 14:18:21 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Balances:
    SOL balance:         1.00000000
    BTC balance:         0.00000000
    ETH balance:         0.00000000
    SOL balance:         0.00000000
    SRM balance:         0.00000000
   USDC balance:     1,000.00000000
```

You can see above that the USDC balance is now 1,000. You should see whatever amount you transferred in your own output.


# 9. ⚖️ 'Balancing' The Wallet

The default group is a cross-margined basket of 3 tokens: BTC, ETH, and USDC. A general liquidator probably wants to be able to provide any of those tokens, to allow for situations where it needs to provide tokens to make up a margin account's shortfall.

After performing a liquidation though, the wallet may 'run out' of one type of token, or may have too much of another token, skewing the risk profile of the wallet. To fix this, we need to 'balance' the proportion of each token in the wallet.

What proportion of tokens is 'right'? It depends on your goals. You might want to accumulate only USDC, so you would specify a fixed amount of BTC and ETH as the target for balancing. On the other hand, you may just want to keep a third of the value in each token.

For our purposes here, let's go for about a fifth in each token. At today's prices, that's:
* 0.004 BTC
* 0.06 ETH
* 2.65 SOL
* 30 SRM
* 200 USDC

To set this up, we can use the `group-balance-wallet` command. We tell it we want to put 33% in BTC (using the `--target` parameter with the value "BTC:33%") and 33% in ETH (using the `--target` parameter with the value "ETH:33%"). Since this command actually performs transactions, let's run it first with the `--dry-run` parameter - this tells the command to run but not send any actual transactions to Serum.
```
# mango-explorer group-balance-wallet --target "BTC:0.004" --target "ETH:0.06" --target "SOL:2.65" --target "SRM:30" --dry-run
2021-05-08 14:20:04 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Skipping BUY trade of 0.00400000 of 'BTC'.
Skipping BUY trade of 0.06000000 of 'ETH'.
Skipping BUY trade of 2.65000000 of 'SOL'.
Skipping BUY trade of 30.00000000 of 'SRM'.
```
Let's run it again without the `--dry-run` flag, so that it actually performs the transactions. This will place orders on the Serum orderbook to trade the tokens.
```
# mango-explorer group-balance-wallet --target "BTC:0.004" --target "ETH:0.06" --target "SOL:2.65" --target "SRM:30" --dry-run
2021-05-08 14:28:12 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

BUY order market: C1EuT9VokAKLiW7i2ASnZUvxDoKuKkCpDDeNxAptuNe4 <pyserum.market.market.Market object at 0x7f237d0894c0>
Price 61719.00 - adjusted by 0.05 from 58780
Source token account: « AccountInfo [2HchGy6FnjC6DuZb9oTZ9ByUMtUScJkhdDzGUkVNtc8T]:
    Owner: TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA
    Executable: False
    Lamports: 2039280
    Rent Epoch: 179                                                                                             »
Placing order
    paying_token_address: 2HchGy6FnjC6DuZb9oTZ9ByUMtUScJkhdDzGUkVNtc8T
    account: <solana.account.Account object at 0x7f237d147790>
    order_type: IOC
    side: BUY
    price: 61719.0
    quantity: 0.005609457341096823
    client_id: 4886581369384305006
Order transaction ID: 38DxpqDUXLetSwD1iJ3PsUBJ42fzYxpYeMk6uWucuLYQfAvPn5VcGrcwFxc5Rb2hgsxhBKLew7idAx3xGhqhaHtK
Need to settle open orders: « OpenOrders:
    Flags: « SerumAccountFlags: initialized | open_orders »
    Program ID: 9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin
    Address: 2DCKHwbchxUDr2x2A7Z8YxKJojvv7gipTKwjyiZBbyvB
    Market: C1EuT9VokAKLiW7i2ASnZUvxDoKuKkCpDDeNxAptuNe4
    Owner: 48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB
    Base Token: 0.00560000 of 0.00560000
    Quote Token: 15.80494500 of 15.80494500
    Referrer Rebate Accrued: 144803
    Orders:
        None
    Client IDs:
        None
»
Base account: GzbKPy1TaM4gHNEBcVDKskEouePDopC5YRRLoFpPqkhm
Quote account: 2HchGy6FnjC6DuZb9oTZ9ByUMtUScJkhdDzGUkVNtc8T
Settlement transaction ID: 26nUTaeoKRPK7fQ4jCS216VVbVprqJGWbMn1NRC3vP3FXgnDFXrq1PthJgVWAuKAmmyixV77SrGwr2amox8ucrL3
Waiting on settlement transaction IDs: ['26nUTaeoKRPK7fQ4jCS216VVbVprqJGWbMn1NRC3vP3FXgnDFXrq1PthJgVWAuKAmmyixV77SrGwr2amox8ucrL3']
Waiting on specific settlement transaction ID: 26nUTaeoKRPK7fQ4jCS216VVbVprqJGWbMn1NRC3vP3FXgnDFXrq1PthJgVWAuKAmmyixV77SrGwr2amox8ucrL3
All settlement transaction IDs confirmed.
Order execution complete
BUY order market: 7dLVkUfBVfCGkFhSXDCq1ukM9usathSgS716t643iFGF <pyserum.market.market.Market object at 0x7f237d0b1ee0>
Price 3846.30750000000010 - adjusted by 0.05 from 3663.15000000000009094947017729282379150390625
Source token account: « AccountInfo [2HchGy6FnjC6DuZb9oTZ9ByUMtUScJkhdDzGUkVNtc8T]:
    Owner: TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA
    Executable: False
    Lamports: 2039280
    Rent Epoch: 179
»
Placing order
    paying_token_address: 2HchGy6FnjC6DuZb9oTZ9ByUMtUScJkhdDzGUkVNtc8T
    account: <solana.account.Account object at 0x7f237d147790>
    order_type: IOC
    side: BUY
    price: 3846.3075
    quantity: 0.09001342018264541
    client_id: 3766227519595772173
Order transaction ID: 63HUK1wNizrUJAYaMPxaQirni6AQp6BFgeqL8Uuw9cZhGJseqszLZkWFmMGPFWULKoHFuJSWMmX7kGQqNpxovvu8
Need to settle open orders: « OpenOrders:
    Flags: « SerumAccountFlags: initialized | open_orders »
    Program ID: 9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin
    Address: E4jX61Z8w7uXpCiqU3amBKPdtf8qzpdrGvGFifNsxBAg
    Market: 7dLVkUfBVfCGkFhSXDCq1ukM9usathSgS716t643iFGF
    Owner: 48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB
    Base Token: 0.09000000 of 0.09000000
    Quote Token: 15.19678100 of 15.19678100
    Referrer Rebate Accrued: 145307
    Orders:
        None
    Client IDs:
        None
»
Base account: EeehKVmdzDatRzMgx8RGDAdnQ6XD1wTfWXHhD4aezrRM
Quote account: 2HchGy6FnjC6DuZb9oTZ9ByUMtUScJkhdDzGUkVNtc8T
Settlement transaction ID: 4Sb7qV8XL7vL3PsbLUuqtFHxcYbM3swu62T5ZMMsHewdWaaddDwaP1pK9jmANV5RBx9zh3vxuyGWfmh2xmwkFbAM
Waiting on settlement transaction IDs: ['4Sb7qV8XL7vL3PsbLUuqtFHxcYbM3swu62T5ZMMsHewdWaaddDwaP1pK9jmANV5RBx9zh3vxuyGWfmh2xmwkFbAM']
Waiting on specific settlement transaction ID: 4Sb7qV8XL7vL3PsbLUuqtFHxcYbM3swu62T5ZMMsHewdWaaddDwaP1pK9jmANV5RBx9zh3vxuyGWfmh2xmwkFbAM
All settlement transaction IDs confirmed.
Order execution complete
```

If you have problems at this stage, for example with Solana transactions timing out because of network problems, there are useful commands to manually fix things: `serum-buy`, `serum-sell` and (particularly useful for problems where Serum completes the order but the token doesn't make it to your wallet) `group-settle`.

Now if we check the balances we can see we have roughly a fifth in each of the five group tokens:
```
# mango-explorer group-balances
2021-05-08 14:31:43 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Balances:
    SOL balance:         0.94913592
    BTC balance:         0.00400000
    ETH balance:         0.06000000
    SOL balance:         2.65000000
    SRM balance:        30.00000000
   USDC balance:       199.20742600
```

We now have about 200 USDC, 0.004 BTC, 0.06 ETH, 2.65 SOL, and 30 SRM. That's roughly a fifth each at today's prices.


# 10. ✅ Validate Account (Again)

Now would be a good time to run the `Account Scout` tool again, to make sure things are as we expect.
```
# mango-explorer account-scout
2021-05-08 14:34:10 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

« ScoutReport [48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB]:
    Summary:
        No problems found

    Errors:
        None

    Warnings:
        None

    Details:
        Token account with mint '9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E' has balance: 0.004 BTC
        Token account with mint '2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk' has balance: 0.06 ETH
        Token account with mint 'So11111111111111111111111111111111111111112' has balance: 2.65 SOL
        Token account with mint 'SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt' has balance: 30 SRM
        Token account with mint 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v' has balance: 199.207426 USDC
        Serum open orders account for market 'BTC/USDC': « OpenOrders:
            Flags: « SerumAccountFlags: initialized | open_orders »
            Program ID: 9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin
            Address: 2DCKHwbchxUDr2x2A7Z8YxKJojvv7gipTKwjyiZBbyvB
            Market: C1EuT9VokAKLiW7i2ASnZUvxDoKuKkCpDDeNxAptuNe4
            Owner: 48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB
            Base Token: 0.00000000 of 0.00000000
            Quote Token: 0.00000000 of 0.00000000
            Referrer Rebate Accrued: 0
            Orders:
                None
            Client IDs:
                None
        »
        Serum open orders account for market 'ETH/USDC': « OpenOrders:
            Flags: « SerumAccountFlags: initialized | open_orders »
            Program ID: 9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin
            Address: E4jX61Z8w7uXpCiqU3amBKPdtf8qzpdrGvGFifNsxBAg
            Market: 7dLVkUfBVfCGkFhSXDCq1ukM9usathSgS716t643iFGF
            Owner: 48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB
            Base Token: 0.00000000 of 0.00000000
            Quote Token: 0.00000000 of 0.00000000
            Referrer Rebate Accrued: 0
            Orders:
                None
            Client IDs:
                None
        »
        Serum open orders account for market 'SOL/USDC': « OpenOrders:
            Flags: « SerumAccountFlags: initialized | open_orders »
            Program ID: 9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin
            Address: E4jX61Z8w7uXpCiqU3amBKPdtf8qzpdrGvGFifNsxBAh
            Market: 7dLVkUfBVfCGkFhSXDCq1ukM9usathSgS716t643iFGF
            Owner: 48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB
            Base Token: 0.00000000 of 0.00000000
            Quote Token: 0.00000000 of 0.00000000
            Referrer Rebate Accrued: 0
            Orders:
                None
            Client IDs:
                None
        »
        Serum open orders account for market 'SRM/USDC': « OpenOrders:
            Flags: « SerumAccountFlags: initialized | open_orders »
            Program ID: 9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin
            Address: E4jX61Z8w7uXpCiqU3amBKPdtf8qzpdrGvGFifNsxBAi
            Market: 7dLVkUfBVfCGkFhSXDCq1ukM9usathSgS716t643iFGF
            Owner: 48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB
            Base Token: 0.00000000 of 0.00000000
            Quote Token: 0.00000000 of 0.00000000
            Referrer Rebate Accrued: 0
            Orders:
                None
            Client IDs:
                None
        »
        Account '48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB' has no Mango Markets margin accounts.
»
```

You can see that the process of balancing the tokens has created the necessary token accounts, as well as creating the `OpenOrders` accounts Serum uses for trading.

All looks good now!


# 11. 🎬 Start The (Pretend) Liquidator

OK, now we're ready to try a test run of the liquidator.

This is a long-running process, so we'll need to use Control-C to cancel it when we're done.

Here goes:
```
# mango-explorer liquidator --target "BTC:0.004" --target "ETH:0.06" --target "SOL:2.65" --target "SRM:30" --dry-run
2021-05-08 14:36:34 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg                                                                       
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation                                                             
    📧 Email: mailto:hello@blockworks.foundation

2021-05-08 14:36:34 ⓘ root         Context: « Context:
    Cluster: mainnet-beta
    Cluster URL: https://mango.rpcpool.com/
    Program ID: JD3bq9hGdy38PuWQ4h2YJpELmHVGPPfFSuFkpzAd9zfu
    DEX Program ID: 9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin
    Group Name: BTC_ETH_USDC
    Group ID: 7pVYhpKUHw88neQHxgExSH6cerMZ1Axx1ALQP9sxtvQV
»
2021-05-08 14:36:34 ⓘ root         Wallet address: 48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB
2021-05-08 14:36:34 ⓘ root         Checking wallet accounts.
2021-05-08 14:36:37 ⓘ root         Wallet account report: « ScoutReport [48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB]:
    Summary:
        No problems found

    Errors:
        None

    Warnings:
        None

    Details:
        Token account with mint '9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E' has balance: 0.004 BTC
        Token account with mint '2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk' has balance: 0.06 ETH
        Token account with mint 'So11111111111111111111111111111111111111112' has balance: 2.65 SOL
        Token account with mint 'SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt' has balance: 30 SRM
        Token account with mint 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v' has balance: 199.207426 USDC
        Serum open orders account for market 'BTC/USDC': « OpenOrders:
            Flags: « SerumAccountFlags: initialized | open_orders »
            Program ID: 9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin
            Address: 2DCKHwbchxUDr2x2A7Z8YxKJojvv7gipTKwjyiZBbyvB
            Market: C1EuT9VokAKLiW7i2ASnZUvxDoKuKkCpDDeNxAptuNe4
            Owner: 48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB
            Base Token: 0.00000000 of 0.00000000
            Quote Token: 0.00000000 of 0.00000000
            Referrer Rebate Accrued: 0
            Orders:
                None
            Client IDs:
                None
        »
        Serum open orders account for market 'ETH/USDC': « OpenOrders:
            Flags: « SerumAccountFlags: initialized | open_orders »
            Program ID: 9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin
            Address: E4jX61Z8w7uXpCiqU3amBKPdtf8qzpdrGvGFifNsxBAg
            Market: 7dLVkUfBVfCGkFhSXDCq1ukM9usathSgS716t643iFGF
            Owner: 48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB
            Base Token: 0.00000000 of 0.00000000
            Quote Token: 0.00000000 of 0.00000000
            Referrer Rebate Accrued: 0
            Orders:
                None
            Client IDs:
                None
        »
        Serum open orders account for market 'SOL/USDC': « OpenOrders:
            Flags: « SerumAccountFlags: initialized | open_orders »
            Program ID: 9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin
            Address: E4jX61Z8w7uXpCiqU3amBKPdtf8qzpdrGvGFifNsxBAh
            Market: 7dLVkUfBVfCGkFhSXDCq1ukM9usathSgS716t643iFGF
            Owner: 48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB
            Base Token: 0.00000000 of 0.00000000
            Quote Token: 0.00000000 of 0.00000000
            Referrer Rebate Accrued: 0
            Orders:
                None
            Client IDs:
                None
        »
        Serum open orders account for market 'SRM/USDC': « OpenOrders:
            Flags: « SerumAccountFlags: initialized | open_orders »
            Program ID: 9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin
            Address: E4jX61Z8w7uXpCiqU3amBKPdtf8qzpdrGvGFifNsxBAi
            Market: 7dLVkUfBVfCGkFhSXDCq1ukM9usathSgS716t643iFGF
            Owner: 48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB
            Base Token: 0.00000000 of 0.00000000
            Quote Token: 0.00000000 of 0.00000000
            Referrer Rebate Accrued: 0
            Orders:
                None
            Client IDs:
                None
        »
        Account '48z8UzFTYYbmFGgryA3muJ4tjdPsDUnB84YvfCXtv4dB' has no Mango Markets margin accounts.
»
2021-05-08 14:36:37 ⓘ root         Wallet accounts OK.
2021-05-08 14:36:37 ⓘ PollingLiqui Fetching all margin accounts...
2021-05-08 14:37:01 ⓘ PollingLiqui Fetched 15448 margin accounts to process.
2021-05-08 14:37:01 ⓘ PollingLiqui Of those 15448, 3694 have a nonzero collateral ratio.
2021-05-08 14:37:01 ⓘ PollingLiqui Of those 3694, 109 are ripe 🥭.
2021-05-08 14:37:01 ⓘ PollingLiqui Update 0 of 109 ripe 🥭 accounts.
2021-05-08 14:37:02 ⓘ PollingLiqui Of those 109, 81 are liquidatable.
2021-05-08 14:37:02 ⓘ PollingLiqui Of those 81 liquidatable margin accounts, 2 are 'above water' margin accounts with assets greater than their liabilities.
2021-05-08 14:37:02 ⓘ PollingLiqui Of those 2 above water margin accounts, 0 are worthwhile margin accounts with more than 0.01 net assets.
2021-05-08 14:37:02 ⓘ root         Check of all ripe 🥭 accounts complete. Time taken: 0.39 seconds, sleeping for 5 seconds...
2021-05-08 14:37:07 ⓘ PollingLiqui Update 1 of 10 - 109 ripe 🥭 accounts.
2021-05-08 14:37:09 ⓘ PollingLiqui Of those 109, 81 are liquidatable.
2021-05-08 14:37:09 ⓘ PollingLiqui Of those 81 liquidatable margin accounts, 2 are 'above water' margin accounts with assets greater than their liabilities.
2021-05-08 14:37:09 ⓘ PollingLiqui Of those 2 above water margin accounts, 0 are worthwhile margin accounts with more than 0.01 net assets.
2021-05-08 14:37:09 ⓘ root         Check of all ripe 🥭 accounts complete. Time taken: 2.26 seconds, sleeping for 3 seconds...
2021-05-08 14:37:12 ⓘ PollingLiqui Update 2 of 10 - 109 ripe 🥭 accounts.
2021-05-08 14:37:12 ⓘ PollingLiqui Of those 109, 81 are liquidatable.
2021-05-08 14:37:12 ⓘ PollingLiqui Of those 81 liquidatable margin accounts, 2 are 'above water' margin accounts with assets greater than their liabilities.
2021-05-08 14:37:12 ⓘ PollingLiqui Of those 2 above water margin accounts, 0 are worthwhile margin accounts with more than 0.01 net assets.
2021-05-08 14:37:12 ⓘ root         Check of all ripe 🥭 accounts complete. Time taken: 0.41 seconds, sleeping for 5 seconds...
^C2021-05-08 14:38:36 ⓘ root         Stopping...
2021-05-08 14:38:36 ⓘ root         Liquidator completed.

```

Well, that all seemed fine.

Some important things to note from the simulated run:
* It does a bunch of checks on startup to make sure it is in a state that can run.
* It prints out some summary information about the wallet account and child accounts.
* It loops once per minute, assessing which margin accounts are liquidatable (none, in the above run)
* It sleeps for as long as it can between runs
* You can't see it in the above (because no liquidations occurred) but it will automatically balance the wallet after every liquidation.


# 12. ⚡ Really Start The Liquidator

Remember that section on ☠️ Risks above? Well, if you still want to do it - **and I’m not recommending you do** - you can have `liquidator` submit live orders by removing the `--dry-run` parameter.

Output should be broadly the same as the output for a 'dry run', but if it sees any worthwhile liquidatable accounts it should try to perform a partial liquidation.

Now, it's over to you. Happy liquidating!
