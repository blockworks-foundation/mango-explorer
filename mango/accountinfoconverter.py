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

from .account import Account
from .accountinfo import AccountInfo
from .addressableaccount import AddressableAccount
from .cache import Cache
from .context import Context
from .group import Group
from .layouts import layouts
from .lotsizeconverter import NullLotSizeConverter
from .openorders import OpenOrders
from .perpeventqueue import PerpEventQueue
from .perpmarketdetails import PerpMarketDetails
from .rootbank import RootBank
from .serumeventqueue import SerumEventQueue


# # 🥭 build_account_info_converter function
#
# Given a `Context` and an account type, returns a function that can take an `AccountInfo` and
# return one of our objects.
#
def build_account_info_converter(context: Context, account_type: str) -> typing.Callable[[AccountInfo], AddressableAccount]:
    account_type_upper = account_type.upper()
    if account_type_upper == "GROUP":
        return lambda account_info: Group.parse(context, account_info)
    elif account_type_upper == "ACCOUNT":
        def account_loader(account_info: AccountInfo) -> Account:
            layout_account = layouts.MANGO_ACCOUNT.parse(account_info.data)
            group_address = layout_account.group
            group: Group = Group.load(context, group_address)
            return Account.parse(account_info, group)
        return account_loader
    elif account_type_upper == "OPENORDERS":
        return lambda account_info: OpenOrders.parse(account_info, Decimal(6), Decimal(6))
    elif account_type_upper == "PERPEVENTQUEUE":
        return lambda account_info: PerpEventQueue.parse(account_info, NullLotSizeConverter())
    elif account_type_upper == "SERUMEVENTQUEUE":
        return lambda account_info: SerumEventQueue.parse(account_info)
    elif account_type_upper == "CACHE":
        return lambda account_info: Cache.parse(account_info)
    elif account_type_upper == "ROOTBANK":
        return lambda account_info: RootBank.parse(account_info)
    elif account_type_upper == "PERPMARKETDETAILS":
        def perp_market_details_loader(account_info: AccountInfo) -> PerpMarketDetails:
            layout_perp_market_details = layouts.PERP_MARKET.parse(account_info.data)
            group_address = layout_perp_market_details.group
            group: Group = Group.load(context, group_address)
            return PerpMarketDetails.parse(account_info, group)
        return perp_market_details_loader

    raise Exception(f"Could not find AccountInfo converter for type {account_type}.")
