# In --strict mode, mypy complains about imports unless they're done this way.
#
# It complains 'Module has no attribute ABC' or 'Module "mango" does not explicitly export
# attribute "XYZ"; implicit reexport disabled'. We could dial that back by using the
# --implicit-reexport parameter, but let's keep things strict.
#
# Each import then *must* be of the form `from .file import X as X`. (Until/unless there's
# a better way.)
#
from .account import Account as Account
from .account import AccountSlot as AccountSlot
from .account import Valuation as Valuation
from .accountflags import AccountFlags as AccountFlags
from .accountinfo import AccountInfo as AccountInfo
from .accountinfoconverter import (
    build_account_info_converter as build_account_info_converter,
)
from .accountliquidator import AccountLiquidator as AccountLiquidator
from .accountliquidator import NullAccountLiquidator as NullAccountLiquidator
from .accountscout import AccountScout as AccountScout
from .accountscout import ScoutReport as ScoutReport
from .addressableaccount import AddressableAccount as AddressableAccount
from .arguments import parse_args as parse_args
from .arguments import setup_logging as setup_logging
from .balancesheet import BalanceSheet as BalanceSheet
from .cache import Cache as Cache
from .cache import MarketCache as MarketCache
from .cache import PerpMarketCache as PerpMarketCache
from .cache import PriceCache as PriceCache
from .cache import RootBankCache as RootBankCache
from .client import BetterClient as BetterClient
from .client import ClusterUrlData as ClusterUrlData
from .client import BlockhashNotFoundException as BlockhashNotFoundException
from .client import ClientException as ClientException
from .client import CompoundException as CompoundException
from .client import CompoundRPCCaller as CompoundRPCCaller
from .client import FailedToFetchBlockhashException as FailedToFetchBlockhashException
from .client import NodeIsBehindException as NodeIsBehindException
from .client import RateLimitException as RateLimitException
from .client import RPCCaller as RPCCaller
from .client import AbstractSlotHolder as AbstractSlotHolder
from .client import CheckingSlotHolder as CheckingSlotHolder
from .client import NullSlotHolder as NullSlotHolder
from .client import StaleSlotException as StaleSlotException
from .client import (
    TooManyRequestsRateLimitException as TooManyRequestsRateLimitException,
)
from .client import (
    TooMuchBandwidthRateLimitException as TooMuchBandwidthRateLimitException,
)
from .client import (
    TransactionAlreadyProcessedException as TransactionAlreadyProcessedException,
)
from .client import TransactionException as TransactionException
from .combinableinstructions import CombinableInstructions as CombinableInstructions
from .constants import MangoConstants as MangoConstants
from .constants import DATA_PATH as DATA_PATH
from .constants import SOL_DECIMAL_DIVISOR as SOL_DECIMAL_DIVISOR
from .constants import SOL_DECIMALS as SOL_DECIMALS
from .constants import SOL_MINT_ADDRESS as SOL_MINT_ADDRESS
from .constants import SYSTEM_PROGRAM_ADDRESS as SYSTEM_PROGRAM_ADDRESS
from .constants import WARNING_DISCLAIMER_TEXT as WARNING_DISCLAIMER_TEXT
from .constants import version as version
from .context import Context as Context
from .contextbuilder import ContextBuilder as ContextBuilder
from .datetimes import datetime_from_chain as datetime_from_chain
from .datetimes import datetime_from_timestamp as datetime_from_timestamp
from .datetimes import local_now as local_now
from .datetimes import utc_now as utc_now
from .encoding import decode_binary as decode_binary
from .encoding import encode_binary as encode_binary
from .encoding import encode_key as encode_key
from .encoding import encode_int as encode_int
from .group import Group as Group
from .group import GroupSlot as GroupSlot
from .group import GroupSlotPerpMarket as GroupSlotPerpMarket
from .group import GroupSlotSpotMarket as GroupSlotSpotMarket
from .healthcheck import HealthCheck as HealthCheck
from .idl import IdlParser as IdlParser
from .idl import lazy_load_cached_idl_parser as lazy_load_cached_idl_parser
from .idsjsonmarketlookup import IdsJsonMarketLookup as IdsJsonMarketLookup
from .inventory import Inventory as Inventory
from .inventory import InventoryAccountWatcher as InventoryAccountWatcher
from .instructions import (
    build_mango_cache_perp_markets_instructions as build_mango_cache_perp_markets_instructions,
)
from .instructions import (
    build_mango_cache_prices_instructions as build_mango_cache_prices_instructions,
)
from .instructions import (
    build_mango_cache_root_banks_instructions as build_mango_cache_root_banks_instructions,
)
from .instructions import (
    build_mango_create_account_instructions as build_mango_create_account_instructions,
)
from .instructions import (
    build_mango_deposit_instructions as build_mango_deposit_instructions,
)
from .instructions import (
    build_mango_redeem_accrued_instructions as build_mango_redeem_accrued_instructions,
)
from .instructions import (
    build_mango_register_referrer_id_instructions as build_mango_register_referrer_id_instructions,
)
from .instructions import (
    build_mango_set_account_delegate_instructions as build_mango_set_account_delegate_instructions,
)
from .instructions import (
    build_mango_set_referrer_memory_instructions as build_mango_set_referrer_memory_instructions,
)
from .instructions import (
    build_mango_settle_fees_instructions as build_mango_settle_fees_instructions,
)
from .instructions import (
    build_mango_settle_pnl_instructions as build_mango_settle_pnl_instructions,
)
from .instructions import (
    build_mango_update_funding_instructions as build_mango_update_funding_instructions,
)
from .instructions import (
    build_mango_update_root_bank_instructions as build_mango_update_root_bank_instructions,
)
from .instructions import (
    build_mango_unset_account_delegate_instructions as build_mango_unset_account_delegate_instructions,
)
from .instructions import (
    build_mango_withdraw_instructions as build_mango_withdraw_instructions,
)
from .instructions import (
    build_perp_cancel_all_orders_instructions as build_perp_cancel_all_orders_instructions,
)
from .instructions import (
    build_perp_cancel_order_instructions as build_perp_cancel_order_instructions,
)
from .instructions import (
    build_perp_consume_events_instructions as build_perp_consume_events_instructions,
)
from .instructions import (
    build_perp_place_order_instructions as build_perp_place_order_instructions,
)
from .instructions import (
    build_serum_consume_events_instructions as build_serum_consume_events_instructions,
)
from .instructions import (
    build_serum_create_openorders_instructions as build_serum_create_openorders_instructions,
)
from .instructions import (
    build_serum_place_order_instructions as build_serum_place_order_instructions,
)
from .instructions import (
    build_serum_settle_instructions as build_serum_settle_instructions,
)
from .instructions import (
    build_solana_create_account_instructions as build_solana_create_account_instructions,
)
from .instructions import (
    build_spl_close_account_instructions as build_spl_close_account_instructions,
)
from .instructions import (
    build_spl_create_associated_account_instructions as build_spl_create_associated_account_instructions,
)
from .instructions import (
    build_spl_create_account_instructions as build_spl_create_account_instructions,
)
from .instructions import (
    build_spl_faucet_airdrop_instructions as build_spl_faucet_airdrop_instructions,
)
from .instructions import (
    build_spl_transfer_tokens_instructions as build_spl_transfer_tokens_instructions,
)
from .instructions import (
    build_spot_cancel_order_instructions as build_spot_cancel_order_instructions,
)
from .instructions import (
    build_spot_create_openorders_instructions as build_spot_create_openorders_instructions,
)
from .instructions import (
    build_spot_place_order_instructions as build_spot_place_order_instructions,
)
from .instructions import (
    build_spot_settle_instructions as build_spot_settle_instructions,
)
from .instructionreporter import InstructionReporter as InstructionReporter
from .instructionreporter import SerumInstructionReporter as SerumInstructionReporter
from .instructionreporter import MangoInstructionReporter as MangoInstructionReporter
from .instructionreporter import (
    CompoundInstructionReporter as CompoundInstructionReporter,
)
from .instructiontype import InstructionType as InstructionType
from .instrumentlookup import InstrumentLookup as InstrumentLookup
from .instrumentlookup import NullInstrumentLookup as NullInstrumentLookup
from .instrumentlookup import CompoundInstrumentLookup as CompoundInstrumentLookup
from .instrumentlookup import IdsJsonTokenLookup as IdsJsonTokenLookup
from .instrumentlookup import NonSPLInstrumentLookup as NonSPLInstrumentLookup
from .instrumentlookup import SPLTokenLookup as SPLTokenLookup
from .instrumentvalue import InstrumentValue as InstrumentValue
from .liquidatablereport import LiquidatableState as LiquidatableState
from .liquidatablereport import LiquidatableReport as LiquidatableReport
from .liquidationevent import LiquidationEvent as LiquidationEvent
from .liquidationprocessor import LiquidationProcessor as LiquidationProcessor
from .liquidationprocessor import LiquidationProcessorState as LiquidationProcessorState
from .loadedmarket import Event as Event
from .loadedmarket import FillEvent as FillEvent
from .loadedmarket import LoadedMarket as LoadedMarket
from .logmessages import expand_log_messages as expand_log_messages
from .lotsizeconverter import LotSizeConverter as LotSizeConverter
from .mangoinstruction import MangoInstruction as MangoInstruction
from .lotsizeconverter import NullLotSizeConverter as NullLotSizeConverter
from .markets import InventorySource as InventorySource
from .markets import MarketType as MarketType
from .markets import Market as Market
from .marketlookup import CompoundMarketLookup as CompoundMarketLookup
from .marketlookup import MarketLookup as MarketLookup
from .marketlookup import NullMarketLookup as NullMarketLookup
from .marketoperations import MarketInstructionBuilder as MarketInstructionBuilder
from .marketoperations import MarketOperations as MarketOperations
from .marketoperations import (
    NullMarketInstructionBuilder as NullMarketInstructionBuilder,
)
from .marketoperations import NullMarketOperations as NullMarketOperations
from .metadata import Metadata as Metadata
from .modelstate import EventQueue as EventQueue
from .modelstate import NullEventQueue as NullEventQueue
from .modelstate import ModelState as ModelState
from .notification import CompoundNotificationTarget as CompoundNotificationTarget
from .notification import ConsoleNotificationTarget as ConsoleNotificationTarget
from .notification import CsvFileNotificationTarget as CsvFileNotificationTarget
from .notification import DiscordNotificationTarget as DiscordNotificationTarget
from .notification import FilteringNotificationTarget as FilteringNotificationTarget
from .notification import MailjetNotificationTarget as MailjetNotificationTarget
from .notification import NotificationHandler as NotificationHandler
from .notification import NotificationTarget as NotificationTarget
from .notification import TelegramNotificationTarget as TelegramNotificationTarget
from .notification import parse_notification_target as parse_notification_target
from .observables import CaptureFirstItem as CaptureFirstItem
from .observables import CollectingObserverSubscriber as CollectingObserverSubscriber
from .observables import Disposable as Disposable
from .observables import DisposeWrapper as DisposeWrapper
from .observables import EventSource as EventSource
from .observables import FunctionObserver as FunctionObserver
from .observables import LatestItemObserverSubscriber as LatestItemObserverSubscriber
from .observables import NullObserverSubscriber as NullObserverSubscriber
from .observables import PrintingObserverSubscriber as PrintingObserverSubscriber
from .observables import (
    TimestampedPrintingObserverSubscriber as TimestampedPrintingObserverSubscriber,
)
from .observables import (
    create_backpressure_skipping_observer as create_backpressure_skipping_observer,
)
from .observables import debug_print_item as debug_print_item
from .observables import log_subscription_error as log_subscription_error
from .observables import (
    observable_pipeline_error_reporter as observable_pipeline_error_reporter,
)
from .openorders import OpenOrders as OpenOrders
from .oracle import Oracle as Oracle
from .oracle import OracleProvider as OracleProvider
from .oracle import OracleSource as OracleSource
from .oracle import Price as Price
from .oracle import SupportedOracleFeature as SupportedOracleFeature
from .orders import Order as Order
from .orders import OrderType as OrderType
from .orders import OrderBook as OrderBook
from .orders import Side as Side
from .ownedinstrumentvalue import OwnedInstrumentValue as OwnedInstrumentValue
from .oraclefactory import create_oracle_provider as create_oracle_provider
from .output import output as output
from .output import output_formatter as output_formatter
from .output import OutputFormat as OutputFormat
from .output import OutputFormatter as OutputFormatter
from .output import to_json as to_json
from .perpaccount import PerpAccount as PerpAccount
from .perpeventqueue import PerpEvent as PerpEvent
from .perpeventqueue import PerpEventQueue as PerpEventQueue
from .perpeventqueue import PerpFillEvent as PerpFillEvent
from .perpeventqueue import PerpOutEvent as PerpOutEvent
from .perpeventqueue import PerpUnknownEvent as PerpUnknownEvent
from .perpeventqueue import (
    UnseenAccountFillEventTracker as UnseenAccountFillEventTracker,
)
from .perpeventqueue import (
    UnseenPerpEventChangesTracker as UnseenPerpEventChangesTracker,
)
from .perpmarket import PerpMarket as PerpMarket
from .perpmarket import PerpMarketInstructionBuilder as PerpMarketInstructionBuilder
from .perpmarket import PerpMarketOperations as PerpMarketOperations
from .perpmarket import PerpMarketStub as PerpMarketStub
from .perpmarket import PerpOrderBookSide as PerpOrderBookSide
from .perpmarketdetails import PerpMarketDetails as PerpMarketDetails
from .perpopenorders import PerpOpenOrders as PerpOpenOrders
from .placedorder import PlacedOrder as PlacedOrder
from .placedorder import PlacedOrdersContainer as PlacedOrdersContainer
from .porcelain import instruction_builder as instruction_builder
from .porcelain import instrument as instrument
from .porcelain import instrument_value as instrument_value
from .porcelain import market as market
from .porcelain import operations as operations
from .porcelain import token as token
from .publickey import encode_public_key_for_sorting as encode_public_key_for_sorting
from .reconnectingwebsocket import ReconnectingWebsocket as ReconnectingWebsocket
from .retrier import RetryWithPauses as RetryWithPauses
from .retrier import retry_context as retry_context
from .serumeventqueue import SerumEventQueue as SerumEventQueue
from .serumeventqueue import (
    UnseenSerumEventChangesTracker as UnseenSerumEventChangesTracker,
)
from .serummarket import SerumMarket as SerumMarket
from .serummarket import SerumMarketInstructionBuilder as SerumMarketInstructionBuilder
from .serummarket import SerumMarketOperations as SerumMarketOperations
from .serummarket import SerumMarketStub as SerumMarketStub
from .serummarketlookup import SerumMarketLookup as SerumMarketLookup
from .spotmarket import SpotMarket as SpotMarket
from .spotmarket import SpotMarketInstructionBuilder as SpotMarketInstructionBuilder
from .spotmarket import SpotMarketOperations as SpotMarketOperations
from .spotmarket import SpotMarketStub as SpotMarketStub
from .text import indent_collection_as_str as indent_collection_as_str
from .text import indent_item_by as indent_item_by
from .tokens import Instrument as Instrument
from .tokens import RoundDirection as RoundDirection
from .tokens import SolToken as SolToken
from .tokens import Token as Token
from .tokenaccount import TokenAccount as TokenAccount
from .tokenbank import BankBalances as BankBalances
from .tokenbank import InterestRates as InterestRates
from .tokenbank import NodeBank as NodeBank
from .tokenbank import RootBank as RootBank
from .tokenbank import TokenBank as TokenBank
from .tokenoperations import (
    build_create_associated_instructions_and_account as build_create_associated_instructions_and_account,
)
from .tradehistory import TradeHistory as TradeHistory
from .transactionmonitoring import (
    SignatureSubscription as SignatureSubscription,
)
from .transactionmonitoring import (
    DequeTransactionStatusCollector as DequeTransactionStatusCollector,
)
from .transactionmonitoring import (
    NullTransactionStatusCollector as NullTransactionStatusCollector,
)
from .transactionmonitoring import (
    TransactionOutcome as TransactionOutcome,
)
from .transactionmonitoring import (
    TransactionStatus as TransactionStatus,
)
from .transactionmonitoring import (
    TransactionStatusCollector as TransactionStatusCollector,
)
from .transactionmonitoring import (
    WebSocketTransactionMonitor as WebSocketTransactionMonitor,
)
from .transactionscout import TransactionScout as TransactionScout
from .transactionscout import (
    fetch_all_recent_transaction_signatures as fetch_all_recent_transaction_signatures,
)
from .transactionscout import (
    mango_instruction_from_response as mango_instruction_from_response,
)
from .version import Version as Version
from .wallet import Wallet as Wallet
from .walletbalancer import FilterSmallChanges as FilterSmallChanges
from .walletbalancer import FixedTargetBalance as FixedTargetBalance
from .walletbalancer import LiveAccountBalancer as LiveAccountBalancer
from .walletbalancer import LiveWalletBalancer as LiveWalletBalancer
from .walletbalancer import NullWalletBalancer as NullWalletBalancer
from .walletbalancer import PercentageTargetBalance as PercentageTargetBalance
from .walletbalancer import TargetBalance as TargetBalance
from .walletbalancer import WalletBalancer as WalletBalancer
from .walletbalancer import (
    calculate_required_balance_changes as calculate_required_balance_changes,
)
from .walletbalancer import parse_fixed_target_balance as parse_fixed_target_balance
from .walletbalancer import parse_target_balance as parse_target_balance
from .walletbalancer import sort_changes_for_trades as sort_changes_for_trades
from .watcher import LamdaUpdateWatcher as LamdaUpdateWatcher
from .watcher import ManualUpdateWatcher as ManualUpdateWatcher
from .watcher import Watcher as Watcher
from .watchers import build_group_watcher as build_group_watcher
from .watchers import build_account_watcher as build_account_watcher
from .watchers import build_cache_watcher as build_cache_watcher
from .watchers import build_spot_open_orders_watcher as build_spot_open_orders_watcher
from .watchers import build_serum_open_orders_watcher as build_serum_open_orders_watcher
from .watchers import build_perp_open_orders_watcher as build_perp_open_orders_watcher
from .watchers import build_price_watcher as build_price_watcher
from .watchers import build_serum_inventory_watcher as build_serum_inventory_watcher
from .watchers import build_orderbook_watcher as build_orderbook_watcher
from .watchers import build_serum_event_queue_watcher as build_serum_event_queue_watcher
from .watchers import build_spot_event_queue_watcher as build_spot_event_queue_watcher
from .watchers import build_perp_event_queue_watcher as build_perp_event_queue_watcher
from .websocketsubscription import (
    IndividualWebSocketSubscriptionManager as IndividualWebSocketSubscriptionManager,
)
from .websocketsubscription import (
    SharedWebSocketSubscriptionManager as SharedWebSocketSubscriptionManager,
)
from .websocketsubscription import (
    WebSocketAccountSubscription as WebSocketAccountSubscription,
)
from .websocketsubscription import WebSocketLogSubscription as WebSocketLogSubscription
from .websocketsubscription import (
    WebSocketProgramSubscription as WebSocketProgramSubscription,
)
from .websocketsubscription import WebSocketSubscription as WebSocketSubscription
from .websocketsubscription import (
    WebSocketSubscriptionManager as WebSocketSubscriptionManager,
)

from .layouts import layouts

import decimal

# Increased precision from 18 to 36 because for a decimal like:
# val = Decimal("17436036573.2030800")
#
# The following rounding operations would both throw decimal.InvalidOperation:
# val.quantize(Decimal('.000000001'))
# round(val, 9)
decimal.getcontext().prec = 36
