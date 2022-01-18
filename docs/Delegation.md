# 🥭 Mango Explorer

# 🔥 Delegation

Mango Account Delegation is a feature that allows a separate account limited access to the Mango Account's features.

Delegation can provide some additional security for more sophisticated key management procedures.

A delegated account *can*, for example:
* Deposit funds
* Place orders
* Cancel orders

A delegated account *cannot*, for example:
* Withdraw funds
* Close the Mango Account

A Mango Account can have at most one delegate. The owner of the Mango Account continues to have full control of the Mango Account irrespective of delegation.


# 🆒 Commands

`mango-explorer` provides two commands for delegation: `delegate-account` and `show-delegated-accounts`.

You can see exactly what additional parameters a command takes by specifying the `--help` parameter.

## `delegate-account`

> Accepts parameter: `--account-address <ACCOUNT-PUBLIC-KEY>` (required, `PublicKey`, no default)

> Accepts parameter: `--delegate-address <DELEGATE-PUBLIC-KEY>` (optional, `PublicKey`, no default)

> Accepts parameter: `--revoke` (optional, TRUE if specified otherwise FALSE)

`delegate-account` allows you to set or revoke delegation of a Mango Account. It must be run by the owner of the Mango Account.


## `show-delegated-accounts`

> Accepts parameter: `--address <DELEGATE-PUBLIC-KEY>` (optional, `PublicKey`, default value: wallet root address)

`show-delegated-accounts` will list all accounts for which the current wallet is nominated as the delegate. **It will not** list accounts *owned* by the current wallet, only those in which it is listed as a delegate.


# ✅ Example Walkthrough

To run this walkthrough, you need to set up 2 different Solana wallets and 1 Mango Account. Choose one of the wallets as the Owner and use it to create a Mango Account. The other wallet is the Delegate.

In these examples,
* `ALBdwdFnHsmTAQ3xGqkDK8hcTMXeuMNyCNkz1ikBzv3L` is the address of the Mango Account Owner's wallet
* `7zTdp1YhPdBQw8nFJJXkmTewZf4zPwDbjktKzQLaQr62` is the address of the Mango Account
* `6aNN6nbAm9Dbqex9kKGAYcMFJg7Jhertwew9JhRv4QfB` is the address of Delegate's wallet


## Show No Delegate

*Run as Owner of the Mango Account*

This command will show the Mango Account, including what account (if any) is listed as a delegate:
```
show-accounts
```
This will output something like (abridged):
```
« Account (un-named), Version.V3 [7zTdp1YhPdBQw8nFJJXkmTewZf4zPwDbjktKzQLaQr62]
    « Metadata Version.V2 - Account: Initialized »
    Owner: ALBdwdFnHsmTAQ3xGqkDK8hcTMXeuMNyCNkz1ikBzv3L
    Delegated To: None
```


## Delegate Account

*Run as Owner of the Mango Account*

This command will grant the Delegate limited access to the Mango Account:
```
delegate-account --account-address 7zTdp1YhPdBQw8nFJJXkmTewZf4zPwDbjktKzQLaQr62 --delegate-address 6aNN6nbAm9Dbqex9kKGAYcMFJg7Jhertwew9JhRv4QfB
```


## Show Delegate

*Run as Owner of the Mango Account*

This command will now show the Mango Account with `6aNN6nbAm9Dbqex9kKGAYcMFJg7Jhertwew9JhRv4QfB` listed as a delegate:
```
show-accounts
```
This will output the address of the Delegate in the 'Delegated To' line (abridged):
```
« Account (un-named), Version.V3 [7zTdp1YhPdBQw8nFJJXkmTewZf4zPwDbjktKzQLaQr62]
    « Metadata Version.V2 - Account: Initialized »
    Owner: ALBdwdFnHsmTAQ3xGqkDK8hcTMXeuMNyCNkz1ikBzv3L
    Delegated To: 6aNN6nbAm9Dbqex9kKGAYcMFJg7Jhertwew9JhRv4QfB
```


## Show Delegated Account

*Run as Delegate*

This command will show all Mango Accounts with the current user listed as a delegate. If it is run as the user with the wallet address `6aNN6nbAm9Dbqex9kKGAYcMFJg7Jhertwew9JhRv4QfB` (the Delegate)
```
show-delegated-accounts
```
It will show the same output as `show-account` run by the Owner:
```
« Account (un-named), Version.V3 [7zTdp1YhPdBQw8nFJJXkmTewZf4zPwDbjktKzQLaQr62]
    « Metadata Version.V2 - Account: Initialized »
    Owner: ALBdwdFnHsmTAQ3xGqkDK8hcTMXeuMNyCNkz1ikBzv3L
    Delegated To: 6aNN6nbAm9Dbqex9kKGAYcMFJg7Jhertwew9JhRv4QfB
```


## Deposit

*Run as Delegate*

Delegates can deposit funds from their own wallet (not the Owner's wallet).
```
deposit --symbol SOL --quantity 1 --account-address 7zTdp1YhPdBQw8nFJJXkmTewZf4zPwDbjktKzQLaQr62
```
Note that to target an account which has been delegated, the `--account-address` parameter must be specified. (This is the same way an account is specified for wallets that hold multiple Mango Accounts.)


## Place Order

*Run as Delegate*

Delegates can place and cancel orders using the delegated Mango Account.
```
place-order --market SOL-PERP --quantity 1 --side BUY --order-type LIMIT --price 10 --skip-preflight --account-address 7zTdp1YhPdBQw8nFJJXkmTewZf4zPwDbjktKzQLaQr62
```

**Note**: it is the Delegate running this command so it is the Delegate that pays the SOL for the transaction.


## Withdraw

*Run as Delegate*

Delegates **cannot** withdraw funds from the delegated Mango Account. **This will fail**:
```
withdraw --symbol SOL --quantity 1 --account-address 7zTdp1YhPdBQw8nFJJXkmTewZf4zPwDbjktKzQLaQr62
```
**This will fail** with an error containing the following in the transaction logs:
```
Program log: MangoErrorCode::InvalidOwner; src/processor.rs
```

## Revoke Delegation

*Run as Owner of the Mango Account*

This command will revoke the delegated authority to the Delegate, removing their access to the Mango Account:
```
delegate-account --account-address 7zTdp1YhPdBQw8nFJJXkmTewZf4zPwDbjktKzQLaQr62 --revoke
```


## Show No Delegated Accounts

*Run as Delegate*

Running the same command as earlier:
```
show-delegated-accounts
```
Now shows no delegated accounts, since the delegation was revoked:
```
Account 6aNN6nbAm9Dbqex9kKGAYcMFJg7Jhertwew9JhRv4QfB has no accounts delegated to it.
```
