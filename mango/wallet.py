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


import json
import logging
import os.path
import typing

from solana.account import Account
from solana.publickey import PublicKey


# # 🥭 Wallet class
#
# The `Wallet` class wraps our understanding of saving and loading keys, and creating the
# appropriate Solana `Account` object.
#
# To load a private key from a file, the file must be a JSON-formatted text file with a root
# array of the 64 bytes making up the secret key.
#
# For example:
# ```
# [200,48,184,13... for another 60 bytes...]
# ```
# **TODO:** It would be good to be able to load a `Wallet` from a mnemonic string. I haven't yet found a Python library that can generate a BIP44 derived seed for Solana that matches the derived seeds created by Sollet and Ledger.
#


_DEFAULT_WALLET_FILENAME: str = "id.json"


class Wallet:
    def __init__(self, secret_key):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.secret_key = secret_key[0:32]
        self.account = Account(self.secret_key)

    @property
    def address(self) -> PublicKey:
        return self.account.public_key()

    def save(self, filename: str, overwrite: bool = False) -> None:
        if os.path.isfile(filename) and not overwrite:
            raise Exception(f"Wallet file '{filename}' already exists.")

        with open(filename, "w") as json_file:
            json.dump(list(self.secret_key), json_file)

    @staticmethod
    def load(filename: str = _DEFAULT_WALLET_FILENAME) -> "Wallet":
        if not os.path.isfile(filename):
            logging.error(f"Wallet file '{filename}' is not present.")
            raise Exception(f"Wallet file '{filename}' is not present.")
        else:
            with open(filename) as json_file:
                data = json.load(json_file)
                return Wallet(data)

    @staticmethod
    def create() -> "Wallet":
        new_account = Account()
        new_secret_key = new_account.secret_key()
        return Wallet(new_secret_key)


# default_wallet object
#
# A default Wallet object that loads the private key from the id.json file, if it exists.
#

default_wallet: typing.Optional[Wallet] = None
if os.path.isfile(_DEFAULT_WALLET_FILENAME):
    try:
        default_wallet = Wallet.load(_DEFAULT_WALLET_FILENAME)
    except Exception as exception:
        logging.warning(
            f"Failed to load default wallet from file '{_DEFAULT_WALLET_FILENAME}' - exception: {exception}")
