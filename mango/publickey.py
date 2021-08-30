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

import typing

from solana.publickey import PublicKey


# # 🥭 encode_public_key_for_sorting function
#
# This is fairly nasty and unintuitive.
#
# ConsumeEvents in Serum takes in a list of OpenOrders addresses but (since it runs a binary
# search on them) they have to be sorted. Calling it in Rust uses a BTreeSet to build the
# sorted list, but it builds it from the underlying integers of the PublicKey.
#
# Every PublicKey is 32 bytes long. The 'raw' view in Rust is an array of 4 8-byte words
# expressed as integers.
#
# When the BTreeSet orders these, it uses the underlying 4 ints.
#
# So when we want to provide a sorted array to ConsumeEvents, we need to sort it the same way.
#
def encode_public_key_for_sorting(address: PublicKey) -> typing.List[int]:
    raw = bytes(address)
    return [
        int.from_bytes(raw[0:8], "little"),
        int.from_bytes(raw[8:16], "little"),
        int.from_bytes(raw[16:24], "little"),
        int.from_bytes(raw[24:32], "little")
    ]
