from .account import AccountBasketToken, AccountBasketBaseToken, Account
from .accountflags import AccountFlags
from .accountinfo import AccountInfo
from .accountinfoconverter import build_account_info_converter
from .accountliquidator import AccountLiquidator, NullAccountLiquidator
from .accountscout import ScoutReport, AccountScout
from .addressableaccount import AddressableAccount
from .balancesheet import BalanceSheet
from .cache import PriceCache, RootBankCache, PerpMarketCache, Cache
from .client import CompatibleClient, BetterClient
from .collateralcalculator import CollateralCalculator, SerumCollateralCalculator, SpotCollateralCalculator, PerpCollateralCalculator
from .combinableinstructions import CombinableInstructions
from .constants import SYSTEM_PROGRAM_ADDRESS, SOL_MINT_ADDRESS, SOL_DECIMALS, SOL_DECIMAL_DIVISOR, WARNING_DISCLAIMER_TEXT, MangoConstants
from .context import Context
from .contextbuilder import ContextBuilder
from .createmarketinstructionbuilder import create_market_instruction_builder
from .createmarketoperations import create_market_operations
from .encoding import decode_binary, encode_binary, encode_key, encode_int
from .ensuremarketloaded import ensure_market_loaded
from .group import GroupBasketMarket, Group
from .healthcheck import HealthCheck
from .idsjsontokenlookup import IdsJsonTokenLookup
from .idsjsonmarketlookup import IdsJsonMarketLookup
from .inventory import Inventory, SpotInventoryAccountWatcher, PerpInventoryAccountWatcher
from .instructions import build_create_solana_account_instructions, build_create_spl_account_instructions, build_create_associated_spl_account_instructions, build_transfer_spl_tokens_instructions, build_close_spl_account_instructions, build_create_serum_open_orders_instructions, build_serum_place_order_instructions, build_serum_consume_events_instructions, build_serum_settle_instructions, build_spot_place_order_instructions, build_cancel_spot_order_instructions, build_cancel_perp_order_instructions, build_mango_consume_events_instructions, build_create_account_instructions, build_place_perp_order_instructions, build_deposit_instructions, build_withdraw_instructions, build_redeem_accrued_mango_instructions, build_faucet_airdrop_instructions
from .instructionreporter import InstructionReporter, SerumInstructionReporter, MangoInstructionReporter, CompoundInstructionReporter
from .instructiontype import InstructionType
from .liquidatablereport import LiquidatableState, LiquidatableReport
from .liquidationevent import LiquidationEvent
from .liquidationprocessor import LiquidationProcessor, LiquidationProcessorState
from .lotsizeconverter import LotSizeConverter, NullLotSizeConverter
from .mangoinstruction import MangoInstruction
from .market import InventorySource, Market
from .marketinstructionbuilder import MarketInstructionBuilder, NullMarketInstructionBuilder
from .marketlookup import MarketLookup, NullMarketLookup, CompoundMarketLookup
from .marketoperations import MarketOperations, DryRunMarketOperations
from .metadata import Metadata
from .notification import NotificationTarget, TelegramNotificationTarget, DiscordNotificationTarget, MailjetNotificationTarget, CsvFileNotificationTarget, FilteringNotificationTarget, NotificationHandler, parse_subscription_target
from .observables import DisposePropagator, DisposeWrapper, NullObserverSubscriber, PrintingObserverSubscriber, TimestampedPrintingObserverSubscriber, CollectingObserverSubscriber, LatestItemObserverSubscriber, CaptureFirstItem, FunctionObserver, create_backpressure_skipping_observer, debug_print_item, log_subscription_error, observable_pipeline_error_reporter, EventSource
from .openorders import OpenOrders
from .oracle import OracleSource, Price, Oracle, OracleProvider, SupportedOracleFeature
from .orderbookside import OrderBookSideType, PerpOrderBookSide
from .orders import Order, OrderType, Side
from .ownedtokenvalue import OwnedTokenValue
from .oraclefactory import create_oracle_provider
from .parse_account_info_to_orders import parse_account_info_to_orders
from .perpaccount import PerpAccount
from .perpeventqueue import PerpEvent, PerpFillEvent, PerpOutEvent, PerpUnknownEvent, PerpEventQueue, UnseenPerpEventChangesTracker
from .perpmarket import PerpMarket, PerpMarketStub
from .perpmarketdetails import PerpMarketDetails
from .perpmarketinfo import PerpMarketInfo
from .perpmarketinstructionbuilder import PerpMarketInstructionBuilder
from .perpmarketoperations import PerpMarketOperations
from .perpopenorders import PerpOpenOrders
from .placedorder import PlacedOrder, PlacedOrdersContainer
from .publickey import encode_public_key_for_sorting
from .reconnectingwebsocket import ReconnectingWebsocket
from .retrier import RetryWithPauses, retry_context
from .rootbank import NodeBank, RootBank
from .serumeventqueue import SerumEventQueue, UnseenSerumEventChangesTracker
from .serummarket import SerumMarket, SerumMarketStub
from .serummarketlookup import SerumMarketLookup
from .serummarketinstructionbuilder import SerumMarketInstructionBuilder
from .serummarketoperations import SerumMarketOperations
from .spltokenlookup import SplTokenLookup
from .spotmarket import SpotMarket, SpotMarketStub
from .spotmarketinfo import SpotMarketInfo
from .spotmarketinstructionbuilder import SpotMarketInstructionBuilder
from .spotmarketoperations import SpotMarketOperations
from .token import Token, SolToken
from .tokenaccount import TokenAccount
from .tokeninfo import TokenInfo
from .tokenlookup import TokenLookup, NullTokenLookup, CompoundTokenLookup
from .tokenvalue import TokenValue
from .tradeexecutor import TradeExecutor, NullTradeExecutor, ImmediateTradeExecutor
from .transactionscout import TransactionScout, fetch_all_recent_transaction_signatures, mango_instruction_from_response
from .version import Version
from .wallet import Wallet
from .walletbalancer import TargetBalance, FixedTargetBalance, PercentageTargetBalance, TargetBalanceParser, sort_changes_for_trades, calculate_required_balance_changes, FilterSmallChanges, WalletBalancer, NullWalletBalancer, LiveWalletBalancer
from .watcher import Watcher, ManualUpdateWatcher, LamdaUpdateWatcher
from .watchers import build_group_watcher, build_account_watcher, build_cache_watcher, build_spot_open_orders_watcher, build_serum_open_orders_watcher, build_perp_open_orders_watcher, build_price_watcher, build_serum_inventory_watcher, build_perp_orderbook_side_watcher, build_serum_orderbook_side_watcher
from .websocketsubscription import WebSocketSubscription, WebSocketProgramSubscription, WebSocketAccountSubscription, WebSocketLogSubscription, WebSocketSubscriptionManager, IndividualWebSocketSubscriptionManager, SharedWebSocketSubscriptionManager

from .layouts import layouts

import decimal
import logging
import logging.handlers
import pandas as pd

pd.options.display.float_format = '{:,.8f}'.format

# Increased precision from 18 to 36 because for a decimal like:
# val = Decimal("17436036573.2030800")
#
# The following rounding operations would both throw decimal.InvalidOperation:
# val.quantize(Decimal('.000000001'))
# round(val, 9)
decimal.getcontext().prec = 36

_log_levels = {
    logging.CRITICAL: "🛑",
    logging.ERROR: "🚨",
    logging.WARNING: "⚠",
    logging.INFO: "ⓘ",
    logging.DEBUG: "🐛"
}

default_log_record_factory = logging.getLogRecordFactory()


def emojified_record_factory(*args, **kwargs):
    record = default_log_record_factory(*args, **kwargs)
    # Here's where we add our own format keywords.
    record.level_emoji = _log_levels[record.levelno]
    return record


logging.setLogRecordFactory(emojified_record_factory)

# Make logging a little more verbose than the default.
logging.basicConfig(level=logging.INFO,
                    datefmt="%Y-%m-%d %H:%M:%S",
                    format="%(asctime)s %(level_emoji)s %(name)-12.12s %(message)s")

# Stop libraries outputting lots of information unless it's a warning or worse.
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("solanaweb3").setLevel(logging.WARNING)
