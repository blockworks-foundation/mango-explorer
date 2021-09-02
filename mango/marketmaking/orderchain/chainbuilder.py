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

from ...orders import OrderType
from .biasquoteonpositionelement import BiasQuoteOnPositionElement
from .chain import Chain
from .confidenceintervalspreadelement import ConfidenceIntervalSpreadElement
from .element import Element
from .fixedratioselement import FixedRatiosElement
from .minimumchargeelement import MinimumChargeElement
from .preventpostonlycrossingbookelement import PreventPostOnlyCrossingBookElement
from .roundtolotsizeelement import RoundToLotSizeElement

_DEFAULT_CHAIN = [
    "confidenceintervalspread",
    "biasquoteonposition",
    "minimumcharge",
    "preventpostonlycrossingbook",
    "roundtolotsize"
]


# # 🥭 ChainBuilder class
#
# A `ChainBuilder` class to allow building a `Chain`, keeping parameter and constructor complexities all in
# one place.
#
class ChainBuilder:
    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--chain", type=str, action="append", default=[],
                            help="The specific order chain elements to use instead of the default chain")
        # OrderType is used by multiple elements so specify it here rather than have them fighting over which
        # one specifies it.
        parser.add_argument("--order-type", type=OrderType, default=OrderType.POST_ONLY,
                            choices=list(OrderType), help="Order type: LIMIT, IOC or POST_ONLY")
        # Now add args for all the elements.
        BiasQuoteOnPositionElement.add_command_line_parameters(parser)
        ConfidenceIntervalSpreadElement.add_command_line_parameters(parser)
        FixedRatiosElement.add_command_line_parameters(parser)
        MinimumChargeElement.add_command_line_parameters(parser)
        PreventPostOnlyCrossingBookElement.add_command_line_parameters(parser)
        RoundToLotSizeElement.add_command_line_parameters(parser)

    # This function is the converse of `add_command_line_parameters()` - it takes
    # an argument of parsed command-line parameters and expects to see the ones it added
    # to that collection in the `add_command_line_parameters()` call.
    #
    # It then uses those parameters to create a properly-configured `Chain` object.
    #
    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> Chain:
        chain_names: typing.Sequence[str] = args.chain
        if chain_names is None or len(chain_names) == 0:
            chain_names = _DEFAULT_CHAIN

        elements: typing.List[Element] = []
        for name in chain_names:
            element = ChainBuilder._create_element_by_name(args, name)
            elements += [element]

        return Chain(elements)

    @staticmethod
    def _create_element_by_name(args: argparse.Namespace, name: str) -> Element:
        proper_name: str = name.upper()
        if proper_name == "BIASQUOTEONPOSITION":
            return BiasQuoteOnPositionElement(args)
        elif proper_name == "CONFIDENCEINTERVALSPREAD":
            return ConfidenceIntervalSpreadElement(args)
        elif proper_name == "FIXEDRATIOS":
            return FixedRatiosElement(args)
        elif proper_name == "MINIMUMCHARGE":
            return MinimumChargeElement(args)
        elif proper_name == "PREVENTPOSTONLYCROSSINGBOOK":
            return PreventPostOnlyCrossingBookElement(args)
        elif proper_name == "ROUNDTOLOTSIZE":
            return RoundToLotSizeElement(args)
        else:
            raise Exception(f"Unknown chain element: '{proper_name}'")
