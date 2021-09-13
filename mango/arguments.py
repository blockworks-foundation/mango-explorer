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

import argparse
import logging
import typing

from .constants import WARNING_DISCLAIMER_TEXT


# # 🥭 parse_args
#
# This function parses CLI arguments and sets up common logging for all commands.
#
def parse_args(parser: argparse.ArgumentParser, logging_default=logging.INFO) -> argparse.Namespace:
    parser.add_argument("--log-level", default=logging_default, type=lambda level: getattr(logging, level),
                        help="level of verbosity to log (possible values: DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    parser.add_argument("--log-suppress-timestamp", default=False, action="store_true",
                        help="Suppress timestamp in log output (useful for systems that supply their own timestamp on log messages)")

    args: argparse.Namespace = parser.parse_args()

    log_record_format: str = "%(asctime)s %(level_emoji)s %(name)-12.12s %(message)s"
    print("args.log_suppress_timestamp", args.log_suppress_timestamp)
    if args.log_suppress_timestamp:
        print("Here")
        log_record_format = "%(level_emoji)s %(name)-12.12s %(message)s"

    print("log_record_format", log_record_format)

    # Make logging a little more verbose than the default.
    logging.basicConfig(level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S", format=log_record_format)

    # Stop libraries outputting lots of information unless it's a warning or worse.
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("solanaweb3").setLevel(logging.WARNING)

    default_log_record_factory: typing.Callable[[typing.Any], logging.LogRecord] = logging.getLogRecordFactory()
    log_levels: typing.Dict[int, str] = {
        logging.CRITICAL: "🛑",
        logging.ERROR: "🚨",
        logging.WARNING: "⚠",
        logging.INFO: "ⓘ",
        logging.DEBUG: "🐛"
    }

    def _emojified_record_factory(*args, **kwargs):
        record = default_log_record_factory(*args, **kwargs)
        # Here's where we add our own format keywords.
        record.level_emoji = log_levels[record.levelno]
        return record

    logging.setLogRecordFactory(_emojified_record_factory)

    logging.getLogger().setLevel(args.log_level)
    logging.warning(WARNING_DISCLAIMER_TEXT)

    return args
