from .account import Account
from .accountflags import AccountFlags
from .accountinfo import AccountInfo
from .accountliquidator import AccountLiquidator, NullAccountLiquidator
from .accountscout import ScoutReport, AccountScout
from .addressableaccount import AddressableAccount
from .balancesheet import BalanceSheet
from .combinableinstructions import CombinableInstructions
from .constants import SYSTEM_PROGRAM_ADDRESS, SOL_MINT_ADDRESS, SOL_DECIMALS, SOL_DECIMAL_DIVISOR, WARNING_DISCLAIMER_TEXT, MangoConstants
from .context import Context, default_cluster, default_cluster_url, default_program_id, default_dex_program_id, default_group_name, default_group_id
from .createmarketoperations import create_market_operations
from .encoding import decode_binary, encode_binary, encode_key, encode_int
from .group import Group
from .idsjsontokenlookup import IdsJsonTokenLookup
from .idsjsonmarketlookup import IdsJsonMarketLookup
from .instructions import build_create_solana_account_instructions, build_create_spl_account_instructions, build_transfer_spl_tokens_instructions, build_close_spl_account_instructions, build_create_serum_open_orders_instructions, build_serum_place_order_instructions, build_serum_consume_events_instructions, build_serum_settle_instructions, build_spot_place_order_instructions, build_cancel_spot_order_instructions, build_cancel_perp_order_instructions, build_mango_consume_events_instructions, build_create_account_instructions, build_place_perp_order_instructions, build_withdraw_instructions
from .instructiontype import InstructionType
from .liquidatablereport import LiquidatableState, LiquidatableReport
from .liquidationevent import LiquidationEvent
from .liquidationprocessor import LiquidationProcessor, LiquidationProcessorState
from .market import AddressableMarket, InventorySource, Market
from .marketinstructionbuilder import MarketInstructionBuilder, NullMarketInstructionBuilder
from .marketlookup import MarketLookup, CompoundMarketLookup
from .marketoperations import MarketOperations, NullMarketOperations
from .metadata import Metadata
from .notification import NotificationTarget, TelegramNotificationTarget, DiscordNotificationTarget, MailjetNotificationTarget, CsvFileNotificationTarget, FilteringNotificationTarget, NotificationHandler, parse_subscription_target
from .observables import DisposePropagator, NullObserverSubscriber, PrintingObserverSubscriber, TimestampedPrintingObserverSubscriber, CollectingObserverSubscriber, LatestItemObserverSubscriber, CaptureFirstItem, FunctionObserver, create_backpressure_skipping_observer, debug_print_item, log_subscription_error, observable_pipeline_error_reporter, EventSource, FileToucherObserver
from .openorders import OpenOrders
from .orderbookside import OrderBookSide
from .orders import Order, OrderType, Side
from .ownedtokenvalue import OwnedTokenValue
from .oracle import OracleSource, Price, Oracle, OracleProvider
from .oraclefactory import create_oracle_provider
from .perpmarket import PerpMarket
from .perpmarketinfo import PerpMarketInfo
from .perpmarketinstructionbuilder import PerpMarketInstructionBuilder
from .perpmarketoperations import PerpMarketOperations
from .perpsmarket import PerpsMarket
from .reconnectingwebsocket import ReconnectingWebsocket
from .retrier import RetryWithPauses, retry_context
from .rootbank import NodeBank, RootBank
from .serummarket import SerumMarket
from .serummarketlookup import SerumMarketLookup
from .serummarketinstructionbuilder import SerumMarketInstructionBuilder
from .serummarketoperations import SerumMarketOperations
from .spltokenlookup import SplTokenLookup
from .spotmarket import SpotMarket
from .spotmarketinfo import SpotMarketInfo
from .spotmarketinstructionbuilder import SpotMarketInstructionBuilder
from .token import Token, SolToken
from .tokenaccount import TokenAccount
from .tokeninfo import TokenInfo
from .tokenlookup import TokenLookup, CompoundTokenLookup
from .tokenvalue import TokenValue
from .tradeexecutor import TradeExecutor, NullTradeExecutor, SerumImmediateTradeExecutor
from .transactionscout import MangoInstruction, TransactionScout, fetch_all_recent_transaction_signatures
from .version import Version
from .wallet import Wallet
from .walletbalancer import TargetBalance, FixedTargetBalance, PercentageTargetBalance, TargetBalanceParser, sort_changes_for_trades, calculate_required_balance_changes, FilterSmallChanges, WalletBalancer, NullWalletBalancer, LiveWalletBalancer
from .websocketsubscription import WebSocketSubscription, WebSocketSubscriptionManager

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
