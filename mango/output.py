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

import collections.abc
import enum
import json
import jsons
import typing

from dataclasses import dataclass
from solana.publickey import PublicKey


# # 🥭 OutputFormat enum
#
# How should we format any output?
#
class OutputFormat(enum.Enum):
    # We use strings here so that argparse can work with these as parameters.
    TEXT = "TEXT"
    JSON = "JSON"
    CSV = "CSV"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self}"


def to_json(obj: typing.Any) -> str:
    return json.dumps(
        jsons.dump(
            obj,
            strip_attr=(
                "data",
                "_logger",
                "lot_size_converter",
                "tokens",
                "tokens_by_index",
                "slots",
                "base_tokens",
                "base_tokens_by_index",
                "oracles",
                "oracles_by_index",
                "spot_markets",
                "spot_markets_by_index",
                "perp_markets",
                "perp_markets_by_index",
                "shared_quote_token",
                "liquidity_incentive_token",
            ),
            key_transformer=jsons.KEY_TRANSFORMER_CAMELCASE,
        ),
        sort_keys=True,
        indent=4,
    )


@dataclass
class OutputFormatter:
    format: OutputFormat

    def out(self, *obj: typing.Any) -> None:
        if (
            len(obj) == 1
            and isinstance(obj[0], collections.abc.Sequence)
            and not isinstance(obj[0], str)
        ):
            for item in obj[0]:
                self.single_out(item)
        elif isinstance(obj[0], str):
            self.multi_out(*obj)
        else:
            for item in obj:
                self.single_out(item)

    def single_out(self, obj: typing.Any) -> None:
        if self.format == OutputFormat.JSON:
            json_value: str
            if "to_json" in dir(obj):
                json_value = obj.to_json()
            else:
                json_value = to_json(obj)
            print(json_value)
        elif self.format == OutputFormat.CSV:
            if "to_csv" in dir(obj):
                csv_value: str = obj.to_csv()
                print(csv_value)
            else:
                raise Exception("CSV output is not supported for this item.")
        else:
            print(obj)

    def multi_out(self, *obj: typing.Any) -> None:
        if self.format == OutputFormat.JSON:
            json_value: str
            if all("to_json" in dir(inner) for inner in obj):
                json_value = "[" + ",".join(inner.to_json() for inner in obj) + "]"
            else:
                json_value = to_json(obj)
            print(json_value)
        elif self.format == OutputFormat.CSV:
            if all("to_csv" in dir(inner) for inner in obj):
                csv_value = "\n\n".join(inner.to_csv() for inner in obj)
                print(csv_value)
            else:
                raise Exception("CSV output is not supported for this item.")
        else:
            print(*obj)


output_formatter: OutputFormatter = OutputFormatter(OutputFormat.TEXT)


jsons.set_serializer(lambda pubkey, **_: f"{pubkey}", PublicKey)


def output(*obj: typing.Any) -> None:
    output_formatter.out(*obj)
