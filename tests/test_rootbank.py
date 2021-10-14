from .context import mango
from .data import load_root_bank
from .fakes import fake_account_info, fake_seeded_public_key

from datetime import datetime, timezone
from decimal import Decimal
from solana.publickey import PublicKey


def test_node_bank_constructor():
    account_info = fake_account_info(fake_seeded_public_key("node bank"))
    meta_data = mango.Metadata(mango.layouts.DATA_TYPE.parse(bytearray(b'\x03')), mango.Version.V1, True)
    deposits = Decimal(1000)
    borrows = Decimal(100)
    vault = fake_seeded_public_key("vault")

    actual = mango.NodeBank(account_info, mango.Version.V1, meta_data, deposits, borrows, vault)
    assert actual is not None
    assert actual.logger is not None
    assert actual.account_info == account_info
    assert actual.address == fake_seeded_public_key("node bank")
    assert actual.meta_data == meta_data
    assert actual.meta_data.data_type == mango.layouts.DATA_TYPE.NodeBank
    assert actual.deposits == deposits
    assert actual.borrows == borrows
    assert actual.vault == fake_seeded_public_key("vault")


def test_root_bank_constructor():
    account_info = fake_account_info(fake_seeded_public_key("root bank"))
    meta_data = mango.Metadata(mango.layouts.DATA_TYPE.parse(bytearray(b'\x02')), mango.Version.V1, True)
    optimal_util = Decimal("0.7")
    optimal_rate = Decimal("0.06")
    max_rate = Decimal("1.5")
    node_bank = fake_seeded_public_key("node bank")
    deposit_index = Decimal(98765)
    borrow_index = Decimal(12345)
    timestamp = datetime.now()

    actual = mango.RootBank(account_info, mango.Version.V1, meta_data, optimal_util, optimal_rate,
                            max_rate, [node_bank], deposit_index, borrow_index, timestamp)
    assert actual is not None
    assert actual.logger is not None
    assert actual.account_info == account_info
    assert actual.address == fake_seeded_public_key("root bank")
    assert actual.meta_data == meta_data
    assert actual.meta_data.data_type == mango.layouts.DATA_TYPE.RootBank
    assert actual.optimal_util == optimal_util
    assert actual.optimal_rate == optimal_rate
    assert actual.max_rate == max_rate
    assert actual.node_banks[0] == node_bank
    assert actual.deposit_index == deposit_index
    assert actual.borrow_index == borrow_index
    assert actual.last_updated == timestamp


def test_root_bank_loaded():
    actual = load_root_bank("tests/testdata/empty/root_bank0.json")

    assert actual is not None
    assert actual.logger is not None
    assert actual.address == PublicKey("HUBX4iwWEUK5VrXXXcB7uhuKrfT4fpu2T9iZbg712JrN")
    assert actual.meta_data.version == mango.Version.V1
    assert actual.meta_data.data_type == mango.layouts.DATA_TYPE.RootBank
    assert actual.meta_data.is_initialized
    # Typescript says: 0.69999999999999928946
    assert actual.optimal_util == Decimal("0.699999999999999289457264239899814129")
    # Typescript says: 0.05999999999999872102
    assert actual.optimal_rate == Decimal("0.0599999999999987210230756318196654320")
    # Typescript says: 1.5
    assert actual.max_rate == Decimal("1.5")
    assert actual.node_banks[0] == PublicKey("J2Lmnc1e4frMnBEJARPoHtfpcohLfN67HdK1inXjTFSM")
    # Typescript says: 1000154.42276607355830719825
    assert actual.deposit_index == Decimal("1000154.42276607355830719825462438166")
    # Typescript says: 1000219.00867863010088498754
    assert actual.borrow_index == Decimal("1000219.00867863010088498754157626536")
    # Typescript says: "Mon, 04 Oct 2021 14:58:05 GMT"
    assert actual.last_updated == datetime(2021, 10, 4, 14, 58, 5, 0, timezone.utc)
