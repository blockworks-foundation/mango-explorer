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


import pyserum.enums
import typing

from solana.publickey import PublicKey

from .instructiontype import InstructionType
from .orders import OrderType, Side


# The index of the sender/signer depends on the instruction.
_instruction_signer_indices: typing.Dict[InstructionType, int] = {
    InstructionType.InitMangoGroup: 1,
    InstructionType.InitMarginAccount: 2,
    InstructionType.Deposit: 2,
    InstructionType.Withdraw: 2,
    InstructionType.AddSpotMarket: 7,
    InstructionType.AddToBasket: 2,
    InstructionType.Borrow: 2,
    InstructionType.CachePrices: -1,  # No signer
    InstructionType.CacheRootBanks: -1,  # No signer
    InstructionType.PlaceSpotOrder: 2,
    InstructionType.AddOracle: 2,
    InstructionType.AddPerpMarket: 6,
    InstructionType.PlacePerpOrder: 2,
    InstructionType.CancelPerpOrderByClientId: 2,
    InstructionType.CancelPerpOrder: 2,
    InstructionType.ConsumeEvents: -1,  # No signer
    InstructionType.CachePerpMarkets: -1,  # No signer
    InstructionType.UpdateFunding: -1,  # No signer
    InstructionType.SetOracle: -1,  # No signer
    InstructionType.SettleFunds: 2,
    InstructionType.CancelSpotOrder: 1,
    InstructionType.UpdateRootBank: -1,  # No signer
    InstructionType.SettlePnl: -1,  # No signer
    InstructionType.SettleBorrow: -1,  # No signer
    InstructionType.ForceCancelSpotOrders: -1,
    InstructionType.ForceCancelPerpOrders: -1,
    InstructionType.LiquidateTokenAndToken: -1,
    InstructionType.LiquidateTokenAndPerp: -1,
    InstructionType.LiquidatePerpMarket: -1,
    InstructionType.SettleFees: -1,
    InstructionType.ResolvePerpBankruptcy: -1,
    InstructionType.ResolveTokenBankruptcy: -1,
    InstructionType.InitSpotOpenOrders: -1,
    InstructionType.RedeemMngo: -1,
    InstructionType.AddMangoAccountInfo: -1,
    InstructionType.DepositMsrm: -1,
    InstructionType.WithdrawMsrm: -1,
    InstructionType.ChangePerpMarketParams: -1,
    InstructionType.SetGroupAdmin: -1,
    InstructionType.CancelAllPerpOrders: -1,
    InstructionType.ForceSettleQuotePositions: -1,
    InstructionType.PlaceSpotOrder2: -1,
    InstructionType.InitAdvancedOrders: -1,
    InstructionType.AddPerpTriggerOrder: -1,
    InstructionType.RemoveAdvancedOrder: -1,
    InstructionType.ExecutePerpTriggerOrder: -1,
    InstructionType.CreatePerpMarket: -1,
    InstructionType.ChangePerpMarketParams2: -1,
    InstructionType.UpdateMarginBasket: -1,
    InstructionType.ChangeMaxMangoAccounts: -1,
    InstructionType.CloseMangoAccount: -1,
    InstructionType.CloseSpotOpenOrders: -1,
    InstructionType.CloseAdvancedOrders: -1,
    InstructionType.CreateDustAccount: -1,
    InstructionType.ResolveDust: -1,
    InstructionType.CreateMangoAccount: -1,
    InstructionType.UpgradeMangoAccountV0V1: -1,
    InstructionType.CancelPerpOrderSide: -1,
    InstructionType.SetDelegate: -1,
    InstructionType.ChangeSpotMarketParams: -1,
    InstructionType.CreateSpotOpenOrders: -1,
    InstructionType.ChangeReferralFeeParams: -1,
    InstructionType.SetReferrerMemory: -1,
    InstructionType.RegisterReferrerId: -1,
    InstructionType.PlacePerpOrder2: 2,
}


# The index of the token IN account depends on the instruction, and for some instructions
# doesn't exist.
_token_in_indices: typing.Dict[InstructionType, int] = {
    InstructionType.InitMangoGroup: -1,
    InstructionType.InitMarginAccount: -1,
    InstructionType.Deposit: 8,
    InstructionType.Withdraw: 7,
    InstructionType.AddSpotMarket: -1,
    InstructionType.AddToBasket: -1,
    InstructionType.Borrow: -1,
    InstructionType.CachePrices: -1,
    InstructionType.CacheRootBanks: -1,
    InstructionType.PlaceSpotOrder: -1,
    InstructionType.AddOracle: -1,
    InstructionType.AddPerpMarket: -1,
    InstructionType.PlacePerpOrder: -1,
    InstructionType.CancelPerpOrderByClientId: -1,
    InstructionType.CancelPerpOrder: -1,
    InstructionType.ConsumeEvents: -1,
    InstructionType.CachePerpMarkets: -1,
    InstructionType.UpdateFunding: -1,
    InstructionType.SetOracle: -1,
    InstructionType.SettleFunds: -1,
    InstructionType.CancelSpotOrder: -1,
    InstructionType.UpdateRootBank: -1,
    InstructionType.SettlePnl: -1,
    InstructionType.SettleBorrow: -1,
    InstructionType.ForceCancelSpotOrders: -1,
    InstructionType.ForceCancelPerpOrders: -1,
    InstructionType.LiquidateTokenAndToken: -1,
    InstructionType.LiquidateTokenAndPerp: -1,
    InstructionType.LiquidatePerpMarket: -1,
    InstructionType.SettleFees: -1,
    InstructionType.ResolvePerpBankruptcy: -1,
    InstructionType.ResolveTokenBankruptcy: -1,
    InstructionType.InitSpotOpenOrders: -1,
    InstructionType.RedeemMngo: -1,
    InstructionType.AddMangoAccountInfo: -1,
    InstructionType.DepositMsrm: -1,
    InstructionType.WithdrawMsrm: -1,
    InstructionType.ChangePerpMarketParams: -1,
    InstructionType.SetGroupAdmin: -1,
    InstructionType.CancelAllPerpOrders: -1,
    InstructionType.ForceSettleQuotePositions: -1,
    InstructionType.PlaceSpotOrder2: -1,
    InstructionType.InitAdvancedOrders: -1,
    InstructionType.AddPerpTriggerOrder: -1,
    InstructionType.RemoveAdvancedOrder: -1,
    InstructionType.ExecutePerpTriggerOrder: -1,
    InstructionType.CreatePerpMarket: -1,
    InstructionType.ChangePerpMarketParams2: -1,
    InstructionType.UpdateMarginBasket: -1,
    InstructionType.ChangeMaxMangoAccounts: -1,
    InstructionType.CloseMangoAccount: -1,
    InstructionType.CloseSpotOpenOrders: -1,
    InstructionType.CloseAdvancedOrders: -1,
    InstructionType.CreateDustAccount: -1,
    InstructionType.ResolveDust: -1,
    InstructionType.CreateMangoAccount: -1,
    InstructionType.UpgradeMangoAccountV0V1: -1,
    InstructionType.CancelPerpOrderSide: -1,
    InstructionType.SetDelegate: -1,
    InstructionType.ChangeSpotMarketParams: -1,
    InstructionType.CreateSpotOpenOrders: -1,
    InstructionType.ChangeReferralFeeParams: -1,
    InstructionType.SetReferrerMemory: -1,
    InstructionType.RegisterReferrerId: -1,
    InstructionType.PlacePerpOrder2: -1,
}

# The index of the token OUT account depends on the instruction, and for some instructions
# doesn't exist.
_token_out_indices: typing.Dict[InstructionType, int] = {
    InstructionType.InitMangoGroup: -1,
    InstructionType.InitMarginAccount: -1,
    InstructionType.Deposit: 6,
    InstructionType.Withdraw: 6,
    InstructionType.AddSpotMarket: -1,
    InstructionType.AddToBasket: -1,
    InstructionType.Borrow: -1,
    InstructionType.CachePrices: -1,
    InstructionType.CacheRootBanks: -1,
    InstructionType.PlaceSpotOrder: -1,
    InstructionType.AddOracle: -1,
    InstructionType.AddPerpMarket: -1,
    InstructionType.PlacePerpOrder: -1,
    InstructionType.CancelPerpOrderByClientId: -1,
    InstructionType.CancelPerpOrder: -1,
    InstructionType.ConsumeEvents: -1,
    InstructionType.CachePerpMarkets: -1,
    InstructionType.UpdateFunding: -1,
    InstructionType.SetOracle: -1,
    InstructionType.SettleFunds: -1,
    InstructionType.CancelSpotOrder: -1,
    InstructionType.UpdateRootBank: -1,
    InstructionType.SettlePnl: -1,
    InstructionType.SettleBorrow: -1,
    InstructionType.ForceCancelSpotOrders: -1,
    InstructionType.ForceCancelPerpOrders: -1,
    InstructionType.LiquidateTokenAndToken: -1,
    InstructionType.LiquidateTokenAndPerp: -1,
    InstructionType.LiquidatePerpMarket: -1,
    InstructionType.SettleFees: -1,
    InstructionType.ResolvePerpBankruptcy: -1,
    InstructionType.ResolveTokenBankruptcy: -1,
    InstructionType.InitSpotOpenOrders: -1,
    InstructionType.RedeemMngo: -1,
    InstructionType.AddMangoAccountInfo: -1,
    InstructionType.DepositMsrm: -1,
    InstructionType.WithdrawMsrm: -1,
    InstructionType.ChangePerpMarketParams: -1,
    InstructionType.SetGroupAdmin: -1,
    InstructionType.CancelAllPerpOrders: -1,
    InstructionType.ForceSettleQuotePositions: -1,
    InstructionType.PlaceSpotOrder2: -1,
    InstructionType.InitAdvancedOrders: -1,
    InstructionType.AddPerpTriggerOrder: -1,
    InstructionType.RemoveAdvancedOrder: -1,
    InstructionType.ExecutePerpTriggerOrder: -1,
    InstructionType.CreatePerpMarket: -1,
    InstructionType.ChangePerpMarketParams2: -1,
    InstructionType.UpdateMarginBasket: -1,
    InstructionType.ChangeMaxMangoAccounts: -1,
    InstructionType.CloseMangoAccount: -1,
    InstructionType.CloseSpotOpenOrders: -1,
    InstructionType.CloseAdvancedOrders: -1,
    InstructionType.CreateDustAccount: -1,
    InstructionType.ResolveDust: -1,
    InstructionType.CreateMangoAccount: -1,
    InstructionType.UpgradeMangoAccountV0V1: -1,
    InstructionType.CancelPerpOrderSide: -1,
    InstructionType.SetDelegate: -1,
    InstructionType.ChangeSpotMarketParams: -1,
    InstructionType.CreateSpotOpenOrders: -1,
    InstructionType.ChangeReferralFeeParams: -1,
    InstructionType.SetReferrerMemory: -1,
    InstructionType.RegisterReferrerId: -1,
    InstructionType.PlacePerpOrder2: -1,
}


# Some instructions (like liqudate) have a 'target' account. Most don't.
_target_indices: typing.Dict[InstructionType, int] = {
    InstructionType.InitMangoGroup: -1,
    InstructionType.InitMarginAccount: -1,
    InstructionType.Deposit: -1,
    InstructionType.Withdraw: -1,
    InstructionType.AddSpotMarket: -1,
    InstructionType.AddToBasket: -1,
    InstructionType.Borrow: -1,
    InstructionType.CachePrices: -1,
    InstructionType.CacheRootBanks: -1,
    InstructionType.PlaceSpotOrder: -1,
    InstructionType.AddOracle: -1,
    InstructionType.AddPerpMarket: -1,
    InstructionType.PlacePerpOrder: -1,
    InstructionType.CancelPerpOrderByClientId: -1,
    InstructionType.CancelPerpOrder: -1,
    InstructionType.ConsumeEvents: -1,
    InstructionType.CachePerpMarkets: -1,
    InstructionType.UpdateFunding: -1,
    InstructionType.SetOracle: -1,
    InstructionType.SettleFunds: -1,
    InstructionType.CancelSpotOrder: -1,
    InstructionType.UpdateRootBank: -1,
    InstructionType.SettlePnl: -1,
    InstructionType.SettleBorrow: -1,
    InstructionType.ForceCancelSpotOrders: -1,
    InstructionType.ForceCancelPerpOrders: -1,
    InstructionType.LiquidateTokenAndToken: -1,
    InstructionType.LiquidateTokenAndPerp: -1,
    InstructionType.LiquidatePerpMarket: -1,
    InstructionType.SettleFees: -1,
    InstructionType.ResolvePerpBankruptcy: -1,
    InstructionType.ResolveTokenBankruptcy: -1,
    InstructionType.InitSpotOpenOrders: -1,
    InstructionType.RedeemMngo: -1,
    InstructionType.AddMangoAccountInfo: -1,
    InstructionType.DepositMsrm: -1,
    InstructionType.WithdrawMsrm: -1,
    InstructionType.ChangePerpMarketParams: -1,
    InstructionType.SetGroupAdmin: -1,
    InstructionType.CancelAllPerpOrders: -1,
    InstructionType.ForceSettleQuotePositions: -1,
    InstructionType.PlaceSpotOrder2: -1,
    InstructionType.InitAdvancedOrders: -1,
    InstructionType.AddPerpTriggerOrder: -1,
    InstructionType.RemoveAdvancedOrder: -1,
    InstructionType.ExecutePerpTriggerOrder: -1,
    InstructionType.CreatePerpMarket: -1,
    InstructionType.ChangePerpMarketParams2: -1,
    InstructionType.UpdateMarginBasket: -1,
    InstructionType.ChangeMaxMangoAccounts: -1,
    InstructionType.CloseMangoAccount: -1,
    InstructionType.CloseSpotOpenOrders: -1,
    InstructionType.CloseAdvancedOrders: -1,
    InstructionType.CreateDustAccount: -1,
    InstructionType.ResolveDust: -1,
    InstructionType.CreateMangoAccount: -1,
    InstructionType.UpgradeMangoAccountV0V1: -1,
    InstructionType.CancelPerpOrderSide: -1,
    InstructionType.SetDelegate: -1,
    InstructionType.ChangeSpotMarketParams: -1,
    InstructionType.CreateSpotOpenOrders: -1,
    InstructionType.ChangeReferralFeeParams: -1,
    InstructionType.SetReferrerMemory: -1,
    InstructionType.RegisterReferrerId: -1,
    InstructionType.PlacePerpOrder2: -1,
}


# # 🥭 MangoInstruction class
#
# This class packages up Mango instruction data, which can come from disparate parts of the
# transaction. Keeping it all together here makes many things simpler.
#
class MangoInstruction:
    def __init__(
        self,
        program_id: PublicKey,
        instruction_type: InstructionType,
        raw_data: bytes,
        instruction_data: typing.Any,
        accounts: typing.Sequence[PublicKey],
    ) -> None:
        self.program_id: PublicKey = program_id
        self.instruction_type: InstructionType = instruction_type
        self.raw_data: bytes = raw_data
        self.instruction_data: typing.Any = instruction_data
        self.accounts: typing.Sequence[PublicKey] = accounts

    @property
    def group(self) -> PublicKey:
        # Group PublicKey is always the zero index.
        return self.accounts[0]

    @property
    def sender(self) -> typing.Optional[PublicKey]:
        account_index = _instruction_signer_indices[self.instruction_type]
        if account_index < 0:
            return None
        return self.accounts[account_index]

    @property
    def token_in_account(self) -> typing.Optional[PublicKey]:
        account_index = _token_in_indices[self.instruction_type]
        if account_index < 0:
            return None
        return self.accounts[account_index]

    @property
    def token_out_account(self) -> typing.Optional[PublicKey]:
        account_index = _token_out_indices[self.instruction_type]
        if account_index < 0:
            return None
        return self.accounts[account_index]

    @property
    def target_account(self) -> typing.Optional[PublicKey]:
        account_index = _target_indices[self.instruction_type]
        if account_index < 0:
            return None
        return self.accounts[account_index]

    def describe_parameters(self) -> str:
        instruction_type = self.instruction_type
        additional_data = ""
        if instruction_type == InstructionType.InitMangoGroup:
            pass
        elif instruction_type == InstructionType.InitMarginAccount:
            pass
        elif instruction_type == InstructionType.Deposit:
            additional_data = f"quantity: {self.instruction_data.quantity}"
        elif instruction_type == InstructionType.Withdraw:
            additional_data = f"quantity: {self.instruction_data.quantity}, allow_borrow: {self.instruction_data.allow_borrow}"
        elif instruction_type == InstructionType.AddSpotMarket:
            pass
        elif instruction_type == InstructionType.AddToBasket:
            pass
        elif instruction_type == InstructionType.Borrow:
            pass
        elif instruction_type == InstructionType.CachePrices:
            pass
        elif instruction_type == InstructionType.CacheRootBanks:
            pass
        elif instruction_type == InstructionType.PlaceSpotOrder:
            additional_data = f"side: {Side.from_value(self.instruction_data.side)}, order_type: {OrderType.from_value(self.instruction_data.order_type)}, limit_price: {self.instruction_data.limit_price}, max_base_quantity: {self.instruction_data.max_base_quantity}, max_quote_quantity: {self.instruction_data.max_quote_quantity}, self_trade_behavior: {pyserum.enums.SelfTradeBehavior(self.instruction_data.self_trade_behavior).name}, client_id: {self.instruction_data.client_id}, limit: {self.instruction_data.limit}"
        elif instruction_type == InstructionType.AddOracle:
            pass
        elif instruction_type == InstructionType.AddPerpMarket:
            pass
        elif instruction_type == InstructionType.PlacePerpOrder:
            additional_data = f"side: {Side.from_value(self.instruction_data.side)}, order_type: {OrderType.from_value(self.instruction_data.order_type)}, price: {self.instruction_data.price}, quantity: {self.instruction_data.quantity}, client_order_id: {self.instruction_data.client_order_id}, reduce_only: {self.instruction_data.reduce_only}"
        elif instruction_type == InstructionType.CancelPerpOrderByClientId:
            additional_data = f"client ID: {self.instruction_data.client_order_id}, missing OK: {self.instruction_data.invalid_id_ok}"
        elif instruction_type == InstructionType.CancelPerpOrder:
            additional_data = f"order ID: {self.instruction_data.order_id}, missing OK: {self.instruction_data.invalid_id_ok}"
        elif instruction_type == InstructionType.ConsumeEvents:
            additional_data = f"limit: {self.instruction_data.limit}"
        elif instruction_type == InstructionType.CachePerpMarkets:
            pass
        elif instruction_type == InstructionType.UpdateFunding:
            pass
        elif instruction_type == InstructionType.SetOracle:
            pass
        elif instruction_type == InstructionType.SettleFunds:
            pass
        elif instruction_type == InstructionType.CancelSpotOrder:
            additional_data = f"order ID: {self.instruction_data.order_id}, side: {Side.from_value(self.instruction_data.side)}"
        elif instruction_type == InstructionType.UpdateRootBank:
            pass
        elif instruction_type == InstructionType.SettlePnl:
            pass
        elif instruction_type == InstructionType.SettleBorrow:
            pass
        elif instruction_type == InstructionType.ForceCancelSpotOrders:
            pass
        elif instruction_type == InstructionType.ForceCancelPerpOrders:
            pass
        elif instruction_type == InstructionType.LiquidateTokenAndToken:
            pass
        elif instruction_type == InstructionType.LiquidateTokenAndPerp:
            pass
        elif instruction_type == InstructionType.LiquidatePerpMarket:
            pass
        elif instruction_type == InstructionType.SettleFees:
            pass
        elif instruction_type == InstructionType.ResolvePerpBankruptcy:
            pass
        elif instruction_type == InstructionType.ResolveTokenBankruptcy:
            pass
        elif instruction_type == InstructionType.InitSpotOpenOrders:
            pass
        elif instruction_type == InstructionType.RedeemMngo:
            pass
        elif instruction_type == InstructionType.AddMangoAccountInfo:
            pass
        elif instruction_type == InstructionType.DepositMsrm:
            pass
        elif instruction_type == InstructionType.WithdrawMsrm:
            pass
        elif instruction_type == InstructionType.ChangePerpMarketParams:
            pass
        elif instruction_type == InstructionType.SetGroupAdmin:
            pass
        elif instruction_type == InstructionType.CancelAllPerpOrders:
            pass
        elif instruction_type == InstructionType.ForceSettleQuotePositions:
            pass
        elif instruction_type == InstructionType.PlaceSpotOrder2:
            additional_data = f"side: {Side.from_value(self.instruction_data.side)}, order_type: {OrderType.from_value(self.instruction_data.order_type)}, limit_price: {self.instruction_data.limit_price}, max_base_quantity: {self.instruction_data.max_base_quantity}, max_quote_quantity: {self.instruction_data.max_quote_quantity}, client_id: {self.instruction_data.client_id},  self_trade_behavior: {pyserum.enums.SelfTradeBehavior(self.instruction_data.self_trade_behavior).name}, limit: {self.instruction_data.limit}"
        elif instruction_type == InstructionType.InitAdvancedOrders:
            pass
        elif instruction_type == InstructionType.AddPerpTriggerOrder:
            pass
        elif instruction_type == InstructionType.RemoveAdvancedOrder:
            pass
        elif instruction_type == InstructionType.ExecutePerpTriggerOrder:
            pass
        elif instruction_type == InstructionType.CreatePerpMarket:
            pass
        elif instruction_type == InstructionType.ChangePerpMarketParams2:
            pass
        elif instruction_type == InstructionType.UpdateMarginBasket:
            pass
        elif instruction_type == InstructionType.ChangeMaxMangoAccounts:
            pass
        elif instruction_type == InstructionType.CloseMangoAccount:
            pass
        elif instruction_type == InstructionType.CloseSpotOpenOrders:
            pass
        elif instruction_type == InstructionType.CloseAdvancedOrders:
            pass
        elif instruction_type == InstructionType.CreateDustAccount:
            pass
        elif instruction_type == InstructionType.ResolveDust:
            pass
        elif instruction_type == InstructionType.CreateMangoAccount:
            pass
        elif instruction_type == InstructionType.UpgradeMangoAccountV0V1:
            pass
        elif instruction_type == InstructionType.CancelPerpOrderSide:
            additional_data = f"side: {Side.from_value(self.instruction_data.side)}, limit: {self.instruction_data.limit}"
        elif instruction_type == InstructionType.SetDelegate:
            pass
        elif instruction_type == InstructionType.ChangeSpotMarketParams:
            pass
        elif instruction_type == InstructionType.CreateSpotOpenOrders:
            pass
        elif instruction_type == InstructionType.ChangeReferralFeeParams:
            pass
        elif instruction_type == InstructionType.SetReferrerMemory:
            pass
        elif instruction_type == InstructionType.RegisterReferrerId:
            additional_data = f"ID: '{self.instruction_data.info}'"
        elif instruction_type == InstructionType.PlacePerpOrder2:
            additional_data = f"side: {Side.from_value(self.instruction_data.side)}, order_type: {OrderType.from_value(self.instruction_data.order_type)}, price: {self.instruction_data.price}, max_base_quantity: {self.instruction_data.max_base_quantity}, max_quote_quantity: {self.instruction_data.max_quote_quantity}, client_order_id: {self.instruction_data.client_order_id}, reduce_only: {self.instruction_data.reduce_only}, expiry_timestamp: {self.instruction_data.expiry_timestamp}, limit: {self.instruction_data.limit}"

        return additional_data

    def __str__(self) -> str:
        parameters = self.describe_parameters() or ""
        keys: typing.List[str] = []
        for index, key in enumerate(self.accounts):
            pubkey: str = str(key)
            keys += [f"    Key[{index: >2}]: {pubkey}"]
        key_details: str = "\n".join(keys)
        raw_data = "".join("{:02x}".format(x) for x in self.raw_data)
        return f"""« Mango Instruction: {self.instruction_type.name}: {parameters}
    Program ID: {self.program_id}
    Data: {raw_data}
{key_details}
»"""

    def __repr__(self) -> str:
        return f"{self}"
