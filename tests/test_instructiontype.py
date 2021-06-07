from .context import mango


def test_instruction_type_init_mango_group():
    actual = mango.InstructionType(0)
    assert actual == mango.InstructionType.InitMangoGroup


def test_instruction_type_init_margin_account():
    actual = mango.InstructionType(1)
    assert actual == mango.InstructionType.InitMarginAccount


def test_instruction_type_deposit():
    actual = mango.InstructionType(2)
    assert actual == mango.InstructionType.Deposit


def test_instruction_type_withdraw():
    actual = mango.InstructionType(3)
    assert actual == mango.InstructionType.Withdraw


def test_instruction_type_borrow():
    actual = mango.InstructionType(4)
    assert actual == mango.InstructionType.Borrow


def test_instruction_type_settle_borrow():
    actual = mango.InstructionType(5)
    assert actual == mango.InstructionType.SettleBorrow


def test_instruction_type_liquidate():
    actual = mango.InstructionType(6)
    assert actual == mango.InstructionType.Liquidate


def test_instruction_type_deposit_srm():
    actual = mango.InstructionType(7)
    assert actual == mango.InstructionType.DepositSrm


def test_instruction_type_withdraw_srm():
    actual = mango.InstructionType(8)
    assert actual == mango.InstructionType.WithdrawSrm


def test_instruction_type_place_order():
    actual = mango.InstructionType(9)
    assert actual == mango.InstructionType.PlaceOrder


def test_instruction_type_settle_funds():
    actual = mango.InstructionType(10)
    assert actual == mango.InstructionType.SettleFunds


def test_instruction_type_cancel_funds():
    actual = mango.InstructionType(11)
    assert actual == mango.InstructionType.CancelOrder


def test_instruction_type_cancel_order_by_client_id():
    actual = mango.InstructionType(12)
    assert actual == mango.InstructionType.CancelOrderByClientId


def test_instruction_type_change_borrow_limit():
    actual = mango.InstructionType(13)
    assert actual == mango.InstructionType.ChangeBorrowLimit


def test_instruction_type_place_and_settle():
    actual = mango.InstructionType(14)
    assert actual == mango.InstructionType.PlaceAndSettle


def test_instruction_type_force_cancel_orders():
    actual = mango.InstructionType(15)
    assert actual == mango.InstructionType.ForceCancelOrders


def test_instruction_type_partial_liquidate():
    actual = mango.InstructionType(16)
    assert actual == mango.InstructionType.PartialLiquidate
