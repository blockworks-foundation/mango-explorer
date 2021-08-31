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

import argparse
import typing

from decimal import Decimal

from ...orders import OrderType
from .biasquoteonpositionelement import BiasQuoteOnPositionElement
from .chain import Chain
from .confidenceintervalspreadelement import ConfidenceIntervalSpreadElement
from .element import Element
from .minimumchargeelement import MinimumChargeElement
from .preventpostonlycrossingbookelement import PreventPostOnlyCrossingBookElement
from .roundtolotsizeelement import RoundToLotSizeElement


# # 🥭 ChainBuilder class
#
# A `ChainBuilder` class to allow building a `Chain`, keeping parameter and constructor complexities all in
# one place.
#
class ChainBuilder:
    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--order-type", type=OrderType, default=OrderType.POST_ONLY,
                            choices=list(OrderType), help="Order type: LIMIT, IOC or POST_ONLY")
        parser.add_argument("--position-size-ratio", type=Decimal, required=True,
                            help="fraction of the token inventory to be bought or sold in each order")
        parser.add_argument("--confidence-interval-level", type=Decimal, action="append",
                            help="the levels of weighting to apply to the confidence interval from the oracle: e.g. 1 - use the oracle confidence interval as the spread, 2 (risk averse, default) - multiply the oracle confidence interval by 2 to get the spread, 0.5 (aggressive) halve the oracle confidence interval to get the spread (can be specified multiple times to give multiple levels)")
        parser.add_argument("--quote-position-bias", type=Decimal, default=Decimal(0),
                            help="bias to apply to quotes based on inventory position")
        parser.add_argument("--minimum-charge-ratio", type=Decimal, default=Decimal("0.0005"),
                            help="minimum fraction of the price to be accept as a spread")

    # This function is the converse of `add_command_line_parameters()` - it takes
    # an argument of parsed command-line parameters and expects to see the ones it added
    # to that collection in the `add_command_line_parameters()` call.
    #
    # It then uses those parameters to create a properly-configured `Chain` object.
    #
    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> Chain:
        confidence_interval_levels: typing.Sequence[Decimal] = args.confidence_interval_level
        if len(confidence_interval_levels) == 0:
            confidence_interval_levels = [Decimal(2)]
        elements: typing.List[Element] = [
            ConfidenceIntervalSpreadElement(args.position_size_ratio, confidence_interval_levels, args.order_type),
            BiasQuoteOnPositionElement(args.quote_position_bias),
            MinimumChargeElement(args.minimum_charge_ratio),
            PreventPostOnlyCrossingBookElement(),
            RoundToLotSizeElement()
        ]

        return Chain(elements)
