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


import enum


# # 🥭 InstructionType enum
#
# This `enum` encapsulates all current Mango Market instruction variants.
#


class InstructionType(enum.IntEnum):
    InitMangoGroup = 0
    InitMarginAccount = 1
    Deposit = 2
    Withdraw = 3
    Borrow = 4
    SettleBorrow = 5
    Liquidate = 6
    DepositSrm = 7
    WithdrawSrm = 8
    PlaceOrder = 9
    SettleFunds = 10
    CancelOrder = 11
    CancelOrderByClientId = 12
    ChangeBorrowLimit = 13
    PlaceAndSettle = 14
    ForceCancelOrders = 15
    PartialLiquidate = 16

    def __str__(self):
        return self.name
