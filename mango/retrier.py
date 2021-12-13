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
import typing
import requests.exceptions
import time

from contextlib import contextmanager
from decimal import Decimal


# # 🥭 RetryWithPauses class
#
# This class takes a function and a list of durations to pause after a failed call.
#
# If the function succeeds, the resultant value is returned.
#
# If the function fails by raising an exception, the call pauses for the duration at the
# head of the list, then the head of the list is moved and the function is retried.
#
# It is retried up to the number of entries in the list of delays. If they all fail, the
# last failing exception is re-raised.
#
# This can be particularly helpful in cases where rate limits prevent further processing.
#
# This class is best used in a `with...` block using the `retry_context()` function below.
#
class RetryWithPauses:
    def __init__(self, name: str, func: typing.Callable[..., typing.Any], pauses: typing.Sequence[Decimal]) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.name: str = name
        self.func: typing.Callable[..., typing.Any] = func
        self.pauses: typing.Sequence[Decimal] = pauses

    def run(self, *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        captured_exception: Exception
        for sleep_time_on_error in self.pauses:
            try:
                return self.func(*args, **kwargs)
            except requests.exceptions.HTTPError as exception:
                captured_exception = exception
                if exception.response is not None:
                    # "You will see HTTP respose codes 429 for too many requests
                    # or 413 for too much bandwidth."
                    if exception.response.status_code == 413:
                        self._logger.info(
                            f"Retriable call [{self.name}] rate limited (too much bandwidth) with error '{exception}'.")
                    elif exception.response.status_code == 429:
                        self._logger.info(
                            f"Retriable call [{self.name}] rate limited (too many requests) with error '{exception}'.")
                    else:
                        self._logger.info(
                            f"Retriable call [{self.name}] failed with unexpected HTTP error '{exception}'.")
                else:
                    self._logger.info(f"Retriable call [{self.name}] failed with unknown HTTP error '{exception}'.")
            except Exception as exception:
                self._logger.info(f"Retriable call failed [{self.name}] with error '{exception}'.")
                captured_exception = exception

            if sleep_time_on_error < 0:
                self._logger.info(f"No more retries for [{self.name}] - propagating exception.")
                raise captured_exception

            self._logger.info(f"Will retry [{self.name}] call in {sleep_time_on_error} second(s).")
            time.sleep(float(sleep_time_on_error))

        self._logger.info(f"End of retry loop for [{self.name}] - propagating exception.")
        raise captured_exception


# # 🥭 retry_context generator
#
# This is a bit of Python 'magic' to allow using the Retrier in a `with...` block.
#
# For example, this will call function `some_function(param1, param2)` up to `retry_count`
# times (7 in this case). It will only retry if the function throws an exception - the
# result of the first successful call is used to set the `result` variable:
# ```
# pauses = [Decimal(1), Decimal(2), Decimal(4)]
# with retry_context("Account Access", some_function, pauses) as retrier:
#     result = retrier.run(param1, param2)
# ```

@contextmanager
def retry_context(name: str, func: typing.Callable[..., typing.Any], pauses: typing.Sequence[Decimal]) -> typing.Iterator[RetryWithPauses]:
    yield RetryWithPauses(name, func, pauses)
