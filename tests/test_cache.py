from .context import mango
from .fakes import fake_account_info, fake_seeded_public_key
from .data import load_cache

from datetime import datetime
from decimal import Decimal


def test_cache_constructor():
    account_info = fake_account_info(fake_seeded_public_key("cache"))
    meta_data = mango.Metadata(mango.layouts.DATA_TYPE.parse(bytearray(b'\x07')), mango.Version.V1, True)
    timestamp = datetime.now()
    price_cache = [mango.PriceCache(Decimal(26), timestamp)]
    root_bank_cache = [mango.RootBankCache(Decimal("0.00001"), Decimal("0.00001"), timestamp)]
    perp_market_cache = [mango.PerpMarketCache(Decimal("0.00002"), Decimal("0.00002"), timestamp)]
    actual = mango.Cache(account_info, mango.Version.V1, meta_data, price_cache, root_bank_cache, perp_market_cache)

    assert actual is not None
    assert actual.logger is not None
    assert actual.account_info == account_info
    assert actual.address == fake_seeded_public_key("cache")
    assert actual.meta_data == meta_data
    assert actual.meta_data.data_type == mango.layouts.DATA_TYPE.Cache
    assert actual.price_cache == price_cache
    assert actual.root_bank_cache == root_bank_cache
    assert actual.perp_market_cache == perp_market_cache


def test_load_cache():
    cache = load_cache("tests/testdata/1deposit/cache.json")

    #
    # These values are all verified with the same file loaded in the TypeScript client.
    #

    assert cache.price_cache[0].price == Decimal("0.33642499999999841975")
    assert cache.price_cache[1].price == Decimal("47380.32499999999999928946")
    assert cache.price_cache[2].price == Decimal("3309.69549999999999911893")
    assert cache.price_cache[3].price == Decimal("0.17261599999999788224")
    assert cache.price_cache[4].price == Decimal("8.79379999999999739657")
    assert cache.price_cache[5].price == Decimal("1")
    assert cache.price_cache[6].price == Decimal("1.00039999999999906777")
    assert cache.price_cache[7] is None
    assert cache.price_cache[8] is None
    assert cache.price_cache[9] is None
    assert cache.price_cache[10] is None
    assert cache.price_cache[11] is None
    assert cache.price_cache[12] is None
    assert cache.price_cache[13] is None
    assert cache.price_cache[14] is None

    assert cache.root_bank_cache[0].deposit_index == Decimal("1001923.86460821722014813417")
    assert cache.root_bank_cache[0].borrow_index == Decimal("1002515.45257855337824182129")
    assert cache.root_bank_cache[1].deposit_index == Decimal("1000007.37249653914441083202")
    assert cache.root_bank_cache[1].borrow_index == Decimal("1000166.98522159213999316307")
    assert cache.root_bank_cache[2].deposit_index == Decimal("1000000.19554886875829424753")
    assert cache.root_bank_cache[2].borrow_index == Decimal("1000001.13273253565107623331")
    assert cache.root_bank_cache[3].deposit_index == Decimal("1000037.82149923799070379005")
    assert cache.root_bank_cache[3].borrow_index == Decimal("1000044.28925241010965052624")
    assert cache.root_bank_cache[4].deposit_index == Decimal("1000000.0000132182767842437")
    assert cache.root_bank_cache[4].borrow_index == Decimal("1000000.14235973938041368569")
    assert cache.root_bank_cache[5].deposit_index == Decimal("1000000.35244386506945346582")
    assert cache.root_bank_cache[5].borrow_index == Decimal("1000000.66156146420993522383")
    assert cache.root_bank_cache[6].deposit_index == Decimal("1000473.25161608998580575758")
    assert cache.root_bank_cache[6].borrow_index == Decimal("1000524.37279217702128875089")
    assert cache.root_bank_cache[7] is None
    assert cache.root_bank_cache[7] is None
    assert cache.root_bank_cache[8] is None
    assert cache.root_bank_cache[8] is None
    assert cache.root_bank_cache[9] is None
    assert cache.root_bank_cache[9] is None
    assert cache.root_bank_cache[10] is None
    assert cache.root_bank_cache[10] is None
    assert cache.root_bank_cache[11] is None
    assert cache.root_bank_cache[11] is None
    assert cache.root_bank_cache[12] is None
    assert cache.root_bank_cache[12] is None
    assert cache.root_bank_cache[13] is None
    assert cache.root_bank_cache[13] is None
    assert cache.root_bank_cache[14] is None
    assert cache.root_bank_cache[14] is None
    assert cache.root_bank_cache[15].deposit_index == Decimal("1000154.42276607534055088422")
    assert cache.root_bank_cache[15].borrow_index == Decimal("1000219.00868743509063563124")

    assert cache.perp_market_cache[0] is None
    assert cache.perp_market_cache[1].long_funding == Decimal("-751864.70031280454435673732")
    assert cache.perp_market_cache[1].short_funding == Decimal("-752275.3557979761382519257")
    assert cache.perp_market_cache[2].long_funding == Decimal("0")
    assert cache.perp_market_cache[2].short_funding == Decimal("0")
    assert cache.perp_market_cache[3].long_funding == Decimal("-636425.51790158202868497028")
    assert cache.perp_market_cache[3].short_funding == Decimal("-636425.51790158202868497028")
    assert cache.perp_market_cache[4] is None
    assert cache.perp_market_cache[5] is None
    assert cache.perp_market_cache[6] is None
    assert cache.perp_market_cache[7] is None
    assert cache.perp_market_cache[8] is None
    assert cache.perp_market_cache[9] is None
    assert cache.perp_market_cache[10] is None
    assert cache.perp_market_cache[11] is None
    assert cache.perp_market_cache[12] is None
    assert cache.perp_market_cache[13] is None
    assert cache.perp_market_cache[14] is None
