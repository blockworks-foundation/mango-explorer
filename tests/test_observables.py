from .context import mango

import rx


def test_collecting_observer_subscriber():
    items = ["a", "b", "c"]
    actual = mango.CollectingObserverSubscriber()
    rx.from_(items).subscribe(actual)
    assert actual.collected == items
