from .context import mango

from decimal import Decimal
from solana.publickey import PublicKey


def test_constructor() -> None:
    address: PublicKey = PublicKey("11111111111111111111111111111118")
    executable: bool = False
    lamports: Decimal = Decimal(12345)
    owner: PublicKey = PublicKey("11111111111111111111111111111119")
    rent_epoch: Decimal = Decimal(250)
    data: bytes = bytes([1, 2, 3])
    actual = mango.AccountInfo(address, executable, lamports, owner, rent_epoch, data)
    assert actual is not None
    assert actual.address == address
    assert actual.executable == executable
    assert actual.lamports == lamports
    assert actual.sols == Decimal("0.000012345")
    assert actual.owner == owner
    assert actual.rent_epoch == rent_epoch
    assert actual.data == data


def test_split_list_into_chunks() -> None:
    list_to_split = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
    split_3 = mango.AccountInfo._split_list_into_chunks(list_to_split, 3)
    assert len(split_3) == 4
    assert split_3[0] == ["a", "b", "c"]
    assert split_3[1] == ["d", "e", "f"]
    assert split_3[2] == ["g", "h", "i"]
    assert split_3[3] == ["j"]
    split_2 = mango.AccountInfo._split_list_into_chunks(list_to_split, 2)
    assert len(split_2) == 5
    assert split_2[0] == ["a", "b"]
    assert split_2[1] == ["c", "d"]
    assert split_2[2] == ["e", "f"]
    assert split_2[3] == ["g", "h"]
    assert split_2[4] == ["i", "j"]
    split_20 = mango.AccountInfo._split_list_into_chunks(list_to_split, 20)
    assert len(split_20) == 1
    assert split_20[0] == ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
