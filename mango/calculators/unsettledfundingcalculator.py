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

from ..token import Token
from ..tokenvalue import TokenValue


class UnsettledFundingParams(typing.NamedTuple):
    quote_token: Token
    base_position: TokenValue
    long_funding: Decimal
    long_settled_funding: Decimal
    short_funding: Decimal
    short_settled_funding: Decimal


def calculate_unsettled_funding(params: UnsettledFundingParams) -> TokenValue:
    result: Decimal
    if params.base_position > 0:
        result = params.base_position.value * (params.long_funding - params.long_settled_funding)
    else:
        result = params.base_position.value * (params.short_funding - params.short_settled_funding)

    return TokenValue(params.quote_token, result)
