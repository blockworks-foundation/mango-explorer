# # ⚠ Warning
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
# NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# [🥭 Mango Markets](https://mango.markets/) support is available at:
#   [Docs](https://docs.mango.markets/)
#   [Discord](https://discord.gg/67jySBhxrg)
#   [Twitter](https://twitter.com/mangomarkets)
#   [Github](https://github.com/blockworks-foundation)
#   [Email](mailto:hello@blockworks.foundation)


import typing

from decimal import Decimal

from solana.publickey import PublicKey

from .account import Account
from .accountinfo import AccountInfo
from .addressableaccount import AddressableAccount
from .cache import Cache
from .constants import SYSTEM_PROGRAM_ADDRESS
from .context import Context
from .group import Group
from .layouts import layouts
from .lotsizeconverter import LotSizeConverter, NullLotSizeConverter
from .openorders import OpenOrders
from .perpeventqueue import PerpEvent, PerpEventQueue, UnseenPerpEventChangesTracker
from .perpmarket import PerpOrderBookSide
from .perpmarketdetails import PerpMarketDetails
from .serumeventqueue import SerumEvent, SerumEventQueue, UnseenSerumEventChangesTracker
from .tokens import Instrument, Token
from .tokenbank import NodeBank, RootBank, TokenBank


# # 🥭 build_account_info_converter function
#
# Given a `Context` and an account type, returns a function that can take an `AccountInfo` and
# return one of our objects.
#
def build_account_info_converter(
    context: Context, account_type: str
) -> typing.Union[
    typing.Callable[[AccountInfo], AddressableAccount],
    typing.Callable[[AccountInfo], typing.Sequence[typing.Any]],
]:
    account_type_upper = account_type.upper()
    if account_type_upper == "ACCOUNTINFO":
        return lambda account_info: account_info
    elif account_type_upper == "GROUP":
        return lambda account_info: Group.parse_with_context(context, account_info)
    elif account_type_upper == "ACCOUNT" or account_type_upper == "MANGOACCOUNT":

        def account_loader(account_info: AccountInfo) -> Account:
            layout_account = layouts.MANGO_ACCOUNT.parse(account_info.data)
            group_address = layout_account.group
            group: Group = Group.load(context, group_address)
            cache: Cache = group.fetch_cache(context)
            return Account.parse(account_info, group, cache)

        return account_loader
    elif account_type_upper == "OPENORDERS":
        base = Token(
            "FAKEBASE",
            "Fake Base Token",
            Decimal(6),
            SYSTEM_PROGRAM_ADDRESS,
        )
        quote = Token(
            "FAKEQUOTE",
            "Fake Quote Token",
            Decimal(6),
            SYSTEM_PROGRAM_ADDRESS,
        )
        return lambda account_info: OpenOrders.parse(account_info, base, quote)
    elif account_type_upper == "CACHE":
        return lambda account_info: Cache.parse(account_info)
    elif account_type_upper == "ROOTBANK":
        return lambda account_info: RootBank.parse(account_info)
    elif account_type_upper == "NODEBANK":
        return lambda account_info: NodeBank.parse(account_info)
    elif account_type_upper == "PERPMARKETDETAILS":

        def perp_market_details_loader(account_info: AccountInfo) -> PerpMarketDetails:
            layout_perp_market_details = layouts.PERP_MARKET.parse(account_info.data)
            group_address = layout_perp_market_details.group
            group: Group = Group.load(context, group_address)
            return PerpMarketDetails.parse(account_info, group)

        return perp_market_details_loader
    elif account_type_upper == "PERPORDERBOOKSIDE":

        class __FakePerpMarketDetails(PerpMarketDetails):
            def __init__(self) -> None:
                self.base_instrument = Instrument(
                    "UNKNOWNBASE", "Unknown Base", Decimal(0)
                )
                self.quote_token = TokenBank(
                    Token("UNKNOWNQUOTE", "Unknown Quote", Decimal(0), PublicKey(0)),
                    PublicKey(0),
                )
                self.base_lot_size = Decimal(1)
                self.quote_lot_size = Decimal(1)

        return lambda account_info: PerpOrderBookSide.parse(
            account_info, __FakePerpMarketDetails()
        )
    elif account_type_upper == "SERUMEVENTQUEUE":
        return lambda account_info: SerumEventQueue.parse(account_info)
    elif account_type_upper == "SERUMEVENTS":
        serum_splitter: typing.Optional[UnseenSerumEventChangesTracker] = None

        def __split_serum_events(
            account_info: AccountInfo,
        ) -> typing.Sequence[SerumEvent]:
            nonlocal serum_splitter
            if serum_splitter is None:
                initial_serum_event_queue: SerumEventQueue = SerumEventQueue.parse(
                    account_info
                )
                serum_splitter = UnseenSerumEventChangesTracker(
                    initial_serum_event_queue
                )
            serum_event_queue: SerumEventQueue = SerumEventQueue.parse(account_info)
            return serum_splitter.unseen(serum_event_queue)

        return __split_serum_events
    elif account_type_upper == "PERPEVENTQUEUE":
        return lambda account_info: PerpEventQueue.parse(
            account_info, NullLotSizeConverter()
        )
    elif account_type_upper == "PERPEVENTS":
        # It'd be nice to get the market's lot size converter, but we don't have its address yet.
        lot_size_converter: LotSizeConverter = NullLotSizeConverter()
        perp_splitter: typing.Optional[UnseenPerpEventChangesTracker] = None

        def __split_perp_events(
            account_info: AccountInfo,
        ) -> typing.Sequence[PerpEvent]:
            nonlocal perp_splitter
            if perp_splitter is None:
                initial_perp_event_queue: PerpEventQueue = PerpEventQueue.parse(
                    account_info, lot_size_converter
                )
                perp_splitter = UnseenPerpEventChangesTracker(initial_perp_event_queue)
            perp_event_queue: PerpEventQueue = PerpEventQueue.parse(
                account_info, lot_size_converter
            )
            return perp_splitter.unseen(perp_event_queue)

        return __split_perp_events

    raise Exception(f"Could not find AccountInfo converter for type {account_type}.")
