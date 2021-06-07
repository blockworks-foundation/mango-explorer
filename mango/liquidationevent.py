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

import datetime
import typing

from solana.publickey import PublicKey

from .tokenvalue import TokenValue

# # 🥭 LiquidationEvent class
#


class LiquidationEvent:
    def __init__(self, timestamp: datetime.datetime, liquidator_name: str, group_name: str, succeeded: bool, signature: str, wallet_address: PublicKey, margin_account_address: PublicKey, balances_before: typing.List[TokenValue], balances_after: typing.List[TokenValue]):
        self.timestamp: datetime.datetime = timestamp
        self.liquidator_name: str = liquidator_name
        self.group_name: str = group_name
        self.succeeded: bool = succeeded
        self.signature: str = signature
        self.wallet_address: PublicKey = wallet_address
        self.margin_account_address: PublicKey = margin_account_address
        self.balances_before: typing.List[TokenValue] = balances_before
        self.balances_after: typing.List[TokenValue] = balances_after
        self.changes: typing.List[TokenValue] = TokenValue.changes(balances_before, balances_after)

    def __str__(self) -> str:
        result = "✅" if self.succeeded else "❌"
        changes_text = "\n        ".join([f"{change.value:>15,.8f} {change.token.symbol}" for change in self.changes])
        return f"""« 🥭 Liqudation Event {result} at {self.timestamp}
    💧 Liquidator: {self.liquidator_name}
    🗃️ Group: {self.group_name}
    📇 Signature: {self.signature}
    👛 Wallet: {self.wallet_address}
    💳 Margin Account: {self.margin_account_address}
    💸 Changes:
        {changes_text}
»"""

    def __repr__(self) -> str:
        return f"{self}"
