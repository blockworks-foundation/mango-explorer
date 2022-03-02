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
# Comparing datetime values in Python can lead to the following error:
#   TypeError: can't compare offset-naive and offset-aware datetimes
#
# To avoid that, we use these functions to consistently create the datetime in a way
# that has the correct value and that can be compared with other datetimes generated
# by these methods.
#
# However, getting a comparable UTC time using this mechanism:
#   return datetime.utcnow().astimezone(timezone.utc)
#
# works fine on Linux and Mac but fails on Windows. So we need to avoid that method and
# be careful of different platform issues.
#
# If you use these methods to generate the datetime values, you _should_ be safe.
#


def local_now() -> datetime:
    return datetime.now().astimezone()


# Getting a comparable UTC time using this line:
#   return datetime.utcnow().astimezone(timezone.utc)
# seems to cause `OSError: [Errno 22] Invalid argument` on Windows (but is fine on Mac and
# Linux). Best to avoid it and use the following instead, which seems to work consistently
# on Windows as well as Mac and Linux.
def utc_now() -> datetime:
    return datetime.utcnow().replace(tzinfo=timezone.utc)


# All timestamp values _should be_ in UTC. All we need to do is load the value as a UTC
# datetime that's comparable on all platforms, so we do this the same way as `utc_now()`.
def datetime_from_timestamp(timestamp: float) -> datetime:
    return datetime.utcfromtimestamp(timestamp).replace(tzinfo=timezone.utc)


# All on-chain datetime values are in UTC. All we need to do is load the value as a UTC
# datetime that's comparable on all platforms, so we do this the same way as `utc_now()`.
def datetime_from_chain(onchain_value: float) -> datetime:
    return datetime.utcfromtimestamp(onchain_value).replace(tzinfo=timezone.utc)
