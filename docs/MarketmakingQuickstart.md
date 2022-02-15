# 🥭 Mango Explorer

# 🏃‍ Marketmaking Quickstart

This Quickstart will guide you through setting up and running [mango-explorer](https://github.com/blockworks-foundation/mango-explorer/) to run a marketmaker on [Mango Markets](https://mango.markets/) perps on devnet.

Devnet and [Mango’s Devnet Site](https://devnet.mango.markets) are test/development environments where it is safe to try things out without risking ‘live’ tokens. Tokens on devnet are purely for development and testing and have no value.

Throughout this guide you’ll see the private key, accounts and transaction IDs as well as the commands and parameters that are used. (This is a devnet account so no actual funds are required. And remember - sharing your private key is usually a Very Bad Idea!)

And all you need is a unix-type server (Unix, Linux or OS X etc.) with [docker](https://www.docker.com/) installed and configured. By the end of the guide you should have a marketmaker running against Mango’s BTC-PERP market on devnet.

This Quickstart was completed on a $5-per-month VPS on Vultr, so it doesn’t need high-spec hardware.


## 0.1 ☠️ Risks

Now is the time to question if you should really do this. No-one here is going to take any responsibility for your actions. It’s all on you. Are you certain you want to do this? Are you sure you want to run this code? Have you even checked it to make sure it’s not going to steal your money? Are you aware of the risks from markets in general, plus bugs, developer incompetence, malfeasance and lots of other bad stuff? This guide is for devnet-only but you’re still running software you didn’t create and that always involves risk.

This marketmaker has a very basic strategy that will likely lose money on trades over the long term. Liquidity incentives may make up for this to some extent, or they may not. Proceding is all at your own risk.


## 0.2 🦺 Prerequisites

To run this quickstart you’ll need:
* A unix-y server set up with [docker](https://www.docker.com/) installed and configured.
* Erm...
* That’s it

If you can successfully run `docker run hello-world`, you’re good to go!


## 0.3 🗓️ Comming Up

This Quickstart will guide you through the following sections:
* 1. ❓ Why Run A Marketmaker?
* 2. 📂 Directories And Files
* 3. 📜 ‘mango-explorer’ Alias
* 4. 👛 Create The Wallet
* 5. 🎱 6. 🎱 Common Command Parameters
* 6. 💰 Add Some SOL
* 7. ✅ Initialise Account
* 8. 💸 Add USDC
* 9. ⚖️ Deposit USDC
* 10. 🎬 A Bit About Marketmaking
* 11. 💸 Start The Marketmaker
* 12. ⚡ Really Start The Marketmaker

This Quickstart will use 10,000USDC (devnet, so not real) as the starting point. 10,000USDC seemed a nice starting point for this guide, but how much you use is up to you. Adjust the figures below where necessary.


# 1. ❓ Why Run A Marketmaker?

Traders buy and sell, but it helps when there are reliable entities for them to trade against. And while an individual trader may buy or sell, they typically aren’t doing both at the same time on the same symbol. In contrast, a marketmaker places both buy and sell orders for the same symbol, producing a valuation of the symbol and saying how much they’d be willing to pay for some quantity, and how much they’d ask to part with some quantity. They _literally make a market_ by always providing a price at which someone can buy and a price at which someone can sell, and profit by the difference between the buy and sell prices - the ‘spread’.

It takes a smart strategy to successfully run a marketmaker these days, and this code does not have a smart strategy. Unless there are other factors, expect this marketmaker to lose money in the medium and long term.


# 2. 📂 Directories And Files

Our server needs at least one file - the `id.json` that holds the secret key - but it can be useful to keep all mango-explorer things together, away from any other files you may have.

So what we’ll do is create a directory called `mango-explorer` in your home directory, put the `id.json` file there, and leave it up to you if you want to put logfiles or anything else in there too.

Run the following commands to set up the necessary directories and files:

```
# mkdir ~/mango-explorer
# touch ~/mango-explorer/id.json
# chmod 600 ~/mango-explorer/id.json
```
(Don’t type the # prompt - that’s to show you the unix prompt where the command starts.)

If you are running as `root`, there’s an additional step. Docker can’t write to that file now if you are `root` so you need to explicitly allow the container user access to that file by running:
```
# chown 1000:1000 ~/mango-explorer/id.json
```
You only need to run the `chown` command if you’re `root`. If you’re not `root`, that command is unnecessary and won’t work.


# 3. 📜 ‘mango-explorer’ Setup

## Pull The Container

First, pull the docker container so you have the code locally, ready to run. You can do this with the command:
```
# docker pull opinionatedgeek/mango-explorer-v3:latest
```
You should see output like the following appear as the files are downloaded:
```
Unable to find image 'opinionatedgeek/mango-explorer-v3:latest' locally
latest: Pulling from opinionatedgeek/mango-explorer-v3
345e3491a907: Pulling fs layer
57671312ef6f: Pulling fs layer
5e9250ddb7d0: Pull complete
785c60630545: Pull complete
314959dcc91c: Pull complete
4f4fb700ef54: Pull complete
2727b0936e12: Pull complete
c649f146ecf2: Pull complete
f1962b67837b: Pull complete
ab08f5ffeed7: Pull complete
968ce92ebc33: Pull complete
ac62172ef90e: Pull complete
ef82dda9ba1b: Pull complete
c1d39d11b2b8: Pull complete
fad5cd8318a4: Pull complete
601d4d2fcb66: Pull complete
686145366983: Pull complete
74ac90c5fbf8: Pull complete
29c418d8ea0c: Pull complete
02e01d5beaab: Pull complete
b35b963f1a3b: Pull complete
143c3708a732: Pull complete
650cfea2e368: Pull complete
5e07fca35e32: Pull complete
581a9e4184b8: Pull complete
888aace6a4bd: Pull complete
d7d19b016256: Pull complete
ed305f1f1552: Pull complete
380b2b59e451: Pull complete
719bde4769fa: Pull complete
b032295dfa95: Pull complete
7eca3701e45c: Pull complete
6ad8a619b3d7: Pull complete
3ab9fd3c550e: Pull complete
2734c002353b: Pull complete
79735cbc3330: Pull complete
Digest: sha256:dff5042e5d17cf13daf5bfec5126f75ed9622612adbfc4890a4f3f7cee409891
Status: Downloaded newer image for opinionatedgeek/mango-explorer-v3:latest
```

## Alias

Next, we’ll set up an `alias` to make running the container easier. There are a lot of parameters to the
`docker` command and they’re the same every time so to save typing them over and over, run:
```
# alias mango-explorer="docker run --rm -it --name=mango-explorer \
    -v $HOME/mango-explorer/id.json:/app/id.json \
    opinionatedgeek/mango-explorer-v3:latest"
```
It’s probably a good idea to put this alias in your `.profile` or `.bashrc` (or use whatever mechanism your shell uses for such things).


# 4. 👛 Create The Wallet

Run the following command to create your wallet:
```
# mango-explorer generate-keypair --filename /app/id.json --overwrite
```
(/app/id.json is not a typo in the command - it’s the path to the ID file in the docker container’s context - it’s mapped to the ~/mango-explorer/id.json file.)

The output will be something like the following:
```
Wrote new keypair to /app/id.json
==================================================================================
pubkey: 6MEVCr816wapduGknarkNRwMFWvFQSNv5h7iQEGGx8uB
==================================================================================
```
This is what a successful run of the command looks like. It creates a Solana wallet and writes its secret key to ~/mango-explorer/id.json. **Looking after this file is entirely your responsibility. If you lose this file, you lose the private key for all the funds in the wallet. If you give it to someone else you give them the entire contents of your wallet.** This is not a big deal on devnet but it’s very important on mainnet.

The above run shows a public key of: **6MEVCr816wapduGknarkNRwMFWvFQSNv5h7iQEGGx8uB**

If you look at the file you’ll see the bytes of your private key. **Keep this secret!**

It should look something like this, but with different numbers:
```
# cat ~/mango-explorer/id.json
[166,81,103,111,69,211,162,167,170,195,187,147,198,66,207,254,111,165,74,24,53,240,172,184,88,93,123,9,212,63,129,100,79,121,76,191,160,172,186,119,139,5,119,189,44,192,176,241,32,118,41,15,108,49,7,162,213,238,6,100,23,184,198,118]
```
Yes, that’s the actual secret key of the account.


# 5. 🎱 Common Command Parameters

(Nearly) all `mango-explorer` commands take the following general parameters:

- `--cluster-name CLUSTER_NAME` - Solana RPC cluster name
- `--cluster-url CLUSTER_URL` -  Solana RPC cluster URL
- `--group-name GROUP_NAME` - Mango group name
- `--group-address GROUP_ADDRESS` - Mango group address
- `--mango-program-address MANGO_PROGRAM_ADDRESS` - Mango program address
- `--serum-program-address SERUM_PROGRAM_ADDRESS` - Serum program address
- `--skip-preflight` - Skip pre-flight checks`
- `--token-data-file TOKEN_DATA_FILE`
                        data file that contains token symbols, names, mints and decimals (format is same as
                        [Solana Labs token list](https://raw.githubusercontent.com/solana-labs/token-list/main/src/tokens/solana.tokenlist.json))
- `--log-level LOG_LEVEL` - level of verbosity to log (possible values: DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--id-file ID_FILE` - file containing the JSON-formatted wallet private key

You can see exactly what parameters a command takes by passing just the `--help` parameter.


# 6. 💰 Add Some SOL

SOL tokens are needed for running operations on the Solana blockchain, similar to the way ether is used on Ethereum. Since this is devnet, you can just ask Solana itself for some tokens and it will put them in your account.

To do this, run the command:
```
# mango-explorer airdrop --symbol SOL --quantity 1 --url devnet
```
This will transfer 1 SOL to **6MEVCr816wapduGknarkNRwMFWvFQSNv5h7iQEGGx8uB**, the address shown above when creating the wallet.

You should see output like:
```
Airdropping 1 SOL to 6MEVCr816wapduGknarkNRwMFWvFQSNv5h7iQEGGx8uB
Transaction IDs: ['4FJGNLu1SuE2tXPgykjoGE1Pi5SWAkveMgLCJTmw7FJwwFwhyE9BA12xAcAkLt41nECcxytocMR67zZU4A3awurR']
```

Airdrops of devnet SOL are limited. Requesting more than 1 SOL is (currently) likely to fail but you can run this command again later to get more devnet SOL should you need it. 

When the transfer completes (it’s very fast!) it appears in the wallet and you can check that using the `show-account-balances` command:
```
# mango-explorer show-account-balances --cluster-name devnet
2021-08-27 19:16:34 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

2021-08-27 19:16:34 ⓘ root         Context: « 𝙲𝚘𝚗𝚝𝚎𝚡𝚝 'Mango Explorer':
    Cluster Name: devnet
    Cluster URL: https://mango.devnet.rpcpool.com
    Group Name: devnet.2
    Group Address: Ec2enZyoC4nGpEfu2sUNAa2nUGJHWxoUWYSEJ2hNTWTA
    Mango Program Address: 4skJ85cdxQAFVKbcGgfun8iZPL7BadVYXG3kGEGkufqA
    Serum Program Address: DESVgJVGajEgKGXhb6XmqDHGz3VjdgP7rEVESBgxmroY
»
2021-08-27 19:16:34 ⓘ root         Address: 6MEVCr816wapduGknarkNRwMFWvFQSNv5h7iQEGGx8uB

Token Balances [6MEVCr816wapduGknarkNRwMFWvFQSNv5h7iQEGGx8uB]:
Pure SOL            1.00000000
```

This shows 10 SOL and no other tokens, as you’d expect (since we haven’t acquired any of those yet).


# 7. ✅ Initialise Account

Now let’s set up the Mango Account. The Mango Account is associated with a Mango Group, and it holds your tokens and allows you to trade that Group’s markets using margin.

To create and initialise your Mango Account, run:
```
# mango-explorer ensure-account --cluster-name devnet --wait
2021-08-27 19:17:42 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Created account.
Waiting on transaction IDs: ['TJTBPUPv9tf7vgRUr27Jh8VeWNRGZfy8nkW1uEQhAYRLN8vpM4WboSHgeKGpJc25T4RnSYDFDsSy3fRn8TqKSYp']
2021-08-27 19:17:43 ⓘ BetterClient Waiting up to 60 seconds for ['TJTBPUPv9tf7vgRUr27Jh8VeWNRGZfy8nkW1uEQhAYRLN8vpM4WboSHgeKGpJc25T4RnSYDFDsSy3fRn8TqKSYp'].
2021-08-27 19:17:59 ⓘ BetterClient Confirmed TJTBPUPv9tf7vgRUr27Jh8VeWNRGZfy8nkW1uEQhAYRLN8vpM4WboSHgeKGpJc25T4RnSYDFDsSy3fRn8TqKSYp after 0:00:15.954582 seconds.
« 𝙰𝚌𝚌𝚘𝚞𝚗𝚝 (𝑢𝑛-𝑛𝑎𝑚𝑒𝑑), Version.V3 [E7R5k4tQKr2Doi3LvXLtSonRdgvXVGNFtL7fab2d2GjU]
    « 𝙼𝚎𝚝𝚊𝚍𝚊𝚝𝚊 Version.V1 - Account: Initialized »
    Owner: 6MEVCr816wapduGknarkNRwMFWvFQSNv5h7iQEGGx8uB
    Group: « 𝙶𝚛𝚘𝚞𝚙 'devnet.2' Version.V3 [Ec2enZyoC4nGpEfu2sUNAa2nUGJHWxoUWYSEJ2hNTWTA] »
    MSRM: 0
    Bankrupt? False
    Being Liquidated? False
    Shared Quote Token:
        « 𝙰𝚌𝚌𝚘𝚞𝚗𝚝𝙱𝚊𝚜𝚔𝚎𝚝𝚃𝚘𝚔𝚎𝚗 USDC
            Net Value:     « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 USDC »
                Deposited: « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 USDC »
                Borrowed:  « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 USDC »
        »
    In Basket: MNGO, BTC, ETH, SOL, SRM, RAY, USDT
    Basket [7 in basket]:
        « 𝙰𝚌𝚌𝚘𝚞𝚗𝚝𝙱𝚊𝚜𝚔𝚎𝚝𝙱𝚊𝚜𝚎𝚃𝚘𝚔𝚎𝚗 MNGO
            Net Value:     « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 MNGO »
                Deposited: « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 MNGO »
                Borrowed:  « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 MNGO »
            Spot OpenOrders: None
            Perp Account:
                « 𝙿𝚎𝚛𝚙𝙰𝚌𝚌𝚘𝚞𝚗𝚝 (empty) »
        »
        « 𝙰𝚌𝚌𝚘𝚞𝚗𝚝𝙱𝚊𝚜𝚔𝚎𝚝𝙱𝚊𝚜𝚎𝚃𝚘𝚔𝚎𝚗 BTC
            Net Value:     « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 BTC »
                Deposited: « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 BTC »
                Borrowed:  « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 BTC »
            Spot OpenOrders: None
            Perp Account:
                « 𝙿𝚎𝚛𝚙𝙰𝚌𝚌𝚘𝚞𝚗𝚝 (empty) »
        »
        « 𝙰𝚌𝚌𝚘𝚞𝚗𝚝𝙱𝚊𝚜𝚔𝚎𝚝𝙱𝚊𝚜𝚎𝚃𝚘𝚔𝚎𝚗 ETH
            Net Value:     « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 ETH »
                Deposited: « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 ETH »
                Borrowed:  « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 ETH »
            Spot OpenOrders: None
            Perp Account:
                « 𝙿𝚎𝚛𝚙𝙰𝚌𝚌𝚘𝚞𝚗𝚝 (empty) »
        »
        « 𝙰𝚌𝚌𝚘𝚞𝚗𝚝𝙱𝚊𝚜𝚔𝚎𝚝𝙱𝚊𝚜𝚎𝚃𝚘𝚔𝚎𝚗 SOL
            Net Value:     « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 SOL »
                Deposited: « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 SOL »
                Borrowed:  « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 SOL »
            Spot OpenOrders: None
            Perp Account:
                « 𝙿𝚎𝚛𝚙𝙰𝚌𝚌𝚘𝚞𝚗𝚝 (empty) »
        »
        « 𝙰𝚌𝚌𝚘𝚞𝚗𝚝𝙱𝚊𝚜𝚔𝚎𝚝𝙱𝚊𝚜𝚎𝚃𝚘𝚔𝚎𝚗 SRM
            Net Value:     « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 SRM »
                Deposited: « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 SRM »
                Borrowed:  « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 SRM »
            Spot OpenOrders: None
            Perp Account:
                « 𝙿𝚎𝚛𝚙𝙰𝚌𝚌𝚘𝚞𝚗𝚝 (empty) »
        »
        « 𝙰𝚌𝚌𝚘𝚞𝚗𝚝𝙱𝚊𝚜𝚔𝚎𝚝𝙱𝚊𝚜𝚎𝚃𝚘𝚔𝚎𝚗 RAY
            Net Value:     « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 RAY »
                Deposited: « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 RAY »
                Borrowed:  « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 RAY »
            Spot OpenOrders: None
            Perp Account:
                « 𝙿𝚎𝚛𝚙𝙰𝚌𝚌𝚘𝚞𝚗𝚝 (empty) »
        »
        « 𝙰𝚌𝚌𝚘𝚞𝚗𝚝𝙱𝚊𝚜𝚔𝚎𝚝𝙱𝚊𝚜𝚎𝚃𝚘𝚔𝚎𝚗 USDT
            Net Value:     « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 USDT »
                Deposited: « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 USDT »
                Borrowed:  « 𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎:         0.00000000 USDT »
            Spot OpenOrders: None
            Perp Account:
                « 𝙿𝚎𝚛𝚙𝙰𝚌𝚌𝚘𝚞𝚗𝚝 (empty) »
        »
»
```
You can see the details of your new account there, including all the zero-balances of the Group’s tokens.


# 8. 💸 Add USDC

Now you need to get some devnet USDC. You only need USDC for marketmaking on BTC-PERP - you don’t need a stash of both base and quote tokens the way you would if you were marketmaking on, say, BTC/USDC. There’s a faucet to freely give out devnet USDC tokens at B87AhxX6BkBsj3hnyHzcerX2WxPoACC7ZyDr8E7H9geN. Instead of using the [faucet web site](https://www.spl-token-ui.com/#/token-faucets), just run the command:
```
# mango-explorer airdrop --symbol USDC --quantity 10000 --faucet B87AhxX6BkBsj3hnyHzcerX2WxPoACC7ZyDr8E7H9geN --cluster-name devnet
```
You should see output like:
```
2021-08-30 11:03:09 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

2021-08-30 11:03:09 ⓘ BetterClient Waiting up to 60 seconds for ['2pHzmyPVT1UaU13zyigjQRr1xLz8jExpbiAsFpxxMzjoTEbyxAbhvtfYmQ2oiqfLF5Y6U637EBbJh3Wi1i561z5A'].
2021-08-30 11:03:28 ⓘ BetterClient Confirmed 2pHzmyPVT1UaU13zyigjQRr1xLz8jExpbiAsFpxxMzjoTEbyxAbhvtfYmQ2oiqfLF5Y6U637EBbJh3Wi1i561z5A after 0:00:19.050797 seconds.
Airdropping 10000 USDC to CfWq8oFtsyWQ1eVaC3qW3ffCFjQHUd4QmVjW9L9EQrBL
Transaction IDs: ['2fS2eFBryK97mxwh65dKqvmDX2PZdNDbYYfFHmphufnqWZpYPuhovsdiXpf96teZvM1eF6obxyWgFsAxtmEt6uvU']
```
10,000 devnet USDC should now be deposited into your USDC SPL token devnet account.


# 9. ⚖️ Deposit USDC

Now that you have some devnet USDC in your wallet, it’s time to move it into your Mango Account.

Before doing this, your token balances should look like this:
```
# mango-explorer show-account-balances --cluster-name devnet
2021-08-27 19:23:54 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

2021-08-27 19:23:54 ⓘ root         Context: « 𝙲𝚘𝚗𝚝𝚎𝚡𝚝 'Mango Explorer':
    Cluster Name: devnet
    Cluster URL: https://mango.devnet.rpcpool.com
    Group Name: devnet.2
    Group Address: Ec2enZyoC4nGpEfu2sUNAa2nUGJHWxoUWYSEJ2hNTWTA
    Mango Program Address: 4skJ85cdxQAFVKbcGgfun8iZPL7BadVYXG3kGEGkufqA
    Serum Program Address: DESVgJVGajEgKGXhb6XmqDHGz3VjdgP7rEVESBgxmroY
»
2021-08-27 19:23:54 ⓘ root         Address: 6MEVCr816wapduGknarkNRwMFWvFQSNv5h7iQEGGx8uB

Token Balances [6MEVCr816wapduGknarkNRwMFWvFQSNv5h7iQEGGx8uB]:
Pure SOL             0.96715468
USDC            10,000.00000000

Account Balances [E7R5k4tQKr2Doi3LvXLtSonRdgvXVGNFtL7fab2d2GjU]:
None
```
Deposit your USDC with the following command:
```
# mango-explorer deposit --symbol USDC --quantity 10000 --cluster-name devnet
2021-08-27 19:24:37 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

Transaction IDs: ['3mgPnxsTudgN4FN5h7v5PhguHRESaWfs7d9XWiGNBATnWDtCdm34v8qh3ue5yjygRWcGAJ3W7vzKSJJMNVUvqxzk']
```
Now your token balances should look like this:
```
# mango-explorer show-account-balances --cluster-name devnet
2021-08-27 19:25:21 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

2021-08-27 19:25:21 ⓘ root         Context: « 𝙲𝚘𝚗𝚝𝚎𝚡𝚝 'Mango Explorer':
    Cluster Name: devnet
    Cluster URL: https://mango.devnet.rpcpool.com
    Group Name: devnet.2
    Group Address: Ec2enZyoC4nGpEfu2sUNAa2nUGJHWxoUWYSEJ2hNTWTA
    Mango Program Address: 4skJ85cdxQAFVKbcGgfun8iZPL7BadVYXG3kGEGkufqA
    Serum Program Address: DESVgJVGajEgKGXhb6XmqDHGz3VjdgP7rEVESBgxmroY
»
2021-08-27 19:25:21 ⓘ root         Address: 6MEVCr816wapduGknarkNRwMFWvFQSNv5h7iQEGGx8uB

Token Balances [6MEVCr816wapduGknarkNRwMFWvFQSNv5h7iQEGGx8uB]:
Pure SOL             0.96714968

Account Balances [E7R5k4tQKr2Doi3LvXLtSonRdgvXVGNFtL7fab2d2GjU]:
USDC:
    Deposit:    10,000.00000000
    Borrow:          0.00000000
    Net:        10,000.00000000
```


# 10. 🎬 A Bit About Marketmaking

If you’ve read the [Marketmaking Introduction](MarketmakingIntroduction.md) doc you’ll be well placed to understand the `marketmaker` output, but if you haven’t here’s a brief summary of what the `marketmaker` does:

The marketmaker keeps the group, price and account data up-to-date and passes this fresh state to every ‘pulse’.

A ‘chain’ of pluggable objects of type `Element` look at the state every pulse and build a list of orders they would like to see on the orderbook.

Another pluggable object, this time of type `OrderReconciler` tries to reconcile the desired orders with the existing orders, and only cancel/replace where necessary.


## The Default ‘Chain’

Usually the head of the marketmaker ‘chain’ creates some desired orders, and they may be modified by subsequent elements in the chain.

The default chain is (in order):
- `confidenceinterval`
- `biasquoteonposition`
- `minimumcharge`
- `preventpostonlycrossingbook`
- `roundtolotsize`

Many more details about the chain, the default chain, and additional elements, can be found in the [OrderChain Guide](MarketmakingOrderChain.md)


## Frequently-Used Marketmaker Parameters

Here are some parameters that are commonly passed to the `marketmaker`.

- `--name` You need to give this instance a name. This appears in some error messages and notifications, and can help track down which marketmaker is having problems if you end up running multiple instances.

- `--group` The name of the Mango Group you want to use. (Optional - will use the default group in the `ids.json` file in the container if none is specified.)

- `--market` The name of the market you want to use. (Required. Must be an exact match for one of the markets in the configured group in the `ids.json` file in the container.)

- `--oracle-provider` **** You can pick the oracle to use for price information. Pyth is a common choice because the other options don’t provide a ‘confidence value’. Options are:
    - pyth
    - market
    - ftx
    - stub

- `--confidenceinterval-level` A weighting to apply to the confidence interval from the oracle: e.g. 1 - use the oracle confidence interval as the spread, 2 (risk averse, default) - multiply the oracle confidence interval by 2 to get the spread, 0.5 (aggressive) halve the oracle confidence interval to get the spread.

- `--confidenceinterval-position-size-ratio` This is the portion of your funds to use for each order. 0.01 is 1%.

- `--existing-order-tolerance` The marketmaker examines existing orders and compares them with the desired orders. If an existing order is within tolerance of the price and quantity of a desired order, it is kept. If not, it’s cancelled and a new order is placed. 0.0001 is 0.01%.

- `--pulse-interval` This is the interval (in seconds) between each marketmaker iteration. Each iteration it examines state, cancels orders and places orders - the ‘pulse interval’ is the number of seconds to wait between these iterations.

- `--order-type` The order type to use. POST_ONLY is a common choice for a marketmaker, although LIMIT is sometimes helpful. Options are:
    - POST_ONLY
    - LIMIT
    - IOC


# 11. 💸 Start The Marketmaker

OK, now we’re ready to try a test run of the marketmaker. This will be a ‘dry run’ so no orders will be placed or cancelled, but it will load the full data and calculate what orders it would have placed.

This is a long-running process, so we’ll need to use Control-C to cancel it when we’re done.

Here goes:
```
# mango-explorer marketmaker --name "BTC-PERP Marketmaker" --market BTC-PERP --oracle-provider pyth --confidenceinterval-position-size-ratio 0.1 --minimumcharge-ratio 0 --confidenceinterval-level 2 --confidenceinterval-level 4 --existing-order-tolerance 0.0001 --pulse-interval 30 --order-type POST_ONLY --biasquoteonposition-bias 0.00003 --log-level DEBUG --cluster-name devnet --dry-run
2021-08-27 19:26:09 ⚠ root
⚠ WARNING ⚠

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    🥭 Mango Markets: https://mango.markets
    📄 Documentation: https://docs.mango.markets/
    💬 Discord: https://discord.gg/67jySBhxrg
    🐦 Twitter: https://twitter.com/mangomarkets
    🚧 Github: https://github.com/blockworks-foundation
    📧 Email: mailto:hello@blockworks.foundation

2021-08-27 19:26:09 ⓘ root         « 𝙲𝚘𝚗𝚝𝚎𝚡𝚝 'BTC-PERP Marketmaker':
    Cluster Name: devnet
    Cluster URL: https://mango.devnet.rpcpool.com
    Group Name: devnet.2
    Group Address: Ec2enZyoC4nGpEfu2sUNAa2nUGJHWxoUWYSEJ2hNTWTA
    Mango Program Address: 4skJ85cdxQAFVKbcGgfun8iZPL7BadVYXG3kGEGkufqA
    Serum Program Address: DESVgJVGajEgKGXhb6XmqDHGz3VjdgP7rEVESBgxmroY
»
2021-08-27 19:26:09 ⓘ root         Cleaning up.
2021-08-27 19:26:09 ⓘ root         Settling.
2021-08-27 19:26:10 ⓘ root         Current assets in account E7R5k4tQKr2Doi3LvXLtSonRdgvXVGNFtL7fab2d2GjU (owner: 6MEVCr816wapduGknarkNRwMFWvFQSNv5h7iQEGGx8uB):
2021-08-27 19:26:10 ⓘ root                 0.00000000 MNGO
2021-08-27 19:26:10 ⓘ root                 0.00000000 BTC
2021-08-27 19:26:10 ⓘ root                 0.00000000 ETH
2021-08-27 19:26:10 ⓘ root                 0.00000000 SOL
2021-08-27 19:26:10 ⓘ root                 0.00000000 SRM
2021-08-27 19:26:10 ⓘ root                 0.00000000 RAY
2021-08-27 19:26:10 ⓘ root                 0.00000000 USDT
2021-08-27 19:26:10 ⓘ root            10,000.00000000 USDC
2021-08-27 19:26:40 🐛 PerpPollingM Poll for model state complete. Time taken: 0.27 seconds.
2021-08-27 19:26:40 🐛 ConfidenceIn Initial desired orders - spread 0.1 (48047.1 / 48047.2):
    « 𝙾𝚛𝚍𝚎𝚛 SELL for 0.02061363 at 48636.42500000 [ID: 0 / 0] POST_ONLY »
    « 𝙾𝚛𝚍𝚎𝚛 SELL for 0.02061363 at 48574.00300000 [ID: 0 / 0] POST_ONLY »
    « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02061363 at 48449.15900000 [ID: 0 / 0] POST_ONLY »
    « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02061363 at 48386.73700000 [ID: 0 / 0] POST_ONLY »
2021-08-27 19:26:40 🐛 BiasQuoteOnP Order change - quote_position_bias 0.00003 on inventory 0 / 0.02061363450512981632159133301 creates a (SELL more) bias factor of 1:
Old: « 𝙾𝚛𝚍𝚎𝚛 SELL for 0.02061363 at 48636.42500000 [ID: 0 / 0] POST_ONLY »
New: « 𝙾𝚛𝚍𝚎𝚛 SELL for 0.02061363 at 48636.42500000 [ID: 0 / 0] POST_ONLY »
2021-08-27 19:26:40 🐛 BiasQuoteOnP Order change - quote_position_bias 0.00003 on inventory 0 / 0.02061363450512981632159133301 creates a (SELL more) bias factor of 1:
Old: « 𝙾𝚛𝚍𝚎𝚛 SELL for 0.02061363 at 48574.00300000 [ID: 0 / 0] POST_ONLY »
New: « 𝙾𝚛𝚍𝚎𝚛 SELL for 0.02061363 at 48574.00300000 [ID: 0 / 0] POST_ONLY »
2021-08-27 19:26:40 🐛 BiasQuoteOnP Order change - quote_position_bias 0.00003 on inventory 0 / 0.02061363450512981632159133301 creates a (SELL more) bias factor of 1:
Old: « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02061363 at 48449.15900000 [ID: 0 / 0] POST_ONLY »
New: « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02061363 at 48449.15900000 [ID: 0 / 0] POST_ONLY »
2021-08-27 19:26:40 🐛 BiasQuoteOnP Order change - quote_position_bias 0.00003 on inventory 0 / 0.02061363450512981632159133301 creates a (SELL more) bias factor of 1:
Old: « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02061363 at 48386.73700000 [ID: 0 / 0] POST_ONLY »
New: « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02061363 at 48386.73700000 [ID: 0 / 0] POST_ONLY »
2021-08-27 19:26:40 🐛 PreventPostO Order change - would cross the orderbook 48047.1 / 48047.2:
                    Old: « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02061363 at 48449.15900000 [ID: 0 / 0] POST_ONLY »
                    New: « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02061363 at 48047.00000000 [ID: 0 / 0] POST_ONLY »
2021-08-27 19:26:40 🐛 PreventPostO Order change - would cross the orderbook 48047.1 / 48047.2:
                    Old: « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02061363 at 48386.73700000 [ID: 0 / 0] POST_ONLY »
                    New: « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02061363 at 48047.00000000 [ID: 0 / 0] POST_ONLY »
2021-08-27 19:26:40 ⓘ MarketMaker  Placing BTC-PERP « 𝙾𝚛𝚍𝚎𝚛 SELL for 0.02061363 at 48636.42500000 [ID: 0 / 7770238249772358986] POST_ONLY »
2021-08-27 19:26:40 ⓘ MarketMaker  Placing BTC-PERP « 𝙾𝚛𝚍𝚎𝚛 SELL for 0.02061363 at 48574.00300000 [ID: 0 / 2859503300814086774] POST_ONLY »
2021-08-27 19:26:40 ⓘ MarketMaker  Placing BTC-PERP « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02061363 at 48047.00000000 [ID: 0 / 1673093718900126195] POST_ONLY »
2021-08-27 19:26:40 ⓘ MarketMaker  Placing BTC-PERP « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02061363 at 48047.00000000 [ID: 0 / 3249291616693165281] POST_ONLY »
2021-08-27 19:26:40 ⓘ CombinableIn No instructions to run.
2021-08-27 19:27:10 🐛 PerpPollingM Poll for model state complete. Time taken: 0.25 seconds.
2021-08-27 19:27:10 🐛 ConfidenceIn Initial desired orders - spread 0.1 (48047.1 / 48047.2):
    « 𝙾𝚛𝚍𝚎𝚛 SELL for 0.02062572 at 48522.99500000 [ID: 0 / 0] POST_ONLY »
    « 𝙾𝚛𝚍𝚎𝚛 SELL for 0.02062572 at 48503.07400000 [ID: 0 / 0] POST_ONLY »
    « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02062572 at 48463.23200000 [ID: 0 / 0] POST_ONLY »
    « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02062572 at 48443.31100000 [ID: 0 / 0] POST_ONLY »
2021-08-27 19:27:10 🐛 BiasQuoteOnP Order change - quote_position_bias 0.00003 on inventory 0 / 0.02062572126858168650871365565 creates a (SELL more) bias factor of 1:
Old: « 𝙾𝚛𝚍𝚎𝚛 SELL for 0.02062572 at 48522.99500000 [ID: 0 / 0] POST_ONLY »
New: « 𝙾𝚛𝚍𝚎𝚛 SELL for 0.02062572 at 48522.99500000 [ID: 0 / 0] POST_ONLY »
2021-08-27 19:27:10 🐛 BiasQuoteOnP Order change - quote_position_bias 0.00003 on inventory 0 / 0.02062572126858168650871365565 creates a (SELL more) bias factor of 1:
Old: « 𝙾𝚛𝚍𝚎𝚛 SELL for 0.02062572 at 48503.07400000 [ID: 0 / 0] POST_ONLY »
New: « 𝙾𝚛𝚍𝚎𝚛 SELL for 0.02062572 at 48503.07400000 [ID: 0 / 0] POST_ONLY »
2021-08-27 19:27:10 🐛 BiasQuoteOnP Order change - quote_position_bias 0.00003 on inventory 0 / 0.02062572126858168650871365565 creates a (SELL more) bias factor of 1:
Old: « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02062572 at 48463.23200000 [ID: 0 / 0] POST_ONLY »
New: « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02062572 at 48463.23200000 [ID: 0 / 0] POST_ONLY »
2021-08-27 19:27:10 🐛 BiasQuoteOnP Order change - quote_position_bias 0.00003 on inventory 0 / 0.02062572126858168650871365565 creates a (SELL more) bias factor of 1:
Old: « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02062572 at 48443.31100000 [ID: 0 / 0] POST_ONLY »
New: « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02062572 at 48443.31100000 [ID: 0 / 0] POST_ONLY »
2021-08-27 19:27:10 🐛 PreventPostO Order change - would cross the orderbook 48047.1 / 48047.2:
                    Old: « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02062572 at 48463.23200000 [ID: 0 / 0] POST_ONLY »
                    New: « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02062572 at 48047.00000000 [ID: 0 / 0] POST_ONLY »
2021-08-27 19:27:10 🐛 PreventPostO Order change - would cross the orderbook 48047.1 / 48047.2:
                    Old: « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02062572 at 48443.31100000 [ID: 0 / 0] POST_ONLY »
                    New: « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02062572 at 48047.00000000 [ID: 0 / 0] POST_ONLY »
2021-08-27 19:27:10 ⓘ MarketMaker  Placing BTC-PERP « 𝙾𝚛𝚍𝚎𝚛 SELL for 0.02062572 at 48522.99500000 [ID: 0 / 1736108179658674344] POST_ONLY »
2021-08-27 19:27:10 ⓘ MarketMaker  Placing BTC-PERP « 𝙾𝚛𝚍𝚎𝚛 SELL for 0.02062572 at 48503.07400000 [ID: 0 / 6683862548063046667] POST_ONLY »
2021-08-27 19:27:10 ⓘ MarketMaker  Placing BTC-PERP « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02062572 at 48047.00000000 [ID: 0 / 8764500681576320674] POST_ONLY »
2021-08-27 19:27:10 ⓘ MarketMaker  Placing BTC-PERP « 𝙾𝚛𝚍𝚎𝚛 BUY for 0.02062572 at 48047.00000000 [ID: 0 / 1876564001497484494] POST_ONLY »
2021-08-27 19:27:10 ⓘ CombinableIn No instructions to run.
^C2021-08-27 19:27:19 ⓘ root         Shutting down...
2021-08-27 19:27:19 ⓘ root         Cleaning up.
2021-08-27 19:27:19 ⓘ root         Settling.
2021-08-27 19:27:19 ⓘ root         Shutdown complete.
```

Well, that all seemed fine.

Some important things to note from the simulated run:
* It does a bunch of checks on startup to make sure it is in a state that can run.
* It shows the orders it would have placed, if this hadn’t been a dry run.
* It outputs a **lot** of information. You can turn that down with the parameters `--log-level INFO` or `--log-level WARNING` when you’re confident of the marketmaker’s operation.
* It prints out some summary information about the current assets in the account.
* It pulses every 30 seconds, deciding which orders to place and which to cancel
* It sleeps between runs


# 12. ⚡ Really Start The Marketmaker

If you’ve got this far and you’re happy with the results, you can run the same command with the `--dry-run` parameter removed. That will start the marketmaker and have it place orders. This is all still on devnet, so no real funds are at stake.

Output should be broadly the same as the output for a ‘dry run’, but you’ll be able to see the orders appear on [Mango Devnet](https://devnet.mango.markets) and you’ll sometimes see errors from the chain or more detail from some of the transactions.

Now, it’s over to you. Happy marketmaking!
