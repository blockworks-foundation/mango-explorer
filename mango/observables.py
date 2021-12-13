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
import rx
import rx.subject
import typing

from datetime import datetime
from rx.core.typing import Disposable
from rxpy_backpressure import BackPressure


# # 🥭 Observables
#
# This notebook contains some useful shared tools to work with
# [RX Observables](https://rxpy.readthedocs.io/en/latest/reference_observable.html).
#

# # 🥭 NullObserverSubscriber class
#
# This class can subscribe to an `Observable` to do nothing but make sure it runs.
#
class NullObserverSubscriber(rx.core.observer.observer.Observer):
    def __init__(self) -> None:
        super().__init__()

    def on_next(self, item: typing.Any) -> None:
        pass

    def on_error(self, ex: Exception) -> None:
        pass

    def on_completed(self) -> None:
        pass


# # 🥭 PrintingObserverSubscriber class
#
# This class can subscribe to an `Observable` and print out each item.
#
class PrintingObserverSubscriber(rx.core.observer.observer.Observer):
    def __init__(self, report_no_output: bool) -> None:
        super().__init__()
        self.report_no_output = report_no_output
        self.counter = 0

    def on_next(self, item: typing.Any) -> None:
        self.report_no_output = False
        print(self.counter, item)
        self.counter += 1

    def on_error(self, ex: Exception) -> None:
        self.report_no_output = False
        print(ex)

    def on_completed(self) -> None:
        if self.report_no_output:
            print("No items to show.")


# # 🥭 TimestampedPrintingObserverSubscriber class
#
# Just like `PrintingObserverSubscriber` but it puts a timestamp on each printout.
#
class TimestampedPrintingObserverSubscriber(PrintingObserverSubscriber):
    def __init__(self, report_no_output: bool) -> None:
        super().__init__(report_no_output)

    def on_next(self, item: typing.Any) -> None:
        super().on_next(f"{datetime.now()}: {item}")


# # 🥭 CollectingObserverSubscriber class
#
# This class can subscribe to an `Observable` and collect each item.
#
class CollectingObserverSubscriber(rx.core.observer.observer.Observer):
    def __init__(self) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.collected: typing.List[typing.Any] = []

    def on_next(self, item: typing.Any) -> None:
        self.collected += [item]

    def on_error(self, ex: Exception) -> None:
        self._logger.error(f"Received error: {ex}")

    def on_completed(self) -> None:
        pass


# # 🥭 CaptureFirstItem class
#
# This captures the first item to pass through the pipeline, allowing it to be inspected
# later.
#
class CaptureFirstItem:
    def __init__(self) -> None:
        self.captured: typing.Any = None
        self.has_captured: bool = False

    def capture_if_first(self, item: typing.Any) -> typing.Any:
        if not self.has_captured:
            self.captured = item
            self.has_captured = True

        return item


# # 🥭 TItem type parameter
#
# The `TItem` type parameter is the type parameter for the generic `LatestItemObserverSubscriber`.
#
TItem = typing.TypeVar('TItem')


# # 🥭 LatestItemObserverSubscriber class
#
# This class can subscribe to an `Observable` and capture the latest item as it is observed.
#
class LatestItemObserverSubscriber(rx.core.observer.observer.Observer, typing.Generic[TItem]):
    def __init__(self, initial: TItem) -> None:
        super().__init__()
        self.latest: TItem = initial
        self.update_timestamp: datetime = datetime.now()

    def on_next(self, item: TItem) -> None:
        self.latest = item
        self.update_timestamp = datetime.now()

    def on_error(self, ex: Exception) -> None:
        pass

    def on_completed(self) -> None:
        pass


# # 🥭 FunctionObserver
#
# This class takes functions for `on_next()`, `on_error()` and `on_completed()` and returns
# an `Observer` object.
#
# This is mostly for libraries (like `rxpy_backpressure`) that take observers but not their
# component functions.
#
class FunctionObserver(rx.core.observer.observer.Observer):
    def __init__(self,
                 on_next: typing.Callable[[typing.Any], None],
                 on_error: typing.Callable[[Exception], None] = lambda _: None,
                 on_completed: typing.Callable[[], None] = lambda: None) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._on_next = on_next
        self._on_error = on_error
        self._on_completed = on_completed

    def on_next(self, value: typing.Any) -> None:
        try:
            self._on_next(value)
        except Exception as exception:
            self._logger.warning(f"on_next callable raised exception: {exception}")

    def on_error(self, error: Exception) -> None:
        try:
            self._on_error(error)
        except Exception as exception:
            self._logger.warning(f"on_error callable raised exception: {exception}")

    def on_completed(self) -> None:
        try:
            self._on_completed()
        except Exception as exception:
            self._logger.warning(f"on_completed callable raised exception: {exception}")


# # 🥭 DisposingSubject
#
# This class is a regular Subject that can take additional `Disposable` objects to dispose of when the
# `Subject` is being cleaned up.
#
class DisposingSubject(rx.subject.subject.Subject):
    def __init__(self) -> None:
        super().__init__()
        self._to_dispose: typing.List[rx.core.typing.Disposable] = []

    def add_disposable(self, disposable: rx.core.typing.Disposable) -> None:
        self._to_dispose += [disposable]

    def dispose(self) -> None:
        for disposable in self._to_dispose:
            disposable.dispose()
        super().dispose()


# # 🥭 create_backpressure_skipping_observer function
#
# Creates an `Observer` that skips inputs if they are building up while a subscriber works.
#
# This is useful for situations that, say, poll every second but the operation can sometimes
# take multiple seconds to complete. In that case, the latest item will be immediately
# emitted and the in-between items skipped.
#
def create_backpressure_skipping_observer(on_next: typing.Callable[[typing.Any], None], on_error: typing.Callable[[Exception], None] = lambda _: None, on_completed: typing.Callable[[], None] = lambda: None) -> rx.core.typing.Observer[typing.Any]:
    observer = FunctionObserver(on_next=on_next, on_error=on_error, on_completed=on_completed)
    return typing.cast(rx.core.typing.Observer[typing.Any], BackPressure.LATEST(observer))


# # 🥭 debug_print_item function
#
# This is a handy item that can be added to a pipeline to show what is being passed at that particular stage. For example, this shows how to print the item before and after filtering:
# ```
# fetch().pipe(
#     ops.map(debug_print_item("Unfiltered:")),
#     ops.filter(lambda item: item.something is not None),
#     ops.map(debug_print_item("Filtered:")),
#     ops.filter(lambda item: item.something_else()),
#     ops.map(act_on_item)
# ).subscribe(some_subscriber)
# ```
#
def debug_print_item(title: str) -> typing.Callable[[typing.Any], typing.Any]:
    def _debug_print_item(item: typing.Any) -> typing.Any:
        print(title, item)
        return item
    return _debug_print_item


# # 🥭 log_subscription_error function
#
# Logs subscription exceptions to the root logger.
#
def log_subscription_error(error: Exception) -> None:
    logging.error(f"Observable subscription error: {error}")


# # 🥭 observable_pipeline_error_reporter function
#
# This intercepts and re-raises an exception, to help report on errors.
#
# RxPy pipelines are tricky to restart, so it's often easier to use the `ops.retry()`
# function in the pipeline. That just swallows the error though, so there's no way to know
# what was raised to cause the retry.
#
# Enter `observable_pipeline_error_reporter()`! Put it in a `catch` just before the `retry`
# and it should log the error properly.
#
# For example:
# ```
# from rx import of, operators as ops
#
# def raise_on_every_third(item):
#     if (item % 3 == 0):
#         raise Exception("Divisible by 3")
#     else:
#         return item
#
# sub1 = of(1, 2, 3, 4, 5, 6).pipe(
#     ops.map(lambda e : raise_on_every_third(e)),
#     ops.catch(observable_pipeline_error_reporter),
#     ops.retry(3)
# )
# sub1.subscribe(lambda item: print(item), on_error = lambda error: print(f"Error : {error}"))
# ```
#
def observable_pipeline_error_reporter(ex: Exception, _: rx.core.observable.observable.Observable) -> rx.core.observable.observable.Observable:
    logging.error(f"Intercepted error in observable pipeline: {ex}")
    raise ex


# # 🥭 TEventDatum type parameter
#
# The `TEventDatum` type parameter is the type parameter for the generic `LatestItemObserverSubscriber`.
#
TEventDatum = typing.TypeVar('TEventDatum')


# # 🥭 EventSource class
#
# A strongly(ish)-typed event source that can handle many subscribers.
#
class EventSource(rx.subject.subject.Subject, typing.Generic[TEventDatum]):
    def __init__(self) -> None:
        super().__init__()
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    def on_next(self, event: TEventDatum) -> None:
        super().on_next(event)

    def on_error(self, ex: Exception) -> None:
        super().on_error(ex)

    def on_completed(self) -> None:
        super().on_completed()

    def publish(self, event: TEventDatum) -> None:
        try:
            self.on_next(event)
        except Exception as exception:
            self._logger.warning(f"Failed to publish event '{event}' - {exception}")

    def dispose(self) -> None:
        super().dispose()


# # 🥭 DisposePropagator class
#
# A `Disposable` class that can 'fan out' `dispose()` calls to perform additional
# cleanup actions.
#
class DisposePropagator(Disposable):
    def __init__(self) -> None:
        self.disposables: typing.List[Disposable] = []

    def add_disposable(self, disposable: Disposable) -> None:
        self.disposables += [disposable]

    def dispose(self) -> None:
        for disposable in self.disposables:
            disposable.dispose()


# # 🥭 DisposeWrapper class
#
# A `Disposable` class that wraps a lambda to perform some cleanup actions when it is disposed.
#
class DisposeWrapper(Disposable):
    def __init__(self, callable: typing.Callable[[], None]) -> None:
        self.callable: typing.Callable[[], None] = callable

    def dispose(self) -> None:
        self.callable()
