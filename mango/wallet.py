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
import json
import logging
import os
import os.path
import typing

from solana.account import Account as SolanaAccount
from solana.keypair import Keypair
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
#
# Alternatively (useful for some environments) the bytes can be loaded from the environment.
# The environment key is "KEYPAIR", so it would be stored in the environment using something
# like:
# ```
# export KEYPAIR="[200,48,184,13... for another 60 bytes...]"
# ```
# Alternatively, the environment key "SECRET_KEY" is accepted as an alias for KEYPAIR and may
# be used instead. (If both are specified, "KEYPAIR" is used.)
#
# **TODO:** It would be good to be able to load a `Wallet` from a mnemonic string. I haven't
# yet found a Python library that can generate a BIP44 derived seed for Solana that matches
# the derived seeds created by Sollet and Ledger.
#


_DEFAULT_WALLET_FILENAME: str = "id.json"


class Wallet:
    def __init__(self, secret_key: bytes):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.secret_key: bytes = secret_key[0:32]
        self.keypair: Keypair = Keypair(self.secret_key)

    @property
    def address(self) -> PublicKey:
        return self.keypair.public_key

    def to_deprecated_solana_account(self) -> SolanaAccount:
        # Solana Account is deprecated, so we use keypair everywhere. Some libraries like PySerum haven't
        # caught up yet though, so this gives us a way to access the Solana Account object consistently.
        return SolanaAccount(self.keypair.secret_key[0:32])

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
        new_account = Keypair()
        new_secret_key = new_account.secret_key
        return Wallet(new_secret_key)

    # Configuring a `Wallet` is a common operation for command-line programs and can involve a
    # lot of duplicate code.
    #
    # This function centralises some of it to ensure consistency and readability.
    #
    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--id-file", type=str, default=_DEFAULT_WALLET_FILENAME,
                            help="file containing the JSON-formatted wallet private key")

    # This function is the converse of `add_command_line_parameters()` - it takes
    # an argument of parsed command-line parameters and expects to see the ones it added
    # to that collection in the `add_command_line_parameters()` call.
    #
    # It then uses those parameters to create a properly-configured `Wallet` object.
    #
    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> typing.Optional["Wallet"]:
        # We always have an args.id_file (because we specify a default) so check for the environment
        # variable and give it priority.
        environment_secret_key = os.environ.get("KEYPAIR") or os.environ.get("SECRET_KEY")
        if environment_secret_key is not None:
            secret_key_bytes = json.loads(environment_secret_key)
            if len(secret_key_bytes) >= 32:
                return Wallet(secret_key_bytes)

        # Here we should have values for all our parameters.
        id_filename = args.id_file
        if os.path.isfile(id_filename):
            return Wallet.load(id_filename)

        return None

    @staticmethod
    def from_command_line_parameters_or_raise(args: argparse.Namespace) -> "Wallet":
        wallet = Wallet.from_command_line_parameters(args)
        if wallet is None:
            raise Exception("No wallet file or environment variables available.")

        return wallet

    def __str__(self) -> str:
        return f"« 𝚆𝚊𝚕𝚕𝚎𝚝 for {self.address} »"

    def __repr__(self) -> str:
        return f"{self}"
