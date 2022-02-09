import random
import typing

from .context import mango

from decimal import Decimal

from .fakes import fake_order_id


def test_order_book_sides_sorted_by_price() -> None:
    bids_side = _construct_order_book_side(mango.Side.BUY, 5)
    asks_side = _construct_order_book_side(mango.Side.SELL, 5)
    order_book = _construct_order_book(bids=bids_side, asks=asks_side)
    assert sorted(bids_side, key=lambda o: o.price, reverse=True) == order_book.bids
    assert sorted(asks_side, key=lambda o: o.price, reverse=False) == order_book.asks


def test_orderbook_top_bids_and_asks() -> None:
    bids = _construct_order_book_side(mango.Side.BUY, 7)
    asks = _construct_order_book_side(mango.Side.SELL, 7)
    orderBook: mango.OrderBook = _construct_order_book(bids=bids, asks=asks)

    assert _get_order(bids, -1) == orderBook.top_bid
    assert _get_order(asks) == orderBook.top_ask
    # update orderbook
    update_bids = _construct_order_book_side(mango.Side.BUY, 5)
    update_asks = _construct_order_book_side(mango.Side.SELL, 5)
    orderBook.bids = update_bids
    orderBook.asks = update_asks
    assert _get_order(update_bids, -1) == orderBook.top_bid
    assert _get_order(update_asks) == orderBook.top_ask


def test_orderbook_spread() -> None:
    bids = _construct_order_book_side(mango.Side.BUY, 7)
    asks = _construct_order_book_side(mango.Side.SELL, 7)
    # None's in book
    orderBook: mango.OrderBook = _construct_order_book(bids=bids, asks=[])
    assert orderBook.spread == Decimal(0)
    orderBook = _construct_order_book(bids=[], asks=[])
    assert orderBook.spread == Decimal(0)
    orderBook = _construct_order_book([], [])
    assert orderBook.spread == Decimal(0)
    # ask's spread calculated from generated data
    orderBook = _construct_order_book(bids=bids, asks=asks)
    assert orderBook.spread == _get_order(asks).price - _get_order(bids, -1).price


# ASK is SELL, BID is BUY
def _construct_order_book_side(
    askOrBidSide: mango.Side, size: int
) -> typing.Sequence[mango.Order]:
    result_orders: typing.List[mango.Order] = []
    for index, price in enumerate(random.sample(range(1, 1000), size)):
        constructed_id = fake_order_id(index, price)
        order = mango.Order.from_ids(
            id=constructed_id,
            client_id=0,
            side=askOrBidSide,
            price=Decimal(price),
            quantity=Decimal(random.randint(1, 100)),
        )
        result_orders.append(order)
    return result_orders


def _construct_order_book(
    bids: typing.Sequence[mango.Order], asks: typing.Sequence[mango.Order]
) -> mango.OrderBook:
    # construct orderbook
    return mango.OrderBook(
        symbol="TEST",
        lot_size_converter=mango.NullLotSizeConverter(),
        bids=bids,
        asks=asks,
    )


def _get_order(orders: typing.Sequence[mango.Order], index: int = 0) -> mango.Order:
    return sorted(orders, key=lambda order: order.price)[index]
