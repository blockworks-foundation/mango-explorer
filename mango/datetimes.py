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

from datetime import datetime, timezone

# # 🥭 Datetimes
#
# This file contains a few useful datetime functions.
#
# They exist solely to make clear what is being used when called. There are 2 general cases:
# 1. Logging/time tracking/user output - local time is what should be used.
# 2. Comparison with dates stored on-chain - UTC should be used.
#
# Getting a UTC time that is comparable with on-chain datetimes isn't intuitive, so putting
# it in one place and using that consistently should make it clearer in the calling code
# what is going on, without the unnecessary complications.
#


def local_now() -> datetime:
    return datetime.now()


def utc_now() -> datetime:
    return datetime.utcnow().astimezone(timezone.utc)
