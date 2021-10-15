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

from .idl import IdlParser, lazy_load_cached_idl_parser


def expand_log_messages(original_messages: typing.Sequence[str]) -> typing.Sequence[str]:
    idl_parser: IdlParser = lazy_load_cached_idl_parser("mango_logs.json")
    expanded_messages: typing.List[str] = []
    parse_next_line: bool = False
    for message in original_messages:
        if parse_next_line:
            encoded: str = message[len("Program log: "):]
            name, parsed = idl_parser.decode_and_parse(encoded)
            expanded_messages += ["Mango " + name + " " + str(parsed)]
            parse_next_line = False
        elif message == "Program log: mango-log":
            parse_next_line = True
        else:
            expanded_messages += [message]
            parse_next_line = False

    return expanded_messages
