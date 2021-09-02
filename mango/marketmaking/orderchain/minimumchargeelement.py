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
import mango
import typing

from decimal import Decimal

from .element import Element
from ..modelstate import ModelState


# # 🥭 MinimumChargeElement class
#
# May modifiy an `Order`s price if it would result in too small a difference from the mid-price, meaning less
# of a charge if that `Order` is filled.
#
class MinimumChargeElement(Element):
    def __init__(self, args: argparse.Namespace):
        super().__init__(args)
        self.minimum_charge_ratio: Decimal = args.minimum_charge_ratio

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--minimum-charge-ratio", type=Decimal, default=Decimal("0.0005"),
                            help="minimum fraction of the price to be accept as a spread")

    def process(self, context: mango.Context, model_state: ModelState, orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        # From Daffy on 26th July 2021: max(pyth_conf * 2, price * min_charge)
        # (Private chat link: https://discord.com/channels/@me/832570058861314048/869208592648134666)
        new_orders: typing.List[mango.Order] = []
        for order in orders:
            minimum_charge = model_state.price.mid_price * self.minimum_charge_ratio
            current_charge = (model_state.price.mid_price - order.price).copy_abs()
            if current_charge > minimum_charge:
                # All OK with current order
                new_orders += [order]
            else:
                if order.side == mango.Side.BUY:
                    new_price: Decimal = model_state.price.mid_price - minimum_charge
                else:
                    new_price = model_state.price.mid_price + minimum_charge
                new_order = order.with_price(new_price)
                self.logger.debug(f"""Order change - price is less than minimum charge:
    Old: {order}
    New: {new_order}""")
                new_orders += [new_order]

        return new_orders

    def __str__(self) -> str:
        return f"« 𝙼𝚒𝚗𝚒𝚖𝚞𝚖𝙲𝚑𝚊𝚛𝚐𝚎𝙴𝚕𝚎𝚖𝚎𝚗𝚝 - minimum charge ratio: {self.minimum_charge_ratio} »"
