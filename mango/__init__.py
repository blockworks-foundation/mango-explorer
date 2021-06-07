from .accountinfo import AccountInfo
from .accountliquidator import AccountLiquidator, NullAccountLiquidator, ActualAccountLiquidator, ForceCancelOrdersAccountLiquidator, ReportingAccountLiquidator
from .accountscout import ScoutReport, AccountScout
from .addressableaccount import AddressableAccount
from .aggregator import AggregatorConfig, Round, Answer, Aggregator
from .balancesheet import BalanceSheet
from .baskettoken import BasketToken
from .constants import SYSTEM_PROGRAM_ADDRESS, SOL_MINT_ADDRESS, SOL_DECIMALS, SOL_DECIMAL_DIVISOR, WARNING_DISCLAIMER_TEXT, MangoConstants
from .context import Context, default_cluster, default_cluster_url, default_program_id, default_dex_program_id, default_group_name, default_group_id, default_context, solana_context, serum_context, rpcpool_context
from .encoding import decode_binary, encode_binary, encode_key, encode_int
from .group import Group
from .index import Index
from .instructions import InstructionBuilder, ForceCancelOrdersInstructionBuilder, LiquidateInstructionBuilder
from .instructiontype import InstructionType
from .liquidationevent import LiquidationEvent
from .liquidationprocessor import LiquidationProcessor
from .mangoaccountflags import MangoAccountFlags
from .marginaccount import MarginAccount, MarginAccountMetadata
from .marketmetadata import MarketMetadata
from .notification import NotificationTarget, TelegramNotificationTarget, DiscordNotificationTarget, MailjetNotificationTarget, CsvFileNotificationTarget, FilteringNotificationTarget, NotificationHandler, parse_subscription_target
from .observables import PrintingObserverSubscriber, TimestampedPrintingObserverSubscriber, CollectingObserverSubscriber, CaptureFirstItem, FunctionObserver, create_backpressure_skipping_observer, debug_print_item, log_subscription_error, observable_pipeline_error_reporter, EventSource
from .openorders import OpenOrders
from .ownedtokenvalue import OwnedTokenValue
from .retrier import RetryWithPauses, retry_context
from .serumaccountflags import SerumAccountFlags
from .spotmarket import SpotMarket, SpotMarketLookup
from .token import Token, SolToken, TokenLookup
from .tokenaccount import TokenAccount
from .tokenvalue import TokenValue
from .tradeexecutor import TradeExecutor, NullTradeExecutor, SerumImmediateTradeExecutor
from .transactionscout import MangoInstruction, TransactionScout, fetch_all_recent_transaction_signatures
from .version import Version
from .wallet import Wallet, default_wallet
from .walletbalancer import TargetBalance, FixedTargetBalance, PercentageTargetBalance, TargetBalanceParser, sort_changes_for_trades, calculate_required_balance_changes, FilterSmallChanges, WalletBalancer, NullWalletBalancer, LiveWalletBalancer

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
