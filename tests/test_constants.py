from .context import mango


# There isn't really a lot to test here that isn't just duplication so instead there are just
# a couple of checks to make sure things have loaded properly.


def test_system_program_address():
    assert str(mango.SYSTEM_PROGRAM_ADDRESS) == "11111111111111111111111111111111"


def test_mango_constants():
    mango_group = mango.MangoConstants["mainnet-beta"]
    assert mango_group is not None
    assert len(mango_group["oracles"]) > 0
