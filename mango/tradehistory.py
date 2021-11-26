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

from datetime import datetime
from solana.publickey import PublicKey

from .account import Account
from .context import Context


# # 🥭 TradeHistory class
#
# Downloads and unifies trade history data.
#
class TradeHistory:
    COLUMNS = ["Timestamp", "Market", "Side", "MakerOrTaker", "Value", "Price", "Quantity", "Fee",
               "SequenceNumber", "FeeTier", "MarketType", "OrderId"]

    __perp_column_mapper = {
        "loadTimestamp": "Timestamp",
        "seqNum": "SequenceNumber",
        "price": "Price",
        "quantity": "Quantity"
    }

    __spot_column_mapper = {
        "loadTimestamp": "Timestamp",
        "seqNum": "SequenceNumber",
        "price": "Price",
        "size": "Quantity",
        "side": "Side",
        "feeCost": "Fee",
        "feeTier": "FeeTier",
        "orderId": "OrderId"
    }

    __dtype_mapper = {
        "SequenceNumber": "Int64",
        "Fee": "float64",
        "Price": "float64",
        "Quantity": "float64",
        "Value": "float64"
    }

    def __init__(self, context: Context, account: Account, filename: str, seconds_pause_between_rest_calls: int = 10) -> None:
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.__context: Context = context
        self.__account: Account = account
        self.__filename: str = filename
        self.__seconds_pause_between_rest_calls: int = seconds_pause_between_rest_calls
        self.__trades: pandas.DataFrame = pandas.DataFrame(columns=TradeHistory.COLUMNS)
        if os.path.isfile(filename):
            existing = pandas.read_csv(self.__filename,
                                       parse_dates=["Timestamp"],
                                       dtype=TradeHistory.__dtype_mapper,
                                       float_precision="round_trip")

            self.__trades = self.__trades.append(existing)

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
    def __set_dtypes(data: pandas.DataFrame) -> None:
        data["Timestamp"] = pandas.to_datetime(data["Timestamp"])
        data["Value"] = pandas.to_numeric(data["Value"])
        data["Price"] = pandas.to_numeric(data["Price"])
        data["Quantity"] = pandas.to_numeric(data["Quantity"])
        data["Fee"] = pandas.to_numeric(data["Fee"])
        data["SequenceNumber"] = pandas.to_numeric(data["SequenceNumber"])
        data["FeeTier"] = pandas.to_numeric(data["FeeTier"])

    @staticmethod
    def __download_json(url: str) -> typing.Any:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def __download_all_perps(context: Context, account: Account, newer_than: typing.Optional[datetime], seconds_pause_between_rest_calls: int) -> pandas.DataFrame:
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
        this_address = f"{account.address}"

        def __side_lookup(row: pandas.Series) -> str:
            if row["MakerOrTaker"] == "taker":
                return str(row["takerSide"])
            elif row["takerSide"] == "buy":
                return "sell"
            else:
                return "buy"

        trades: pandas.DataFrame = pandas.DataFrame(columns=TradeHistory.COLUMNS)
        page: int = 0
        complete: bool = False
        while not complete:
            page += 1
            url = f"https://event-history-api.herokuapp.com/perp_trades/{account.address}?page={page}"
            data = TradeHistory.__download_json(url)

            if len(data["data"]) <= 1:
                complete = True
            else:
                raw_data = pandas.DataFrame(data["data"][:-1])
                raw_data["Market"] = raw_data.apply(TradeHistory.__market_lookup(context), axis=1)

                data = raw_data.rename(mapper=TradeHistory.__perp_column_mapper, axis=1, copy=True)
                data["MarketType"] = "perp"
                data["MakerOrTaker"] = data["maker"].apply(lambda addy: "maker" if addy == this_address else "taker")

                data["Fee"] = pandas.to_numeric(numpy.where(data["MakerOrTaker"] == "maker",
                                                data["makerFee"], data["takerFee"]))
                data["FeeTier"] = -1
                data["Price"] = data["Price"].astype("float64")
                data["Quantity"] = data["Quantity"].astype("float64")
                data["Value"] = (data["Price"] * data["Quantity"]) - data["Fee"]
                data["Side"] = data.apply(__side_lookup, axis=1)
                data["OrderId"] = numpy.where(data["MakerOrTaker"] == "maker",
                                              data["makerOrderId"], data["takerOrderId"])
                TradeHistory.__set_dtypes(data)
                trades = trades.append(data[TradeHistory.COLUMNS])

                if (newer_than is not None) and (data.loc[data.index[-1], "Timestamp"] < newer_than):
                    complete = True
                else:
                    time.sleep(seconds_pause_between_rest_calls)

        return trades

    @staticmethod
    def __download_all_spots(context: Context, account: Account, newer_than: typing.Optional[datetime], seconds_pause_between_rest_calls: int) -> pandas.DataFrame:
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
        trades: pandas.DataFrame = pandas.DataFrame(columns=TradeHistory.COLUMNS)
        for spot_open_orders_address in account.spot_open_orders:
            page: int = 0
            complete: bool = False
            while not complete:
                page += 1
                url = f"https://event-history-api.herokuapp.com/trades/open_orders/{spot_open_orders_address}?page={page}"
                data = TradeHistory.__download_json(url)

                if len(data["data"]) <= 1:
                    complete = True
                else:
                    raw_data = pandas.DataFrame(data["data"])
                    raw_data["Market"] = raw_data.apply(TradeHistory.__market_lookup(context), axis=1)

                    data = raw_data.rename(mapper=TradeHistory.__spot_column_mapper, axis=1, copy=True)
                    data["MakerOrTaker"] = numpy.where(data["maker"], "maker", "taker")
                    data["Price"] = data["Price"].astype("float64")
                    data["Quantity"] = data["Quantity"].astype("float64")
                    data["Value"] = (data["Price"] * data["Quantity"]) - data["Fee"]
                    data["MarketType"] = "spot"
                    TradeHistory.__set_dtypes(data)

                    trades = trades.append(data[TradeHistory.COLUMNS])

                    if (newer_than is not None) and (data.loc[data.index[-1], "Timestamp"] < newer_than):
                        complete = True
                    else:
                        time.sleep(seconds_pause_between_rest_calls)

        return trades

    @property
    def trades(self) -> pandas.DataFrame:
        return self.__trades.copy(deep=True)

    def update(self) -> None:
        latest_trade: typing.Optional[datetime] = self.__trades.loc[self.__trades.index[-1],
                                                                    "Timestamp"] if len(self.__trades) > 0 else None
        self.logger.info(f"Downloading spot trades up to cutoff: {latest_trade}")
        spot = TradeHistory.__download_all_spots(self.__context, self.__account,
                                                 latest_trade, self.__seconds_pause_between_rest_calls)
        self.logger.info(f"Downloading perp trades up to cutoff: {latest_trade}")
        perp = TradeHistory.__download_all_perps(self.__context, self.__account,
                                                 latest_trade, self.__seconds_pause_between_rest_calls)
        all_trades = pandas.concat([self.__trades, spot, perp])
        distinct_trades = all_trades.drop_duplicates()
        sorted_trades = distinct_trades.sort_values(["Timestamp", "Market", "SequenceNumber"], axis=0, ascending=True)
        self.logger.info(f"Download complete. Data contains {len(sorted_trades)} trades.")
        self.__trades = sorted_trades

    def save(self) -> None:
        self.__trades.to_csv(self.__filename, index=False, mode="w")

    def __str__(self) -> str:
        return f"« 𝚃𝚛𝚊𝚍𝚎𝙷𝚒𝚜𝚝𝚘𝚛𝚢 for {self.__account.address} »"

    def __repr__(self) -> str:
        return f"{self}"
