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

import logging
import numpy
import pandas
import os
import os.path
import requests
import time
import typing

from datetime import datetime, timedelta
from dateutil import parser
from decimal import Decimal
from solana.publickey import PublicKey

from .account import Account
from .context import Context


# # 🥭 TradeHistory class
#
# Downloads and unifies trade history data.
#
class TradeHistory:
    COLUMNS = ["Timestamp", "Market", "Side", "MakerOrTaker", "Change", "Price", "Quantity", "Fee",
               "SequenceNumber", "FeeTier", "MarketType", "OrderId"]

    __perp_column_name_mapper = {
        "loadTimestamp": "Timestamp",
        "seqNum": "SequenceNumber",
        "price": "Price",
        "quantity": "Quantity"
    }

    __spot_column_name_mapper = {
        "loadTimestamp": "Timestamp",
        "seqNum": "SequenceNumber",
        "price": "Price",
        "size": "Quantity",
        "side": "Side",
        "feeCost": "Fee",
        "feeTier": "FeeTier",
        "orderId": "OrderId"
    }

    __decimal_spot_columns = [
        "openOrderSlot",
        "feeTier",
        "nativeQuantityReleased",
        "nativeQuantityPaid",
        "nativeFeeOrRebate",
        "orderId",
        "clientOrderId",
        "source",
        "seqNum",
        "baseTokenDecimals",
        "quoteTokenDecimals",
        "price",
        "feeCost",
        "size"
    ]

    __decimal_perp_columns = [
        "seqNum",
        "makerFee",
        "takerFee",
        "makerOrderId",
        "takerOrderId",
        "price",
        "quantity"
    ]

    __column_converters = {
        "Timestamp": lambda value: parser.parse(value),
        "SequenceNumber": lambda value: Decimal(value),
        "Price": lambda value: Decimal(value),
        "Change": lambda value: Decimal(value),
        "Quantity": lambda value: Decimal(value),
        "Fee": lambda value: Decimal(value),
        "FeeTier": lambda value: Decimal(value),
        "OrderId": lambda value: Decimal(value)
    }

    def __init__(self, seconds_pause_between_rest_calls: int = 1) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.__seconds_pause_between_rest_calls: int = seconds_pause_between_rest_calls
        self.__trades: pandas.DataFrame = pandas.DataFrame(columns=TradeHistory.COLUMNS)

    @staticmethod
    def __market_lookup(context: Context) -> typing.Callable[[pandas.Series], str]:
        def __safe_lookup(row: pandas.Series) -> str:
            address: PublicKey = PublicKey(row["address"])
            market = context.market_lookup.find_by_address(address)
            if market is None:
                raise Exception(f"No market found with address {address}")
            return market.symbol
        return __safe_lookup

    @staticmethod
    def __download_json(url: str) -> typing.Any:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def __download_all_perps(context: Context, account: Account) -> pandas.DataFrame:
        url = f"https://event-history-api.herokuapp.com/perp_trades/{account.address}?page=all"
        data = TradeHistory.__download_json(url)
        trades: pandas.DataFrame = TradeHistory.__perp_data_to_dataframe(context, account, data)

        return trades

    @staticmethod
    def __download_updated_perps(context: Context, account: Account, newer_than: typing.Optional[datetime], seconds_pause_between_rest_calls: int) -> pandas.DataFrame:
        trades: pandas.DataFrame = pandas.DataFrame(columns=TradeHistory.COLUMNS)
        page: int = 0
        complete: bool = False
        while not complete:
            page += 1
            url = f"https://event-history-api.herokuapp.com/perp_trades/{account.address}?page={page}"
            data = TradeHistory.__download_json(url)
            frame: pandas.DataFrame = TradeHistory.__perp_data_to_dataframe(context, account, data)
            if len(frame) == 0:
                complete = True
            else:
                trades = trades.append(frame)
                if (newer_than is not None) and (frame.loc[frame.index[-1], "Timestamp"] < newer_than):
                    complete = True
                else:
                    time.sleep(seconds_pause_between_rest_calls)

        return trades

    @staticmethod
    def __perp_data_to_dataframe(context: Context, account: Account, data: typing.Any) -> pandas.DataFrame:
        # Perp data is an array of JSON packages like:
        # {
        #     "loadTimestamp": "2021-09-02T10:54:56.000Z",
        #     "address": <PUBLIC-KEY-STRING>,
        #     "seqNum": "2831",
        #     "makerFee": "0",
        #     "takerFee": "0.0004999999999988347",
        #     "takerSide": "sell",
        #     "maker": <PUBLIC-KEY-STRING>,
        #     "makerOrderId": <BIG-INT>,
        #     "taker": <PUBLIC-KEY-STRING>,
        #     "takerOrderId": <BIG-INT>,
        #     "price": "50131.9",
        #     "quantity": "0.019"
        # },
        def __side_lookup(row: pandas.Series) -> str:
            if row["MakerOrTaker"] == "taker":
                return str(row["takerSide"])
            elif row["takerSide"] == "buy":
                return "sell"
            else:
                return "buy"

        def __fee_calculator(row: pandas.Series) -> Decimal:
            price: Decimal = row["Price"]
            quantity: Decimal = row["Quantity"]
            fee_rate: Decimal
            if row["MakerOrTaker"] == "maker":
                fee_rate = row["makerFee"]
            else:
                fee_rate = row["takerFee"]
            return price * quantity * -fee_rate

        if len(data["data"]) <= 1:
            return pandas.DataFrame(columns=TradeHistory.COLUMNS)

        trade_data = data["data"][:-1]
        for trade in trade_data:
            for column_name in TradeHistory.__decimal_perp_columns:
                trade[column_name] = Decimal(trade[column_name])

        frame = pandas.DataFrame(trade_data).rename(mapper=TradeHistory.__perp_column_name_mapper, axis=1, copy=True)
        frame["Timestamp"] = frame["Timestamp"].apply(lambda timestamp: parser.parse(timestamp).replace(microsecond=0))
        frame["Market"] = frame.apply(TradeHistory.__market_lookup(context), axis=1)
        frame["MarketType"] = "perp"

        this_address = f"{account.address}"
        frame["MakerOrTaker"] = frame["maker"].apply(lambda addy: "maker" if addy == this_address else "taker")

        frame["FeeTier"] = -1
        frame["Fee"] = frame.apply(__fee_calculator, axis=1)
        frame["Side"] = frame.apply(__side_lookup, axis=1)
        frame["Value"] = frame["Price"] * frame["Quantity"]
        frame["Change"] = frame["Value"].where(frame["Side"] == "sell", other=-frame["Value"]) + frame["Fee"]
        frame["OrderId"] = numpy.where(frame["MakerOrTaker"] == "maker",
                                       frame["makerOrderId"], frame["takerOrderId"])

        return frame[TradeHistory.COLUMNS]

    @staticmethod
    def __download_all_spots(context: Context, account: Account) -> pandas.DataFrame:
        trades: pandas.DataFrame = pandas.DataFrame(columns=TradeHistory.COLUMNS)
        for spot_open_orders_address in account.spot_open_orders:
            url = f"https://event-history-api.herokuapp.com/trades/open_orders/{spot_open_orders_address}?page=all"
            data = TradeHistory.__download_json(url)
            frame = TradeHistory.__spot_data_to_dataframe(context, account, data)
            trades = trades.append(frame)

        return trades

    @staticmethod
    def __download_updated_spots(context: Context, account: Account, newer_than: typing.Optional[datetime], seconds_pause_between_rest_calls: int) -> pandas.DataFrame:
        trades: pandas.DataFrame = pandas.DataFrame(columns=TradeHistory.COLUMNS)
        for spot_open_orders_address in account.spot_open_orders:
            page: int = 0
            complete: bool = False
            while not complete:
                page += 1
                url = f"https://event-history-api.herokuapp.com/trades/open_orders/{spot_open_orders_address}?page={page}"
                data = TradeHistory.__download_json(url)
                frame = TradeHistory.__spot_data_to_dataframe(context, account, data)

                if len(frame) == 0:
                    complete = True
                else:
                    trades = trades.append(frame)
                    earliest_in_frame = frame.loc[frame.index[-1], "Timestamp"]
                    if (newer_than is not None) and (earliest_in_frame < newer_than):
                        complete = True
                    else:
                        time.sleep(seconds_pause_between_rest_calls)

        return trades

    @staticmethod
    def __spot_data_to_dataframe(context: Context, account: Account, data: typing.Any) -> pandas.DataFrame:
        # Spot data is an array of JSON packages like:
        # {
        #     "loadTimestamp": "2021-10-05T16:04:50.717Z",
        #     "address": <PUBLIC-KEY-STRING>,
        #     "programId": <PUBLIC-KEY-STRING>,
        #     "baseCurrency": "SOL",
        #     "quoteCurrency": "USDC",
        #     "fill": true,
        #     "out": false,
        #     "bid": true,
        #     "maker": true,
        #     "openOrderSlot": "0",
        #     "feeTier": "4",
        #     "nativeQuantityReleased": "3000000000",
        #     "nativeQuantityPaid": "487482712",
        #     "nativeFeeOrRebate": "146288",
        #     "orderId": <BIG-INT>,
        #     "openOrders": <PUBLIC-KEY-STRING>,
        #     "clientOrderId": <BIG-INT>,
        #     "uuid": <LONG-OPAQUE-UUID-STRING>,
        #     "source": "2",
        #     "seqNum": "24827175",
        #     "baseTokenDecimals": 9,
        #     "quoteTokenDecimals": 6,
        #     "side": "buy",
        #     "price": 162.543,
        #     "feeCost": -0.146288,
        #     "size": 3
        # }
        if len(data["data"]) == 0:
            return pandas.DataFrame(columns=TradeHistory.COLUMNS)
        else:
            trade_data = data["data"]
            for trade in trade_data:
                for column_name in TradeHistory.__decimal_spot_columns:
                    trade[column_name] = Decimal(trade[column_name])

            frame = pandas.DataFrame(trade_data).rename(
                mapper=TradeHistory.__spot_column_name_mapper, axis=1, copy=True)
            frame["Timestamp"] = frame["Timestamp"].apply(
                lambda timestamp: parser.parse(timestamp).replace(microsecond=0))
            frame["Market"] = frame.apply(TradeHistory.__market_lookup(context), axis=1)
            frame["MakerOrTaker"] = numpy.where(frame["maker"], "maker", "taker")
            frame["Fee"] = -frame["Fee"]
            frame["Value"] = frame["Price"] * frame["Quantity"]
            frame["Change"] = frame["Value"].where(frame["Side"] == "sell", other=-frame["Value"]) + frame["Fee"]
            frame["MarketType"] = "spot"

            return frame[TradeHistory.COLUMNS]

    @property
    def trades(self) -> pandas.DataFrame:
        return self.__trades.copy(deep=True)

    def download_latest(self, context: Context, account: Account, cutoff: datetime) -> None:
        # Go back further than we need to so we can be sure we're not skipping any trades due to race conditions.
        # We remove duplicates a few lines further down.
        self._logger.info(f"Downloading spot trades from {cutoff}")
        spot: pandas.DataFrame = TradeHistory.__download_updated_spots(context,
                                                                       account,
                                                                       cutoff,
                                                                       self.__seconds_pause_between_rest_calls)
        self._logger.info(f"Downloading perp trades from {cutoff}")
        perp: pandas.DataFrame = TradeHistory.__download_updated_perps(context,
                                                                       account,
                                                                       cutoff,
                                                                       self.__seconds_pause_between_rest_calls)

        all_trades: pandas.DataFrame = pandas.concat([self.__trades, spot, perp])
        all_trades = all_trades[all_trades["Timestamp"] >= cutoff]

        distinct_trades = all_trades.drop_duplicates()
        sorted_trades = distinct_trades.sort_values(["Timestamp", "Market", "SequenceNumber"], axis=0, ascending=True)
        self._logger.info(f"Download complete. Data contains {len(sorted_trades)} trades.")
        self.__trades = sorted_trades

    def update(self, context: Context, account: Account) -> None:
        latest_trade: typing.Optional[datetime] = self.__trades.loc[self.__trades.index[-1],
                                                                    "Timestamp"] if len(self.__trades) > 0 else None
        spot: pandas.DataFrame
        perp: pandas.DataFrame
        if latest_trade is None:
            self._logger.info("Downloading all spot trades.")
            spot = TradeHistory.__download_all_spots(context, account)
            self._logger.info("Downloading all perp trades.")
            perp = TradeHistory.__download_all_perps(context, account)
        else:
            # Go back further than we need to so we can be sure we're not skipping any trades due to race conditions.
            # We remove duplicates a few lines further down.
            cutoff_safety_margin: timedelta = timedelta(hours=1)
            cutoff: datetime = latest_trade - cutoff_safety_margin
            self._logger.info(
                f"Downloading spot trades from {cutoff}, {cutoff_safety_margin} before latest stored trade at {latest_trade}")
            spot = TradeHistory.__download_updated_spots(context, account,
                                                         cutoff, self.__seconds_pause_between_rest_calls)
            self._logger.info(
                f"Downloading perp trades from {cutoff}, {cutoff_safety_margin} before latest stored trade at {latest_trade}")
            perp = TradeHistory.__download_updated_perps(context, account,
                                                         cutoff, self.__seconds_pause_between_rest_calls)

        all_trades = pandas.concat([self.__trades, spot, perp])
        distinct_trades = all_trades.drop_duplicates()
        sorted_trades = distinct_trades.sort_values(["Timestamp", "Market", "SequenceNumber"], axis=0, ascending=True)
        self._logger.info(f"Download complete. Data contains {len(sorted_trades)} trades.")
        self.__trades = sorted_trades

    def load(self, filename: str, ok_if_missing: bool = False) -> None:
        if not os.path.isfile(filename):
            if not ok_if_missing:
                raise Exception(f"File {filename} does not exist or is not a file.")
        else:
            existing = pandas.read_csv(filename,
                                       float_precision="round_trip",
                                       converters=TradeHistory.__column_converters)

            self.__trades = self.__trades.append(existing)

    def save(self, filename: str) -> None:
        self.__trades.to_csv(filename, index=False, mode="w")

    def __str__(self) -> str:
        return f"« TradeHistory containing {len(self.__trades)} trades »"

    def __repr__(self) -> str:
        return f"{self}"
