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
VERSION_2 = 2
VERSION = VERSION_2
MAP_TABLE_SIZE = 640
PROD_ACCT_SIZE = 512
PROD_HDR_SIZE = 48
PROD_ATTR_SIZE = PROD_ACCT_SIZE - PROD_HDR_SIZE

PYTH_DEVNET_MAPPING_ROOT = PublicKey("BmA9Z6FjioHJPpjT39QazZyhDRUdZy2ezwx4GiDdE2u2")
PYTH_MAINNET_MAPPING_ROOT = PublicKey("AHtgzX45WTKfkPG53L6WYhGEXwQkN1BVknET3sVsLL8J")


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

class StringDictionaryAdapter(construct.Adapter):
    def __init__(self):
        construct.Adapter.__init__(self, construct.RepeatUntil(lambda contents, lst, ctx: contents == "",
                                   construct.PascalString(construct.VarInt, "utf8")))

    def _decode(self, obj, context, path) -> typing.Dict[str, str]:
        result = {}
        for counter in range(int(len(obj) / 2)):
            index = counter * 2
            key = obj[index]
            value = obj[index + 1]
            result[key] = value
        return result

    def _encode(self, obj, context, path) -> str:
        # Can only encode string values.
        return str(obj)


# # 🥭 MAPPING layout
#
# This layout implements the Mapping structure. Here's the [Rust implementation](https://github.com/pyth-network/pyth-client-rs/blob/main/src/lib.rs).
#
# // Mapping account structure
# #[repr(C)]
# pub struct Mapping
# {
#   pub magic      : u32,        // pyth magic number
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
#
# // Product account structure
# #[repr(C)]
# pub struct Product
# {
#   pub magic      : u32,        // pyth magic number
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
    "attr" / StringDictionaryAdapter()
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
#
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
#
# // Price account structure V2
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
#   pub drv        : [i64;8],    // calculated values derived from agg. price
#   pub prod       : AccKey,     // product account key
#   pub next       : AccKey,     // next Price account in linked list
#   pub agg_pub    : AccKey,     // quoter who computed last aggregate price
#   pub agg        : PriceInfo,  // aggregate price info
#   pub comp       : [PriceComp;32] // price components one per quoter
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
    "drv" / construct.Array(8, construct.Int64sl),
    "prod" / PublicKeyAdapter(),
    "next" / PublicKeyAdapter(),
    "agg_pub" / PublicKeyAdapter(),
    "agg" / PRICE_INFO,
    "comp" / construct.Array(32, PRICE_COMP)
)
