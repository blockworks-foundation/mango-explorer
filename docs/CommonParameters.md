# 🥭 Mango Explorer

# 🏃‍ Common Parameters

Most command-line programs in `mango-explorer` take a lot of common parameters. This document describes them.

You can see exactly what parameters a command takes by specifying the `--help` parameter.


## 🗓️ Comming Up

This Quickstart will describe the following parameters:
1. `--name`
2. `--cluster-name`
3. `--cluster-url`
4. `--group-name`
5. `--commitment`
6. `--skip-preflight`
7. `--encoding`
8. `--blockhash-cache-duration`
9. `--stale-data-pause-before-retry`
10. `--stale-data-maximum-retries`
11. `--gma-chunk-size`
12. `--gma-chunk-pause`


# 1. `--name` parameter

> Specified using: `--name`

> Accepts parameter: `--name <NAME>` (optional, `string`, default: 'Mango Explorer')

This parameter allows you to set a name for this instance of the program, to appear in error messages. This can be useful for situations where, say, you're running 3 different marketmakers with a common alert channel - you can name each of the marketmakers as, say, `--name BTC-PERP` or `--name SOL-PERP` or `--name ETH/USDC`. The name will be show in errors and alerts, telling you which particular instance had the problem.


# 2. `--cluster-name` parameter

> Specified using: `--cluster-name`

> Accepts parameter: `--cluster-name <CLUSTER-NAME>` (optional, `string`, default: cluster name from the first defined group in the `ids.json` file)

Typically this will be specified using either `--cluster-name mainnet` or `--cluster-name devnet` but other names are possible. The first group in the ids.json file is usually the mainnet group, so effectively the default value is usually `mainnet`.


# 3. `--cluster-url` parameter

> Specified using: `--cluster-url`

> Accepts parameter: `--cluster-url <RPC-NODE-URL>` (optional, `URL`, default: default cluster URL for the current cluster)

This is maybe the most common parameter people need to specify.

This tells the command which RPC node to connect to, for requests and transactions. Mango provides a default URL for `mainnet` and `devnet` in the `ids.json` file but often people need or want to connect to a different one.

For example, to switch to the public Solana endpoint you would specify:
```
---cluster-url https://api.mainnet-beta.solana.com
```

There is an optional possibility to provide two parameters to the `--cluster-url` argument. Then the first parameter defines HTTP url of the RPC node
and the second one defines WS url of the RPC node.

For example, if you want to place order via one RPC node while loading market data via websocket connection from a different node
```
--cluster-url https://localhost:80 wss://localhost:443
```

There are several different RPC node providers now who provide free or premium RPC node connectivity. Use the URL they send you here.

**Note** This parameter is unusual in that it can be specified multiple times. This allows you to provide multiple RPC nodes and have the program switch to the next node if a node displays problems. For example, you can specify `--cluster-url` 3 times (with 3 different RPC URLs) and if one node starts rate-limiting you, the program will automatically switch to using the next node you specified. You'll only see exceptions if all 3 nodes have problems at the same time.


# 4. `--group-name` parameter

> Specified using: `--group-name`

> Accepts parameter: `--group-name <NAME>` (optional, `string`, default: name of the first group in the `ids.json` file)

This allows you to specify a particular group name. Usually this is `mainnet.1` on mainnet, or `devnet.2` on devnet, but there are other possiblities.


# 5. `--commitment` parameter

> Specified using: `--commitment`

> Accepts parameter: `--commitment <COMMITMENT-NAME>` (optional, `string`, default: 'processed')

Commitment is a [Solana term for specifying how 'finalized' a block is at a point in time](https://docs.solana.com/developing/clients/jsonrpc-api#configuring-state-commitment).

It details how certain you can be about the data. Possible values are, in order of confidence:
* `finalized`
* `confirmed`
* `processed` (default)

Processed is the default because most use-cases want speedy access to the latest data, even though that data isn't final. Other use cases may prefer more conservative commitments.


# 6. `--skip-preflight` parameter

> Specified using: `--skip-preflight`

> Accepts parameter: `--skip-preflight` (optional, TRUE if specified otherwise FALSE)

Transactions submitted to Solana RPC nodes can go through a preflight 'trial run'. This can be useful in checking that the transaction will be successful - transactions that fail at the preflight stage incur no transaction costs.

However, preflight can slow down processing or introduce problems of its own, so specifying `--skip-preflight` allows you to turn these 'trial runs' off.


# 7. `--encoding` parameter

> Specified using: `--encoding`

> Accepts parameter: `--encoding <ENCODING-NAME>` (optional, `string`, default: 'base64')

Specifies the encoding to request when receiving data from Solana. Possible options are:
* `base64` (default)
* `base58` (slow)
* `base64+zstd`
* `jsonParsed`

These options are described in [Solana's JSON API documentation for `getAccountInfo()`](https://docs.solana.com/developing/clients/jsonrpc-api#getaccountinfo).


# 8. `--blockhash-cache-duration` parameter

> Specified using: `--blockhash-cache-duration`

> Accepts parameter: `--blockhash-cache-duration <SECONDS>` (optional, `integer`, default: 0)

Solana requires a 'blockhash' be sent with each transaction (to prevent replay attacks). Caching blockhashes for a short while can be useful to improve performance for some use-cases.

This parameter allows you to specify how many seconds a blockhash may be cached for.

By default, this is 0 and blockhashes are not cached.


# 9. `--stale-data-pause-before-retry` parameter

> Specified using: `--stale-data-pause-before-retry`

> Accepts parameter: `--stale-data-pause-before-retry <PAUSE-SECONDS>` (optional, `float`, default: 0.1)

Fetching data from a cluster of load-balanced RPC nodes can sometimes result in one node returning data that is 'older' than data that has already been seen. Data returned from Solana returns the 'slot' number that was up-to-date as far as the commitment that was specified, so seeing a response from Solana that came from an earlier 'slot' means that the data may be out of date or 'stale'.

In situations like this it can be helpful to just re-submit the request automatically, in the hope that an up-to-date server responds this time.

This parameter specifies how long to pause before resubmitting.

> See also: `--stale-data-maximum-retries`

For example, to retry up to 5 times and pause 0.2 seconds between retries (taking up to 1 second), specify:
```
--stale-data-maximum-retries 5 --stale-data-pause-before-retry 0.2
```

# 10. `--stale-data-maximum-retries` parameter

> Specified using: `--stale-data-maximum-retries`

> Accepts parameter: `--stale-data-maximum-retries <NAME>` (optional, `int`, default: 'Mango Explorer')

Fetching data from a cluster of load-balanced RPC nodes can sometimes result in one node returning data that is 'older' than data that has already been seen. Data returned from Solana returns the 'slot' number that was up-to-date as far as the commitment that was specified, so seeing a response from Solana that came from an earlier 'slot' means that the data may be out of date or 'stale'.

In situations like this it can be helpful to just re-submit the request automatically, in the hope that an up-to-date server responds this time.

This parameter specifies how many times to resubmit before giving up.

> See also: `--stale-data-pause-before-retry`

For example, to retry up to 15 times and pause 0.3 seconds between retries (taking up to 4.5 seconds), specify:
```
--stale-data-maximum-retries 15 --stale-data-pause-before-retry 0.3
```

To disable this functionality completely, set  `--stale-data-maximum-retries` to zero:
```
--stale-data-maximum-retries 0
```


# 11. `--gma-chunk-size` parameter

> Specified using: `--gma-chunk-size`

> Accepts parameter: `--gma-chunk-size <CHUNK-SIZE>` (optional, `int`, default: 100)

Calls to `getMultipleAccounts()` can take many public keys as parameters, but most servers enforce a limit. Many servers enforce a maximum of 100 public keys in a single call.

Internally, `mango-explorer` may request an arbitrary number of accounts using calls to `getMultipleAccounts()` and this parameter specifies the maximum that can be fetched in a single `getMultipleAccounts()` call. Subsequent accounts will be automatically fetched in an additional `getMultipleAccounts()` call.

In effect, a large list of public keys will be split into 'chunks' of size `--gma-chunk-size`, and this will result in `(count of public keys / chunk size) + 1` calls to `getMultipleAccounts()`.


# 12. `--gma-chunk-pause` parameter

> Specified using: `--gma-chunk-pause`

> Accepts parameter: `--gma-chunk-pause <PAUSE-SECONDS>` (optional, `float`, default: 0)

Calls to `getMultipleAccounts()` can take many public keys as parameters, but most servers enforce a limit. Many servers enforce a rate limit on calls to .

Internally, `mango-explorer` may request an arbitrary number of accounts using calls to `getMultipleAccounts()` but many servers enforce a rate limit on calls to `getMultipleAccounts()`. This parameter specifies the time to pause between each `getMultipleAccounts()` call.
