from .context import mango


def test_constructor() -> None:
    initialized: bool = True
    market: bool = True
    open_orders: bool = True
    request_queue: bool = True
    event_queue: bool = True
    bids: bool = True
    asks: bool = True
    disabled: bool = True
    actual = mango.AccountFlags(
        mango.Version.V1,
        initialized,
        market,
        open_orders,
        request_queue,
        event_queue,
        bids,
        asks,
        disabled,
    )
    assert actual is not None
    assert actual.version == mango.Version.V1
    assert actual.initialized == initialized
    assert actual.market == market
    assert actual.open_orders == open_orders
    assert actual.request_queue == request_queue
    assert actual.event_queue == event_queue
    assert actual.bids == bids
    assert actual.asks == asks
    assert actual.disabled == disabled

    actual2 = mango.AccountFlags(
        mango.Version.V2,
        not initialized,
        not market,
        not open_orders,
        not request_queue,
        not event_queue,
        not bids,
        not asks,
        not disabled,
    )
    assert actual2 is not None
    assert actual2.version == mango.Version.V2
    assert actual2.initialized == (not initialized)
    assert actual2.market == (not market)
    assert actual2.open_orders == (not open_orders)
    assert actual2.request_queue == (not request_queue)
    assert actual2.event_queue == (not event_queue)
    assert actual2.bids == (not bids)
    assert actual2.asks == (not asks)
    assert actual2.disabled == (not disabled)
