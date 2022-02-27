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

import abc
import random
import time


class IdGenerator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def generate_id(self) -> int:
        raise NotImplementedError(
            "IdGenerator.generate_id() is not implemented on the base type."
        )


class RandomIdGenerator(IdGenerator):
    def generate_id(self) -> int:
        # 9223372036854775807 is sys.maxsize for 64-bit systems, with a bit_length of 63.\n",
        # We explicitly want to use a max of 64-bits though, so we use the number instead of\n",
        # sys.maxsize, which could be lower on 32-bit systems or higher on 128-bit systems.\n",
        return random.randrange(9223372036854775807)  # nosemgrep


class MonotonicIdGenerator(IdGenerator):
    def __init__(self) -> None:
        self.__last_generated_id: int = 0

    def generate_id(self) -> int:
        # After this discussion with Max on Discord (https://discord.com/channels/791995070613159966/818978757648842782/884751007656054804):
        #   can you generate monotonic ids?
        #   in case not the result wouldn't be different from what we have rn, which is random display
        #   so there's still a net benefit for changing the UI
        #   and if you could use the same id generation scheme (unix time in ms) it would even work well with the UI :slight_smile:
        #
        # We go with the time in milliseconds. We get the time in nanoseconds and divide it by 1,000,000 to get
        # the time in milliseconds.
        #
        # But there's more! Because this can be called in a burst, for, say, a dozen orders all within the same
        # millisecond. And using duplicate client order IDs would be Bad. So we keep track of the last one we
        # sent, and we just add one if we get an identical value.
        new_id: int = round(time.time_ns() / 1000000)
        if new_id <= self.__last_generated_id:
            new_id = self.__last_generated_id + 1
        self.__last_generated_id = new_id
        return new_id
