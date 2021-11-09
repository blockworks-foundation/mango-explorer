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


import base64
import base58
import typing
import zstandard

from solana.publickey import PublicKey


# # 🥭 Decoder
#
# This file contains some useful functions for decoding base64 and base58 data.

_decompressor: zstandard.ZstdDecompressor = zstandard.ZstdDecompressor()


# ## decode_binary() function
#
# A Solana binary data structure may come back as an array with the base64 or base58 encoded data, and a text moniker saying which encoding was used.
#
# For example:
# ```
# ['AwAAAAAAAACCaOmpoURMK6XHelGTaFawcuQ/78/15LAemWI8jrt3SRKLy2R9i60eclDjuDS8+p/ZhvTUd9G7uQVOYCsR6+BhmqGCiO6EPYP2PQkf/VRTvw7JjXvIjPFJy06QR1Cq1WfTonHl0OjCkyEf60SD07+MFJu5pVWNFGGEO/8AiAYfduaKdnFTaZEHPcK5Eq72WWHeHg2yIbBF09kyeOhlCJwOoG8O5SgpPV8QOA64ZNV4aKroFfADg6kEy/wWCdp3fv2B8WJgAAAAANVfH3HGtjwAAQAAAAAAAADr8cwFi9UOAAEAAAAAAAAAgfFiYAAAAABo3Dbz0L0oAAEAAAAAAAAAr8K+TvCjCwABAAAAAAAAAIHxYmAAAAAA49t5tVNZhwABAAAAAAAAAAmPtcB1zC8AAQAAAAAAAABIBGiCcyaEZdNhrTyeqUY692vOzzPdHaxAxguht3JQGlkzjtd05dX9LENHkl2z1XvUbTNKZlweypNRetmH0lmQ9VYQAHqylxZVK65gEg85g27YuSyvOBZAjJyRmYU9KdCO1D+4ehdPu9dQB1yI1uh75wShdAaFn2o4qrMYwq3SQQEAAAAAAAAAAiH1PPJKAuh6oGiE35aGhUQhFi/bxgKOudpFv8HEHNCFDy1uAqR6+CTQmradxC1wyyjL+iSft+5XudJWwSdi72NJGmyK96x7Obj/AgAAAAB8RjOEdJow6r9LMhIAAAAAGkNK4CXHh5M2st7PnwAAAE33lx1h8hPFD04AAAAAAAA8YRV3Oa309B2wGwAAAAAAOIlOLmkr6+r605n+AQAAAACgmZmZmZkZAQAAAAAAAAAAMDMzMzMzMwEAAAAAAAAA25D1XcAtRzSuuyx3U+X7aE9vM1EJySU9KprgL0LMJ/vat9+SEEUZuga7O5tTUrcMDYWDg+LYaAWhSQiN2fYk7aCGAQAAAAAAgIQeAAAAAAAA8gUqAQAAAAYGBgICAAAA', 'base64']
# ```
# Alternatively, it may just be a base58-encoded string.
#
# `decode_binary()` decodes the data properly based on which encoding was used.
def decode_binary(encoded: typing.Union[str, typing.Sequence[str]]) -> bytes:
    if isinstance(encoded, str):
        return base58.b58decode(encoded)
    elif encoded[1] == "base64":
        return base64.b64decode(encoded[0])
    elif encoded[1] == "base64+zstd":
        compressed = base64.b64decode(encoded[0])
        with _decompressor.stream_reader(compressed) as reader:
            return reader.read()
    else:
        return base58.b58decode(encoded[0])


# ## encode_binary() function
#
# Inverse of `decode_binary()`, this takes a binary list and encodes it (using base 64), then returns the encoded string and the string "base64" in an array.
#
def encode_binary(decoded: bytes) -> typing.Sequence[str]:
    return [base64.b64encode(decoded).decode(), "base64"]


# ## encode_key() function
#
# Encodes a `PublicKey` in the proper way for RPC calls.
def encode_key(key: PublicKey) -> str:
    return str(key)


# ## encode_int() function
#
# Encodes an `int` in the proper way for RPC calls.
def encode_int(value: int) -> str:
    return base58.b58encode_int(value).decode('ascii')
