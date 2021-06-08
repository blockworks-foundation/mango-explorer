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

# # 🥭 Layouts
#
# This file contains structure layouts to load the sometimes-opaque data blobs from Solana
# accounts.
#
# The idea is to have one data-encapsulating class (in [BaseModel](BaseModel.ipynb)) for
# each type, as well as one or more LAYOUT structures. So for example `Group` loads `GROUP`
# but in future will also be able to load `GROUP_V2`.
#
# The general approach is:
# * Define one (or more) layouts to read in the data blob
# * Use the data from the data blob to construct a more useful strongly-typed object
#
# So for example `GROUP` is defined below but it's a low-level dependency. In general, code
# should depend and work with the `Group` class, not the `GROUP` structure.


import construct
import datetime
import itertools
import typing

from decimal import Decimal
from solana.publickey import PublicKey


# # Adapters
#
# These are adapters for the construct package to simplify our struct declarations.

# ## DecimalAdapter class
#
# A simple construct `Adapter` that lets us use `Decimal`s directly in our structs.


class DecimalAdapter(construct.Adapter):
    def __init__(self, size: int = 8):
        construct.Adapter.__init__(self, construct.BytesInteger(size, swapped=True))

    def _decode(self, obj, context, path) -> Decimal:
        return Decimal(obj)

    def _encode(self, obj, context, path) -> int:
        # Can only encode int values.
        return int(obj)


# ## FloatAdapter class
#
# Some numbers are packaged as 16-bytes to represent a `float`. The way to get the `float`
# is to take the 16-byte int value and divide it by 2 to the power 64. In Javascript this
# would be:
# ```
# return intValue / Math.pow(2, 64);
# ```
# From [Daffy on Discord](https://discordapp.com/channels/791995070613159966/820390560085835786/841327936383614987):
# > It's a u128 underneath. Interpreted as a binary fixed point number where teh fixed point is right at the middle
#
# > Just interpret as u128 then divide by 2 ^ 64. Also make sure there are enough units of precision available
#
# > If you look at our mango-client-ts we just use the javascript number which is a float64 and that has caused some issues for us because of rounding issues.
#
# This is a simple construct `Adapter` that lets us use these float values directly in our
# structs. We do as Daffy says, but we can handle arbitrary sizes, not just u128. (The
# constructor takes a size - in bytes, like the rest of our code - and calculates the
# divisor so the mid-point of the whole sequence of bits is the fixed point.)


class FloatAdapter(construct.Adapter):
    def __init__(self, size: int = 16):
        self.size = size
        construct.Adapter.__init__(self, construct.BytesInteger(size, swapped=True))

        # Our size is in bytes but we want to work with bits here.
        bit_size = self.size * 8

        # For our string of bits, our 'fixed point' is right in the middle.
        fixed_point = bit_size / 2

        # So our divisor is 2 to the power of the fixed point
        self.divisor = Decimal(2 ** fixed_point)

    def _decode(self, obj, context, path) -> Decimal:
        return Decimal(obj) / self.divisor

    def _encode(self, obj, context, path) -> bytes:
        return bytes(obj)


# ## PublicKeyAdapter
#
# A simple construct `Adapter` that lets us use `PublicKey`s directly in our structs.


class PublicKeyAdapter(construct.Adapter):
    def __init__(self):
        construct.Adapter.__init__(self, construct.Bytes(32))

    def _decode(self, obj, context, path) -> typing.Optional[PublicKey]:
        if (obj is None) or (obj == bytes([0] * 32)):
            return None
        return PublicKey(obj)

    def _encode(self, obj, context, path) -> bytes:
        return bytes(obj)


# ## DatetimeAdapter
#
# A simple construct `Adapter` that lets us load `datetime`s directly in our structs.


class DatetimeAdapter(construct.Adapter):
    def __init__(self):
        construct.Adapter.__init__(self, construct.BytesInteger(8, swapped=True))

    def _decode(self, obj, context, path) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(obj)

    def _encode(self, obj, context, path) -> bytes:
        return bytes(obj)


# # Layout Structs

# ## SERUM_ACCOUNT_FLAGS
#
# The SERUM_ prefix is because there's also `MANGO_ACCOUNT_FLAGS`.
#
# Here's the [Serum Rust structure](https://github.com/project-serum/serum-dex/blob/master/dex/src/state.rs):
# ```
# #[derive(Copy, Clone, BitFlags, Debug, Eq, PartialEq)]
# #[repr(u64)]
# pub enum AccountFlag {
#     Initialized = 1u64 << 0,
#     Market = 1u64 << 1,
#     OpenOrders = 1u64 << 2,
#     RequestQueue = 1u64 << 3,
#     EventQueue = 1u64 << 4,
#     Bids = 1u64 << 5,
#     Asks = 1u64 << 6,
#     Disabled = 1u64 << 7,
# }
# ```


SERUM_ACCOUNT_FLAGS = construct.BitsSwapped(
    construct.BitStruct(
        "initialized" / construct.Flag,
        "market" / construct.Flag,
        "open_orders" / construct.Flag,
        "request_queue" / construct.Flag,
        "event_queue" / construct.Flag,
        "bids" / construct.Flag,
        "asks" / construct.Flag,
        "disabled" / construct.Flag,
        construct.Padding(7 * 8)
    )
)


# ## MANGO_ACCOUNT_FLAGS
#
# The MANGO_ prefix is because there's also `SERUM_ACCOUNT_FLAGS`.
#
# The MANGO_ACCOUNT_FLAGS should be exactly 8 bytes.
#
# Here's the [Mango Rust structure](https://github.com/blockworks-foundation/mango/blob/master/program/src/state.rs):
# ```
# #[derive(Copy, Clone, BitFlags, Debug, Eq, PartialEq)]
# #[repr(u64)]
# pub enum AccountFlag {
#     Initialized = 1u64 << 0,
#     MangoGroup = 1u64 << 1,
#     MarginAccount = 1u64 << 2,
#     MangoSrmAccount = 1u64 << 3
# }
# ```


MANGO_ACCOUNT_FLAGS = construct.BitsSwapped(
    construct.BitStruct(
        "initialized" / construct.Flag,
        "group" / construct.Flag,
        "margin_account" / construct.Flag,
        "srm_account" / construct.Flag,
        construct.Padding(4 + (7 * 8))
    )
)


# ## INDEX
#
# Here's the [Mango Rust structure](https://github.com/blockworks-foundation/mango/blob/master/program/src/state.rs):
# ```
# #[derive(Copy, Clone)]
# #[repr(C)]
# pub struct MangoIndex {
#     pub last_update: u64,
#     pub borrow: U64F64,
#     pub deposit: U64F64
# }
# ```


INDEX = construct.Struct(
    "last_update" / DatetimeAdapter(),
    "borrow" / FloatAdapter(),
    "deposit" / FloatAdapter()
)


# ## AGGREGATOR_CONFIG
#
# Here's the [Flux Rust structure](https://github.com/blockworks-foundation/solana-flux-aggregator/blob/master/program/src/state.rs):
# ```
# #[derive(Clone, Debug, BorshSerialize, BorshDeserialize, BorshSchema, Default, PartialEq)]
# pub struct AggregatorConfig {
#     /// description
#     pub description: [u8; 32],
#
#     /// decimals for this feed
#     pub decimals: u8,
#
#     /// oracle cannot start a new round until after `restart_relay` rounds
#     pub restart_delay: u8,
#
#     /// max number of submissions in a round
#     pub max_submissions: u8,
#
#     /// min number of submissions in a round to resolve an answer
#     pub min_submissions: u8,
#
#     /// amount of tokens oracles are reward per submission
#     pub reward_amount: u64,
#
#     /// SPL token account from which to withdraw rewards
#     pub reward_token_account: PublicKey,
# }
# ```


AGGREGATOR_CONFIG = construct.Struct(
    "description" / construct.PaddedString(32, "utf8"),
    "decimals" / DecimalAdapter(1),
    "restart_delay" / DecimalAdapter(1),
    "max_submissions" / DecimalAdapter(1),
    "min_submissions" / DecimalAdapter(1),
    "reward_amount" / DecimalAdapter(),
    "reward_token_account" / PublicKeyAdapter()
)


# ## ROUND
#
# Here's the [Flux Rust structure](https://github.com/blockworks-foundation/solana-flux-aggregator/blob/master/program/src/state.rs):
# ```
# #[derive(Clone, Debug, BorshSerialize, BorshDeserialize, BorshSchema, Default, PartialEq)]
# pub struct Round {
#     pub id: u64,
#     pub created_at: u64,
#     pub updated_at: u64,
# }
# ```


ROUND = construct.Struct(
    "id" / DecimalAdapter(),
    "created_at" / DecimalAdapter(),
    "updated_at" / DecimalAdapter()
)


# ## ANSWER
#
# Here's the [Flux Rust structure](https://github.com/blockworks-foundation/solana-flux-aggregator/blob/master/program/src/state.rs):
# ```
# #[derive(Clone, Debug, BorshSerialize, BorshDeserialize, BorshSchema, Default, PartialEq)]
# pub struct Answer {
#     pub round_id: u64,
#     pub median: u64,
#     pub created_at: u64,
#     pub updated_at: u64,
# }
# ```


ANSWER = construct.Struct(
    "round_id" / DecimalAdapter(),
    "median" / DecimalAdapter(),
    "created_at" / DatetimeAdapter(),
    "updated_at" / DatetimeAdapter()
)


# ## AGGREGATOR
#
# Here's the [Flux Rust structure](https://github.com/blockworks-foundation/solana-flux-aggregator/blob/master/program/src/state.rs):
# ```
# #[derive(Clone, Debug, BorshSerialize, BorshDeserialize, BorshSchema, Default, PartialEq)]
# pub struct Aggregator {
#     pub config: AggregatorConfig,
#     /// is initialized
#     pub is_initialized: bool,
#     /// authority
#     pub owner: PublicKey,
#     /// current round accepting oracle submissions
#     pub round: Round,
#     pub round_submissions: PublicKey, // has_one: Submissions
#     /// the latest answer resolved
#     pub answer: Answer,
#     pub answer_submissions: PublicKey, // has_one: Submissions
# }
# ```


AGGREGATOR = construct.Struct(
    "config" / AGGREGATOR_CONFIG,
    "initialized" / DecimalAdapter(1),
    "owner" / PublicKeyAdapter(),
    "round" / ROUND,
    "round_submissions" / PublicKeyAdapter(),
    "answer" / ANSWER,
    "answer_submissions" / PublicKeyAdapter()
)


# ## GROUP_V1
#
# Groups have a common quote currency, and it's always the last token in the tokens.
#
# That means the number of markets is number_of_tokens - 1.
#
# Here's the [Mango Rust structure](https://github.com/blockworks-foundation/mango/blob/master/program/src/state.rs):
# ```
# #[derive(Copy, Clone)]
# #[repr(C)]
# pub struct MangoGroup {
#     pub account_flags: u64,
#     pub tokens: [Pubkey; NUM_TOKENS],  // Last token is shared quote currency
#     pub vaults: [Pubkey; NUM_TOKENS],  // where funds are stored
#     pub indexes: [MangoIndex; NUM_TOKENS],  // to keep track of interest
#     pub spot_markets: [Pubkey; NUM_MARKETS],  // pubkeys to MarketState of serum dex
#     pub oracles: [Pubkey; NUM_MARKETS],  // oracles that give price of each base currency in quote currency
#     pub signer_nonce: u64,
#     pub signer_key: Pubkey,
#     pub dex_program_id: Pubkey,  // serum dex program id
#
#     // denominated in Mango index adjusted terms
#     pub total_deposits: [U64F64; NUM_TOKENS],
#     pub total_borrows: [U64F64; NUM_TOKENS],
#
#     pub maint_coll_ratio: U64F64,  // 1.10
#     pub init_coll_ratio: U64F64,  //  1.20
#
#     pub srm_vault: Pubkey,  // holds users SRM for fee reduction
#
#     /// This admin key is only for alpha release and the only power it has is to amend borrow limits
#     /// If users borrow too much too quickly before liquidators are able to handle the volume,
#     /// lender funds will be at risk. Hence these borrow limits will be raised slowly
#     pub admin: Pubkey,
#     pub borrow_limits: [u64; NUM_TOKENS],
#
#     pub mint_decimals: [u8; NUM_TOKENS],
#     pub oracle_decimals: [u8; NUM_MARKETS],
#     pub padding: [u8; MANGO_GROUP_PADDING]
# }
# impl_loadable!(MangoGroup);
# ```


GROUP_V1_NUM_TOKENS = 3
GROUP_V1_NUM_MARKETS = GROUP_V1_NUM_TOKENS - 1
GROUP_V1_PADDING = 8 - (GROUP_V1_NUM_TOKENS + GROUP_V1_NUM_MARKETS) % 8
GROUP_V1 = construct.Struct(
    "account_flags" / MANGO_ACCOUNT_FLAGS,
    "tokens" / construct.Array(GROUP_V1_NUM_TOKENS, PublicKeyAdapter()),
    "vaults" / construct.Array(GROUP_V1_NUM_TOKENS, PublicKeyAdapter()),
    "indexes" / construct.Array(GROUP_V1_NUM_TOKENS, INDEX),
    "spot_markets" / construct.Array(GROUP_V1_NUM_MARKETS, PublicKeyAdapter()),
    "oracles" / construct.Array(GROUP_V1_NUM_MARKETS, PublicKeyAdapter()),
    "signer_nonce" / DecimalAdapter(),
    "signer_key" / PublicKeyAdapter(),
    "dex_program_id" / PublicKeyAdapter(),
    "total_deposits" / construct.Array(GROUP_V1_NUM_TOKENS, FloatAdapter()),
    "total_borrows" / construct.Array(GROUP_V1_NUM_TOKENS, FloatAdapter()),
    "maint_coll_ratio" / FloatAdapter(),
    "init_coll_ratio" / FloatAdapter(),
    "srm_vault" / PublicKeyAdapter(),
    "admin" / PublicKeyAdapter(),
    "borrow_limits" / construct.Array(GROUP_V1_NUM_TOKENS, DecimalAdapter()),
    "mint_decimals" / construct.Array(GROUP_V1_NUM_TOKENS, DecimalAdapter(1)),
    "oracle_decimals" / construct.Array(GROUP_V1_NUM_MARKETS, DecimalAdapter(1)),
    "padding" / construct.Array(GROUP_V1_PADDING, construct.Padding(1))
)


# ## GROUP_V2
#
# Groups have a common quote currency, and it's always the last token in the tokens.
#
# That means the number of markets is number_of_tokens - 1.
#
# There is no difference between the V1 and V2 structures except for the number of tokens.
# We handle things this way to be consistent with how we handle V1 and V2 `MarginAccount`s.
#
# Here's the [Mango Rust structure](https://github.com/blockworks-foundation/mango/blob/master/program/src/state.rs):
# ```
# #[derive(Copy, Clone)]
# #[repr(C)]
# pub struct MangoGroup {
#     pub account_flags: u64,
#     pub tokens: [Pubkey; NUM_TOKENS],  // Last token is shared quote currency
#     pub vaults: [Pubkey; NUM_TOKENS],  // where funds are stored
#     pub indexes: [MangoIndex; NUM_TOKENS],  // to keep track of interest
#     pub spot_markets: [Pubkey; NUM_MARKETS],  // pubkeys to MarketState of serum dex
#     pub oracles: [Pubkey; NUM_MARKETS],  // oracles that give price of each base currency in quote currency
#     pub signer_nonce: u64,
#     pub signer_key: Pubkey,
#     pub dex_program_id: Pubkey,  // serum dex program id
#
#     // denominated in Mango index adjusted terms
#     pub total_deposits: [U64F64; NUM_TOKENS],
#     pub total_borrows: [U64F64; NUM_TOKENS],
#
#     pub maint_coll_ratio: U64F64,  // 1.10
#     pub init_coll_ratio: U64F64,  //  1.20
#
#     pub srm_vault: Pubkey,  // holds users SRM for fee reduction
#
#     /// This admin key is only for alpha release and the only power it has is to amend borrow limits
#     /// If users borrow too much too quickly before liquidators are able to handle the volume,
#     /// lender funds will be at risk. Hence these borrow limits will be raised slowly
#     /// UPDATE: 4/15/2021 - this admin key is now useless, borrow limits are removed
#     pub admin: Pubkey,
#     pub borrow_limits: [u64; NUM_TOKENS],
#
#     pub mint_decimals: [u8; NUM_TOKENS],
#     pub oracle_decimals: [u8; NUM_MARKETS],
#     pub padding: [u8; MANGO_GROUP_PADDING]
# }
#
# ```


GROUP_V2_NUM_TOKENS = 5
GROUP_V2_NUM_MARKETS = GROUP_V2_NUM_TOKENS - 1
GROUP_V2_PADDING = 8 - (GROUP_V2_NUM_TOKENS + GROUP_V2_NUM_MARKETS) % 8
GROUP_V2 = construct.Struct(
    "account_flags" / MANGO_ACCOUNT_FLAGS,
    "tokens" / construct.Array(GROUP_V2_NUM_TOKENS, PublicKeyAdapter()),
    "vaults" / construct.Array(GROUP_V2_NUM_TOKENS, PublicKeyAdapter()),
    "indexes" / construct.Array(GROUP_V2_NUM_TOKENS, INDEX),
    "spot_markets" / construct.Array(GROUP_V2_NUM_MARKETS, PublicKeyAdapter()),
    "oracles" / construct.Array(GROUP_V2_NUM_MARKETS, PublicKeyAdapter()),
    "signer_nonce" / DecimalAdapter(),
    "signer_key" / PublicKeyAdapter(),
    "dex_program_id" / PublicKeyAdapter(),
    "total_deposits" / construct.Array(GROUP_V2_NUM_TOKENS, FloatAdapter()),
    "total_borrows" / construct.Array(GROUP_V2_NUM_TOKENS, FloatAdapter()),
    "maint_coll_ratio" / FloatAdapter(),
    "init_coll_ratio" / FloatAdapter(),
    "srm_vault" / PublicKeyAdapter(),
    "admin" / PublicKeyAdapter(),
    "borrow_limits" / construct.Array(GROUP_V2_NUM_TOKENS, DecimalAdapter()),
    "mint_decimals" / construct.Array(GROUP_V2_NUM_TOKENS, DecimalAdapter(1)),
    "oracle_decimals" / construct.Array(GROUP_V2_NUM_MARKETS, DecimalAdapter(1)),
    "padding" / construct.Array(GROUP_V2_PADDING, construct.Padding(1))
)


# ## TOKEN_ACCOUNT


TOKEN_ACCOUNT = construct.Struct(
    "mint" / PublicKeyAdapter(),
    "owner" / PublicKeyAdapter(),
    "amount" / DecimalAdapter(),
    "padding" / construct.Padding(93)
)


# ## OPEN_ORDERS
#
# Trying to use the `OPEN_ORDERS_LAYOUT` and `OpenOrdersAccount` from `pyserum` just
# proved too probelmatic. (`OpenOrdersAccount` doesn't expose `referrer_rebate_accrued`,
# for instance.)


OPEN_ORDERS = construct.Struct(
    construct.Padding(5),
    "account_flags" / SERUM_ACCOUNT_FLAGS,
    "market" / PublicKeyAdapter(),
    "owner" / PublicKeyAdapter(),
    "base_token_free" / DecimalAdapter(),
    "base_token_total" / DecimalAdapter(),
    "quote_token_free" / DecimalAdapter(),
    "quote_token_total" / DecimalAdapter(),
    "free_slot_bits" / DecimalAdapter(16),
    "is_bid_bits" / DecimalAdapter(16),
    "orders" / construct.Array(128, DecimalAdapter(16)),
    "client_ids" / construct.Array(128, DecimalAdapter()),
    "referrer_rebate_accrued" / DecimalAdapter(),
    "padding" / construct.Padding(7)
)


# ## MARGIN_ACCOUNT_V1
#
# Here's the V1 [Mango Rust structure](https://github.com/blockworks-foundation/mango/blob/master/program/src/state.rs):
# ```
# #[derive(Copy, Clone)]
# #[repr(C)]
# pub struct MarginAccount {
#     pub account_flags: u64,
#     pub mango_group: Pubkey,
#     pub owner: Pubkey,  // solana pubkey of owner
#
#     // assets and borrows are denominated in Mango adjusted terms
#     pub deposits: [U64F64; NUM_TOKENS],  // assets being lent out and gaining interest, including collateral
#
#     // this will be incremented every time an order is opened and decremented when order is closed
#     pub borrows: [U64F64; NUM_TOKENS],  // multiply by current index to get actual value
#
#     pub open_orders: [Pubkey; NUM_MARKETS],  // owned by Mango
#
#     pub being_liquidated: bool,
#     pub padding: [u8; 7] // padding to make compatible with previous MarginAccount size
#     // TODO add has_borrows field for easy memcmp fetching
# }
# ```


MARGIN_ACCOUNT_V1_NUM_TOKENS = 3
MARGIN_ACCOUNT_V1_NUM_MARKETS = MARGIN_ACCOUNT_V1_NUM_TOKENS - 1
MARGIN_ACCOUNT_V1 = construct.Struct(
    "account_flags" / MANGO_ACCOUNT_FLAGS,
    "mango_group" / PublicKeyAdapter(),
    "owner" / PublicKeyAdapter(),
    "deposits" / construct.Array(MARGIN_ACCOUNT_V1_NUM_TOKENS, FloatAdapter()),
    "borrows" / construct.Array(MARGIN_ACCOUNT_V1_NUM_TOKENS, FloatAdapter()),
    "open_orders" / construct.Array(MARGIN_ACCOUNT_V1_NUM_MARKETS, PublicKeyAdapter()),
    "being_liquidated" / DecimalAdapter(1),
    "padding" / construct.Padding(7)
)


# ## MARGIN_ACCOUNT_V2
#
# Here's the V2 [Mango Rust structure](https://github.com/blockworks-foundation/mango/blob/master/program/src/state.rs):
# ```
# #[derive(Copy, Clone)]
# #[repr(C)]
# pub struct MarginAccount {
#     pub account_flags: u64,
#     pub mango_group: Pubkey,
#     pub owner: Pubkey,  // solana pubkey of owner
#
#     // assets and borrows are denominated in Mango adjusted terms
#     pub deposits: [U64F64; NUM_TOKENS],  // assets being lent out and gaining interest, including collateral
#
#     // this will be incremented every time an order is opened and decremented when order is closed
#     pub borrows: [U64F64; NUM_TOKENS],  // multiply by current index to get actual value
#
#     pub open_orders: [Pubkey; NUM_MARKETS],  // owned by Mango
#
#     pub being_liquidated: bool,
#     pub has_borrows: bool, // does the account have any open borrows? set by checked_add_borrow and checked_sub_borrow
#     pub padding: [u8; 64] // padding
# }
# ```


MARGIN_ACCOUNT_V2_NUM_TOKENS = 5
MARGIN_ACCOUNT_V2_NUM_MARKETS = MARGIN_ACCOUNT_V2_NUM_TOKENS - 1
MARGIN_ACCOUNT_V2 = construct.Struct(
    "account_flags" / MANGO_ACCOUNT_FLAGS,
    "mango_group" / PublicKeyAdapter(),
    "owner" / PublicKeyAdapter(),
    "deposits" / construct.Array(MARGIN_ACCOUNT_V2_NUM_TOKENS, FloatAdapter()),
    "borrows" / construct.Array(MARGIN_ACCOUNT_V2_NUM_TOKENS, FloatAdapter()),
    "open_orders" / construct.Array(MARGIN_ACCOUNT_V2_NUM_MARKETS, PublicKeyAdapter()),
    "being_liquidated" / DecimalAdapter(1),
    "has_borrows" / DecimalAdapter(1),
    "padding" / construct.Padding(70)
)


# ## build_margin_account_parser_for_num_tokens() function
#
# This function builds a `construct.Struct` that can load a `MarginAccount` with a
# specific number of tokens. The number of markets and size of padding are derived
# from the number of tokens.


def build_margin_account_parser_for_num_tokens(num_tokens: int) -> construct.Struct:
    num_markets = num_tokens - 1

    return construct.Struct(
        "account_flags" / MANGO_ACCOUNT_FLAGS,
        "mango_group" / PublicKeyAdapter(),
        "owner" / PublicKeyAdapter(),
        "deposits" / construct.Array(num_tokens, FloatAdapter()),
        "borrows" / construct.Array(num_tokens, FloatAdapter()),
        "open_orders" / construct.Array(num_markets, PublicKeyAdapter()),
        "padding" / construct.Padding(8)
    )


# ## build_margin_account_parser_for_length() function
#
# This function takes a data length (presumably the size of the structure returned from
# the `AccountInfo`) and returns a `MarginAccount` structure that can parse it.
#
# If the size doesn't _exactly_ match the size of the `Struct`, and Exception is raised.


def build_margin_account_parser_for_length(length: int) -> construct.Struct:
    tried_sizes: typing.List[int] = []
    for num_tokens in itertools.count(start=2):
        parser = build_margin_account_parser_for_num_tokens(num_tokens)
        if parser.sizeof() == length:
            return parser

        tried_sizes += [parser.sizeof()]
        if parser.sizeof() > length:
            raise Exception(
                f"Could not create MarginAccount parser for length ({length}) - tried sizes ({tried_sizes})")


# # Instruction Structs

# ## MANGO_INSTRUCTION_VARIANT_FINDER
#
# The 'variant' of the instruction is held in the first 4 bytes. The remainder of the data
# is per-instruction.
#
# This `struct` loads only the first 4 bytes, as an `int`, so we know which specific parser
# has to be used to load the rest of the data.


MANGO_INSTRUCTION_VARIANT_FINDER = construct.Struct(
    "variant" / construct.BytesInteger(4, swapped=True)
)


# ## Variant 0: INIT_MANGO_GROUP
#
# Instruction variant 1. From the [Rust source](https://github.com/blockworks-foundation/mango/blob/master/program/src/instruction.rs):
#
# > Initialize a group of lending pools that can be cross margined
# ```
# InitMangoGroup {
#     signer_nonce: u64,
#     maint_coll_ratio: U64F64,
#     init_coll_ratio: U64F64,
#     borrow_limits: [u64; NUM_TOKENS]
# },
# ```


INIT_MANGO_GROUP = construct.Struct(
    "variant" / construct.Const(0x0, construct.BytesInteger(4, swapped=True)),
    "signer_nonce" / DecimalAdapter(),
    "maint_coll_ratio" / FloatAdapter(),
    "init_coll_ratio" / FloatAdapter(),
    #  "borrow_limits" / construct.Array(NUM_TOKENS, DecimalAdapter())  # This is inconsistently available
)


# ## Variant 1: INIT_MARGIN_ACCOUNT
#
# Instruction variant 1. From the [Rust source](https://github.com/blockworks-foundation/mango/blob/master/program/src/instruction.rs):
#
# > Initialize a margin account for a user
# ```
# InitMarginAccount,
# ```


INIT_MARGIN_ACCOUNT = construct.Struct(
    "variant" / construct.Const(0x1, construct.BytesInteger(4, swapped=True)),
)


# ## Variant 2: DEPOSIT
#
# Instruction variant 2. From the [Rust source](https://github.com/blockworks-foundation/mango/blob/master/program/src/instruction.rs):
#
# > Deposit funds into margin account to be used as collateral and earn interest.
# ```
# Deposit {
#     quantity: u64
# },
# ```


DEPOSIT = construct.Struct(
    "variant" / construct.Const(0x2, construct.BytesInteger(4, swapped=True)),
    "quantity" / DecimalAdapter()
)


# ## Variant 3: WITHDRAW
#
# Instruction variant 3. From the [Rust source](https://github.com/blockworks-foundation/mango/blob/master/program/src/instruction.rs):
#
# > Withdraw funds that were deposited earlier.
# ```
# Withdraw {
#     quantity: u64
# },
# ```


WITHDRAW = construct.Struct(
    "variant" / construct.Const(0x3, construct.BytesInteger(4, swapped=True)),
    "quantity" / DecimalAdapter()
)


# ## Variant 4: BORROW
#
# Instruction variant 4. From the [Rust source](https://github.com/blockworks-foundation/mango/blob/master/program/src/instruction.rs):
#
# > Borrow by incrementing MarginAccount.borrows given collateral ratio is below init_coll_rat
# ```
# Borrow {
#     token_index: usize,
#     quantity: u64
# },
# ```


BORROW = construct.Struct(
    "variant" / construct.Const(0x4, construct.BytesInteger(4, swapped=True)),
    "token_index" / DecimalAdapter(),
    "quantity" / DecimalAdapter()
)


# ## Variant 5: SETTLE_BORROW
#
# Instruction variant 5. From the [Rust source](https://github.com/blockworks-foundation/mango/blob/master/program/src/instruction.rs):
#
# > Use this token's position and deposit to reduce borrows
# ```
# SettleBorrow {
#     token_index: usize,
#     quantity: u64
# },
# ```


SETTLE_BORROW = construct.Struct(
    "variant" / construct.Const(0x5, construct.BytesInteger(4, swapped=True)),
    "token_index" / DecimalAdapter(),
    "quantity" / DecimalAdapter()
)


# ## Variant 6: LIQUIDATE
#
# Instruction variant 6. From the [Rust source](https://github.com/blockworks-foundation/mango/blob/master/program/src/instruction.rs):
#
# > Take over a MarginAccount that is below init_coll_ratio by depositing funds
# ```
# Liquidate {
#     /// Quantity of each token liquidator is depositing in order to bring account above maint
#     deposit_quantities: [u64; NUM_TOKENS]
# },
# ```


_LIQUIDATE_NUM_TOKENS = 3  # Liquidate is deprecated and was only used with 3 tokens.
LIQUIDATE = construct.Struct(
    "variant" / construct.Const(0x6, construct.BytesInteger(4, swapped=True)),
    "deposit_quantities" / construct.Array(_LIQUIDATE_NUM_TOKENS, DecimalAdapter())
)


# ## Variant 7: DEPOSIT_SRM
#
# Instruction variant 7. From the [Rust source](https://github.com/blockworks-foundation/mango/blob/master/program/src/instruction.rs):
#
# > Deposit SRM into the SRM vault for MangoGroup
# >
# > These SRM are not at risk and are not counted towards collateral or any margin calculations
# >
# > Depositing SRM is a strictly altruistic act with no upside and no downside
# ```
# DepositSrm {
#     quantity: u64
# },
# ```


DEPOSIT_SRM = construct.Struct(
    "variant" / construct.Const(0x7, construct.BytesInteger(4, swapped=True)),
    "quantity" / DecimalAdapter()
)


# ## Variant 8: WITHDRAW_SRM
#
# Instruction variant 8. From the [Rust source](https://github.com/blockworks-foundation/mango/blob/master/program/src/instruction.rs):
#
# > Withdraw SRM owed to this MarginAccount
# ```
# WithdrawSrm {
#     quantity: u64
# },
# ```


WITHDRAW_SRM = construct.Struct(
    "variant" / construct.Const(0x8, construct.BytesInteger(4, swapped=True)),
    "quantity" / DecimalAdapter()
)


# ## Variant 9: PLACE_ORDER
#
# Instruction variant 9. From the [Rust source](https://github.com/blockworks-foundation/mango/blob/master/program/src/instruction.rs):
#
# > Place an order on the Serum Dex using Mango margin facilities
# ```
# PlaceOrder {
#     order: serum_dex::instruction::NewOrderInstructionV3
# },
# ```


PLACE_ORDER = construct.Struct(
    "variant" / construct.Const(0x9, construct.BytesInteger(4, swapped=True)),
    "order" / construct.Padding(1)  # Actual type is: serum_dex::instruction::NewOrderInstructionV3
)


# ## Variant 10: SETTLE_FUNDS
#
# Instruction variant 10. From the [Rust source](https://github.com/blockworks-foundation/mango/blob/master/program/src/instruction.rs):
#
# > Settle all funds from serum dex open orders into MarginAccount positions
# ```
# SettleFunds,
# ```


SETTLE_FUNDS = construct.Struct(
    "variant" / construct.Const(0xa, construct.BytesInteger(4, swapped=True)),
)


# ## Variant 11: CANCEL_ORDER
#
# Instruction variant 11. From the [Rust source](https://github.com/blockworks-foundation/mango/blob/master/program/src/instruction.rs):
#
# > Cancel an order using dex instruction
# ```
# CancelOrder {
#     order: serum_dex::instruction::CancelOrderInstructionV2
# },
# ```


CANCEL_ORDER = construct.Struct(
    "variant" / construct.Const(0xb, construct.BytesInteger(4, swapped=True)),
    "order" / construct.Padding(1)  # Actual type is: serum_dex::instruction::CancelOrderInstructionV2
)


# ## Variant 12: CANCEL_ORDER_BY_CLIENT_ID
#
# Instruction variant 12. From the [Rust source](https://github.com/blockworks-foundation/mango/blob/master/program/src/instruction.rs):
#
# > Cancel an order using client_id
# ```
# CancelOrderByClientId {
#     client_id: u64
# },
# ```


CANCEL_ORDER_BY_CLIENT_ID = construct.Struct(
    "variant" / construct.Const(0xc, construct.BytesInteger(4, swapped=True)),
    "client_id" / DecimalAdapter()
)


# ## Variant 13: CHANGE_BORROW_LIMIT
#
# Instruction variant 13. From the [Rust source](https://github.com/blockworks-foundation/mango/blob/master/program/src/instruction.rs).
#
# > Change the borrow limit using admin key. This will not affect any open positions on any MarginAccount
# >
# > This is intended to be an instruction only in alpha stage while liquidity is slowly improved"_
# ```
# ChangeBorrowLimit {
#     token_index: usize,
#     borrow_limit: u64
# },
# ```


CHANGE_BORROW_LIMIT = construct.Struct(
    "variant" / construct.Const(0xd, construct.BytesInteger(4, swapped=True)),
    "token_index" / DecimalAdapter(),
    "borrow_limit" / DecimalAdapter()
)


# ## Variant 14: PLACE_AND_SETTLE
#
# Instruction variant 14. From the [Rust source](https://github.com/blockworks-foundation/mango/blob/master/program/src/instruction.rs).
#
# > Place an order on the Serum Dex and settle funds from the open orders account
# ```
# PlaceAndSettle {
#     order: serum_dex::instruction::NewOrderInstructionV3
# },
# ```


PLACE_AND_SETTLE = construct.Struct(
    "variant" / construct.Const(0xe, construct.BytesInteger(4, swapped=True)),
    "order" / construct.Padding(1)  # Actual type is: serum_dex::instruction::NewOrderInstructionV3
)


# ## Variant 15: FORCE_CANCEL_ORDERS
#
# Instruction variant 15. From the [Rust source](https://github.com/blockworks-foundation/mango/blob/master/program/src/instruction.rs):
#
# > Allow a liquidator to cancel open orders and settle to recoup funds for partial liquidation
#
# ```
# ForceCancelOrders {
#     /// Max orders to cancel -- could be useful to lower this if running into compute limits
#     /// Recommended: 5
#     limit: u8
# },
# ```


FORCE_CANCEL_ORDERS = construct.Struct(
    "variant" / construct.Const(0xf, construct.BytesInteger(4, swapped=True)),
    "limit" / DecimalAdapter(1)
)


# ## Variant 16: PARTIAL_LIQUIDATE
#
# Instruction variant 16. From the [Rust source](https://github.com/blockworks-foundation/mango/blob/master/program/src/instruction.rs):
#
# > Take over a MarginAccount that is below init_coll_ratio by depositing funds
#
# ```
# PartialLiquidate {
#     /// Quantity of the token being deposited to repay borrows
#     max_deposit: u64
# },
# ```


PARTIAL_LIQUIDATE = construct.Struct(
    "variant" / construct.Const(0x10, construct.BytesInteger(4, swapped=True)),
    "max_deposit" / DecimalAdapter()
)


# ## InstructionParsersByVariant dictionary
#
# This dictionary provides an easy way for us to access the specific parser for a given variant.


InstructionParsersByVariant = {
    0: INIT_MANGO_GROUP,
    1: INIT_MARGIN_ACCOUNT,
    2: DEPOSIT,
    3: WITHDRAW,
    4: BORROW,
    5: SETTLE_BORROW,
    6: LIQUIDATE,
    7: DEPOSIT_SRM,
    8: WITHDRAW_SRM,
    9: PLACE_ORDER,
    10: SETTLE_FUNDS,
    11: CANCEL_ORDER,
    12: CANCEL_ORDER_BY_CLIENT_ID,
    13: CHANGE_BORROW_LIMIT,
    14: PLACE_AND_SETTLE,
    15: FORCE_CANCEL_ORDERS,
    16: PARTIAL_LIQUIDATE
}
