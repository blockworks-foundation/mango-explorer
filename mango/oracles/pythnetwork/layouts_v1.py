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

import construct
import typing

from solana.publickey import PublicKey

from ...layouts.layouts import DecimalAdapter, PublicKeyAdapter


# # 🥭 Pyth
#
# This file contains code specific to the [Pyth Network](https://pyth.network/).
#

# # 🥭 Constants
#
# Pyth defines some constants.
#

MAGIC = 0xa1b2c3d4
VERSION_1 = 1
VERSION = VERSION_1
MAP_TABLE_SIZE = 640
PROD_ACCT_SIZE = 512
PROD_HDR_SIZE = 48
PROD_ATTR_SIZE = PROD_ACCT_SIZE - PROD_HDR_SIZE

PYTH_MAPPING_ROOT = PublicKey("ArppEFcsybCLE8CRtQJLQ9tLv2peGmQoKWFuiUWm4KBP")

# # 🥭 ACCOUNT_TYPE enum
#
# This layout implements the AccountType enum. Here's the [Rust implementation](https://github.com/pyth-network/pyth-client-rs/blob/main/src/lib.rs).
#
# // each account has its own type
# #[repr(C)]
# pub enum AccountType
# {
#   Unknown,
#   Mapping,
#   Product,
#   Price
# }

ACCOUNT_TYPE = construct.Enum(construct.Int32ul, Unknown=0, Mapping=1, Product=2, Price=3)


# # 🥭 PythStringDictionaryAdapter
#
# Loads string key-value pairs into a dictionary. The strings are 'Pascal' strings, which
# specify the string length as an int followed by that number of UTF-8 characters.
#
# Note that this depends on there being a 'size' property in the already-parsed struct
# data. That makes it a good bit less general-purpose.
#

class PythStringDictionaryAdapter(construct.Adapter):
    _size_offset = 48  # Magic number from https://github.com/pyth-network/pyth-client-js/blob/main/src/index.ts

    def __init__(self):
        construct.Adapter.__init__(self, construct.Array(PROD_ATTR_SIZE, construct.Byte))

    def _decode(self, data, context, path) -> typing.Dict[str, str]:
        idx = 0
        size = context.size - PythStringDictionaryAdapter._size_offset
        result = {}
        while idx < size:
            key_length = data[idx]
            idx += 1
            if key_length > 0:
                key = bytes(data[idx:idx + key_length]).decode("utf-8")
                idx += key_length
                value_length = data[idx]
                idx += 1
                value = bytes(data[idx: idx + value_length]).decode("utf-8")
                idx += value_length
                result[key] = value

        return result

    def _encode(self, obj, context, path) -> str:
        # Can only encode str values.
        return str(obj)


# # 🥭 MAPPING layout
#
# This layout implements the Mapping structure. Here's the [Rust implementation](https://github.com/pyth-network/pyth-client-rs/blob/main/src/lib.rs).
#
# // Mapping account structure
# #[repr(C)]
# pub struct Mapping
# {
#   pub magic      : u32,        // pyth _magic number
#   pub ver        : u32,        // program version
#   pub atype      : u32,        // account type
#   pub size       : u32,        // account used size
#   pub num        : u32,        // number of product accounts
#   pub unused     : u32,
#   pub next       : AccKey,     // next mapping account (if any)
#   pub products   : [AccKey;MAP_TABLE_SIZE]
# }

MAPPING = construct.Struct(
    "magic" / DecimalAdapter(4),
    "ver" / DecimalAdapter(4),
    "atype" / ACCOUNT_TYPE,
    "size" / DecimalAdapter(4),
    "num" / DecimalAdapter(4),
    "unused" / DecimalAdapter(4),
    "next" / PublicKeyAdapter(),
    "products" / construct.Array(MAP_TABLE_SIZE, PublicKeyAdapter())
)

# # 🥭 PRODUCT layout
#
# This layout implements the Product structure. Here's the [Rust implementation](https://github.com/pyth-network/pyth-client-rs/blob/main/src/lib.rs).
#
# // Product account structure
# #[repr(C)]
# pub struct Product
# {
#   pub _magic      : u32,        // pyth _magic number
#   pub ver        : u32,        // program version
#   pub atype      : u32,        // account type
#   pub size       : u32,        // price account size
#   pub px_acc     : AccKey,     // first price account in list
#   pub attr       : [u8;PROD_ATTR_SIZE] // key/value pairs of reference attr.
# }

PRODUCT = construct.Struct(
    "magic" / DecimalAdapter(4),
    "ver" / DecimalAdapter(4),
    "atype" / ACCOUNT_TYPE,
    "size" / DecimalAdapter(4),
    "px_acc" / PublicKeyAdapter(),
    "attr" / PythStringDictionaryAdapter()
)


# # 🥭 PRICE_INFO layout
#
# This layout implements the PriceInfo structure. Here's the [Rust implementation](https://github.com/pyth-network/pyth-client-rs/blob/main/src/lib.rs).
#
# // contributing or aggregate price component
# #[repr(C)]
# pub struct PriceInfo
# {
#   pub price      : i64,        // product price
#   pub conf       : u64,        // confidence interval of product price
#   pub status     : PriceStatus,// status of price (Trading is valid)
#   pub corp_act   : CorpAction, // notification of any corporate action
#   pub pub_slot   : u64
# }

PRICE_INFO = construct.Struct(
    "price" / DecimalAdapter(),
    "conf" / DecimalAdapter(),
    "status" / construct.Enum(construct.Int32ul, Unknown=0, Trading=1, Halted=2, Auction=3),
    "corp_act" / construct.Enum(construct.Int32ul, NoCorpAct=0),
    "pub_slot" / DecimalAdapter()
)


# # 🥭 PRICE_COMP layout
#
# This layout implements the PriceComp structure. Here's the [Rust implementation](https://github.com/pyth-network/pyth-client-rs/blob/main/src/lib.rs).

# // latest component price and price used in aggregate snapshot
# #[repr(C)]
# pub struct PriceComp
# {
#   publisher  : AccKey,         // key of contributing quoter
#   agg        : PriceInfo,      // contributing price to last aggregate
#   latest     : PriceInfo       // latest contributing price (not in agg.)
# }

PRICE_COMP = construct.Struct(
    "publisher" / PublicKeyAdapter(),
    "agg" / PRICE_INFO,
    "latest" / PRICE_INFO
)


# # 🥭 PRICE layout
#
# This layout implements the Price structure. Here's the [Rust implementation](https://github.com/pyth-network/pyth-client-rs/blob/main/src/lib.rs).

# // Price account structure
# #[repr(C)]
# pub struct Price
# {
#   pub magic      : u32,        // pyth magic number
#   pub ver        : u32,        // program version
#   pub atype      : u32,        // account type
#   pub size       : u32,        // price account size
#   pub ptype      : PriceType,  // price or calculation type
#   pub expo       : i32,        // price exponent
#   pub num        : u32,        // number of component prices
#   pub unused     : u32,
#   pub curr_slot  : u64,        // currently accumulating price slot
#   pub valid_slot : u64,        // valid slot-time of agg. price
#   pub prod       : AccKey,     // product account key
#   pub next       : AccKey,     // next Price account in linked list
#   pub agg_pub    : AccKey,     // quoter who computed last aggregate price
#   pub agg        : PriceInfo,  // aggregate price info
#   pub comp       : [PriceComp;16] // price components one per quoter
# }

PRICE = construct.Struct(
    "magic" / DecimalAdapter(4),
    "ver" / DecimalAdapter(4),
    "atype" / ACCOUNT_TYPE,
    "size" / DecimalAdapter(4),
    "ptype" / construct.Enum(construct.Int32ul, Unknown=0, Price=1),
    "expo" / construct.Int32sl,
    "num" / DecimalAdapter(4),
    "unused" / DecimalAdapter(4),
    "curr_slot" / DecimalAdapter(),
    "valid_slot" / DecimalAdapter(),
    "prod" / PublicKeyAdapter(),
    "next" / PublicKeyAdapter(),
    "agg_pub" / PublicKeyAdapter(),
    "agg" / PRICE_INFO,
    "comp" / construct.Array(16, PRICE_COMP)
)
