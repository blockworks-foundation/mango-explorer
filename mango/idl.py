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

import base64
import construct
import hashlib
import json
import os.path
import typing

from .constants import DATA_PATH
from .layouts import layouts

_known_idl_type_adapters: typing.Dict[str, typing.Callable[[], typing.Any]] = {
    "publicKey": lambda: layouts.PublicKeyAdapter(),
    "bool": lambda: construct.Flag,
    "u8": lambda: layouts.DecimalAdapter(1),
    "u64": lambda: layouts.DecimalAdapter(),
    "u128": lambda: layouts.DecimalAdapter(16),
    "i8": lambda: layouts.SignedDecimalAdapter(1),
    "i64": lambda: layouts.SignedDecimalAdapter(),
    "i128": lambda: layouts.SignedDecimalAdapter(16),
}


class IdlType:
    def __init__(self, name: str, struct: typing.Any) -> None:
        self.name: str = name
        self.struct: typing.Any = struct


# This really only parses a subset of the IDL. For Mango right now, we only need to parse the
# events, and they have a limited set of types.
#
# We are able to re-use the adapters from the layouts, which is great!
#
# One wrinkle is that IDL has a 'vec' type to describe its arrays. It looks to be a 4-byte prefix
# contains the length of the array, so we can't use fixed structs - we need to use the construct
# context to parse the array length, then refer to that in the next element as the length of
# the construct.Array.
def _load_idl_parsers_from_json_file(filepath: str) -> typing.Dict[bytes, IdlType]:
    def _discriminator_from_name(name: str) -> bytes:
        sha = hashlib.sha256(f"event:{name}".encode())
        return sha.digest()[0:8]

    def _context_counter_lookup(field_counter: str) -> typing.Callable[[typing.Any], int]:
        return lambda ctx: int(ctx[field_counter])

    with open(filepath, encoding="utf-8") as json_file:
        idl_data: typing.Dict[str, typing.Any] = json.load(json_file)

    layout_loaders: typing.Dict[bytes, IdlType] = {}
    for event in idl_data["events"]:
        event_name: str = event["name"]
        discriminator = _discriminator_from_name(event_name)
        fields = []
        for field in event["fields"]:
            field_name: str = field["name"]
            field_type: str = field["type"]
            if isinstance(field_type, dict):
                inner_type: str = field["type"]["vec"]
                counter_name: str = f"{field_name}_count"
                fields += [counter_name / construct.BytesInteger(4, swapped=True)]
                inner_loader = _known_idl_type_adapters[inner_type]
                fields += [field_name / construct.Array(_context_counter_lookup(counter_name), inner_loader())]
            else:
                fields += [field_name / _known_idl_type_adapters[field_type]()]
        layout_loaders[discriminator] = IdlType(event_name, construct.Struct(*fields))
    return layout_loaders


class IdlParser:
    def __init__(self, filepath: str):
        self.parsers: typing.Dict[bytes, IdlType] = _load_idl_parsers_from_json_file(filepath)

    def parse(self, binary_data: bytes) -> typing.Tuple[str, typing.Any]:
        discriminator: bytes = binary_data[0:8]
        idl_type: IdlType = self.parsers[discriminator]
        return idl_type.name, idl_type.struct.parse(binary_data[8:])

    def decode_and_parse(self, encoded: str) -> typing.Tuple[str, typing.Any]:
        decoded: bytes = base64.b64decode(encoded)
        return self.parse(decoded)


_loaded_idl_sets: typing.Dict[str, IdlParser] = {}


def lazy_load_cached_idl_parser(filename: str) -> IdlParser:
    if filename not in _loaded_idl_sets:
        filepath = os.path.join(DATA_PATH, filename)
        idl_parser: IdlParser = IdlParser(filepath)
        _loaded_idl_sets[filename] = idl_parser
    return _loaded_idl_sets[filename]
