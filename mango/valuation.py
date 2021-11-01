# # ⚠ Warning
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
# NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# [🥭 Mango Markets](https://markets/) support is available at:
#   [Docs](https://docs.markets/)
#   [Discord](https://discord.gg/67jySBhxrg)
#   [Twitter](https://twitter.com/mangomarkets)
#   [Github](https://github.com/blockworks-foundation)
#   [Email](mailto:hello@blockworks.foundation)

import typing

from datetime import datetime
from decimal import Decimal
from solana.publickey import PublicKey

from .account import Account
from .accounttokenvalues import AccountTokenValues
from .cache import Cache
from .context import Context
from .group import Group
from .openorders import OpenOrders
from .token import Token, SolToken
from .tokenvalue import TokenValue


class TokenValuation:
    def __init__(self, raw_token_value: TokenValue, price_token_value: TokenValue, value_token_value: TokenValue):
        self.raw: TokenValue = raw_token_value
        self.price: TokenValue = price_token_value
        self.value: TokenValue = value_token_value

    @staticmethod
    def from_json_dict(context: Context, json: typing.Dict[str, typing.Any]) -> "TokenValuation":
        symbol: str = json["symbol"]
        value_currency: str = json["valueCurrency"]
        balance: Decimal = Decimal(json["balance"])
        price: Decimal = Decimal(json["price"])
        value: Decimal = Decimal(json["value"])
        token = context.token_lookup.find_by_symbol(symbol)
        if token is None:
            raise Exception(f"Could not find token for symbol: {symbol}")
        currency_token = context.token_lookup.find_by_symbol(value_currency)
        if currency_token is None:
            raise Exception(f"Could not find token for currency symbol: {value_currency}")
        raw_token_value: TokenValue = TokenValue(token, balance)
        price_token_value: TokenValue = TokenValue(currency_token, price)
        value_token_value: TokenValue = TokenValue(currency_token, value)
        return TokenValuation(raw_token_value, price_token_value, value_token_value)

    @staticmethod
    def from_token_balance(context: Context, group: Group, cache: Cache, token_balance: TokenValue) -> "TokenValuation":
        token_to_lookup: Token = token_balance.token
        if token_balance.token == SolToken:
            token_to_lookup = context.token_lookup.find_by_symbol_or_raise("SOL")
        cached_token_price: TokenValue = group.token_price_from_cache(cache, token_to_lookup)
        balance_value: TokenValue = token_balance * cached_token_price
        return TokenValuation(token_balance, cached_token_price, balance_value)

    @staticmethod
    def all_from_wallet(context: Context, group: Group, cache: Cache, address: PublicKey) -> typing.Sequence["TokenValuation"]:
        balances = group.fetch_balances(context, address)
        wallet_tokens: typing.List[TokenValuation] = []
        for balance in balances:
            if balance.value != 0:
                wallet_tokens += [TokenValuation.from_token_balance(context, group, cache, balance)]
        return wallet_tokens

    def to_json_dict(self) -> typing.Dict[str, typing.Any]:
        return {
            "symbol": self.raw.token.symbol,
            "valueCurrency": self.price.token.symbol,
            "balance": f"{self.raw.value:.8f}",
            "price": f"{self.price.value:.8f}",
            "value": f"{self.value.value:.8f}",
        }

    def __str__(self) -> str:
        return f"   {self.raw:<45} worth {self.value}"


class AccountValuation:
    def __init__(self, name: str, address: PublicKey, tokens: typing.Sequence[TokenValuation]):
        self.name: str = name
        self.address: PublicKey = address
        self.tokens: typing.Sequence[TokenValuation] = tokens

    @property
    def value(self) -> TokenValue:
        return sum((t.value for t in self.tokens[1:]), start=self.tokens[0].value)

    @staticmethod
    def from_json_dict(context: Context, json: typing.Dict[str, typing.Any]) -> "AccountValuation":
        name: str = json["name"]
        address: PublicKey = PublicKey(json["address"])
        tokens: typing.List[TokenValuation] = []
        for token_dict in json["tokens"]:
            token_valuation: TokenValuation = TokenValuation.from_json_dict(context, token_dict)
            tokens += [token_valuation]

        return AccountValuation(name, address, tokens)

    @staticmethod
    def from_account(context: Context, group: Group, account: Account, cache: Cache) -> "AccountValuation":
        open_orders: typing.Dict[str, OpenOrders] = account.load_all_spot_open_orders(context)
        token_values: typing.List[TokenValuation] = []
        for asset in account.basket:
            if (asset.net_value.value != 0) or ((asset.perp_account is not None) and not asset.perp_account.empty):
                report: AccountTokenValues = AccountTokenValues.from_account_basket_base_token(
                    asset, open_orders, group)
                asset_valuation = TokenValuation.from_token_balance(context, group, cache, report.net_value)
                token_values += [asset_valuation]

        quote_valuation = TokenValuation.from_token_balance(context, group, cache, account.shared_quote_token.net_value)
        token_values += [quote_valuation]

        return AccountValuation(account.info, account.address, token_values)

    def to_json_dict(self) -> typing.Dict[str, typing.Any]:
        value: TokenValue = self.value
        return {
            "name": self.name,
            "address": f"{self.address}",
            "value": f"{value.value:.8f}",
            "valueCurrency": value.token.symbol,
            "tokens": list([tok.to_json_dict() for tok in self.tokens])
        }


class Valuation:
    def __init__(self, timestamp: datetime, address: PublicKey, wallet_tokens: typing.Sequence[TokenValuation], accounts: typing.Sequence[AccountValuation]):
        self.timestamp: datetime = timestamp
        self.address: PublicKey = address
        self.wallet_tokens: typing.Sequence[TokenValuation] = wallet_tokens
        self.accounts: typing.Sequence[AccountValuation] = accounts

    @property
    def value(self) -> TokenValue:
        wallet_tokens_value: TokenValue = sum(
            (t.value for t in self.wallet_tokens[1:]), start=self.wallet_tokens[0].value)
        return sum((acc.value for acc in self.accounts), start=wallet_tokens_value)

    @staticmethod
    def from_json_dict(context: Context, json: typing.Dict[str, typing.Any]) -> "Valuation":
        timestamp: datetime = datetime.fromisoformat(json["timestamp"])
        address: PublicKey = PublicKey(json["address"])
        wallet_tokens: typing.List[TokenValuation] = []
        for token_dict in json["wallet"]["tokens"]:
            token_valuation: TokenValuation = TokenValuation.from_json_dict(context, token_dict)
            wallet_tokens += [token_valuation]

        accounts: typing.List[AccountValuation] = []
        for account_dict in json["accounts"]:
            account_valuation: AccountValuation = AccountValuation.from_json_dict(context, account_dict)
            accounts += [account_valuation]

        return Valuation(timestamp, address, wallet_tokens, accounts)

    @staticmethod
    def from_wallet(context: Context, group: Group, cache: Cache, address: PublicKey) -> "Valuation":
        spl_tokens = TokenValuation.all_from_wallet(context, group, cache, address)

        mango_accounts = Account.load_all_for_owner(context, address, group)
        account_valuations = []
        for account in mango_accounts:
            account_valuations += [AccountValuation.from_account(context, group, account, cache)]

        return Valuation(datetime.now(), address, spl_tokens, account_valuations)

    def to_json_dict(self) -> typing.Dict[str, typing.Any]:
        value: TokenValue = self.value
        wallet_value: TokenValue = sum(
            (t.value for t in self.wallet_tokens[1:]), start=self.wallet_tokens[0].value)
        return {
            "timestamp": self.timestamp.isoformat(),
            "address": f"{self.address}",
            "value": f"{value.value:.8f}",
            "valueCurrency": value.token.symbol,
            "wallet": {
                "value": f"{wallet_value.value:.8f}",
                "valueCurrency": wallet_value.token.symbol,
                "tokens": list([tok.to_json_dict() for tok in self.wallet_tokens])
            },
            "accounts": list([acc.to_json_dict() for acc in self.accounts])
        }

    def __str__(self) -> str:
        address: str = f"{self.address}:"
        wallet_total: TokenValue = sum(
            (t.value for t in self.wallet_tokens[1:]), start=self.wallet_tokens[0].value)
        accounts: typing.List[str] = []
        for account in self.accounts:
            account_tokens: str = "\n        ".join([f"{item}" for item in account.tokens])
            accounts += [f"""Account '{account.name}' (total: {account.value}):
        {account_tokens}"""]

        accounts_tokens: str = "\n        ".join(accounts)
        wallet_tokens: str = "\n        ".join([f"{item}" for item in self.wallet_tokens])
        return f"""« 𝚅𝚊𝚕𝚞𝚊𝚝𝚒𝚘𝚗 of {address:<47} {self.value}
    Wallet Tokens (total: {wallet_total}):
        {wallet_tokens}
    {accounts_tokens}
»"""
