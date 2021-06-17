from .context import mango
from .fakes import fake_account_info, fake_context, fake_seeded_public_key, fake_token

from decimal import Decimal

import base64


def test_construction():
    account_info = fake_account_info()
    name = "FAKE_GROUP"
    account_flags = mango.MangoAccountFlags(mango.Version.V1, True, False, True, False)
    basket_tokens = [fake_token(), fake_token(), fake_token()]
    markets = []
    signer_nonce = Decimal(1)
    signer_key = fake_seeded_public_key("signer key")
    dex_program_id = fake_seeded_public_key("DEX program ID")
    total_deposits = [Decimal(1), Decimal(2), Decimal(3)]
    total_borrows = [Decimal(0), Decimal(1), Decimal(2)]
    maint_coll_ratio = Decimal("1.1")
    init_coll_ratio = Decimal("1.2")
    srm_vault = fake_seeded_public_key("SRM vault")
    admin = fake_seeded_public_key("admin")
    borrow_limits = [Decimal(5), Decimal(7), Decimal(2)]

    actual = mango.Group(account_info, mango.Version.V1, name, account_flags,
                         basket_tokens, markets, signer_nonce, signer_key, dex_program_id,
                         total_deposits, total_borrows, maint_coll_ratio, init_coll_ratio,
                         srm_vault, admin, borrow_limits)

    assert actual is not None
    assert actual.logger is not None
    assert actual.name == name
    assert actual.account_flags == account_flags
    assert actual.basket_tokens == basket_tokens
    assert actual.markets == markets
    assert actual.signer_nonce == signer_nonce
    assert actual.signer_key == signer_key
    assert actual.dex_program_id == dex_program_id
    assert actual.total_deposits == total_deposits
    assert actual.total_borrows == total_borrows
    assert actual.maint_coll_ratio == maint_coll_ratio
    assert actual.init_coll_ratio == init_coll_ratio
    assert actual.srm_vault == srm_vault
    assert actual.admin == admin
    assert actual.borrow_limits == borrow_limits


def test_group3_parse():
    # Data for group BTC_ETH_USDT
    group_3_public_key = fake_seeded_public_key("group3")
    owner_3_public_key = fake_seeded_public_key("owner3")
    encoded_3 = "AwAAAAAAAACCaOmpoURMK6XHelGTaFawcuQ/78/15LAemWI8jrt3SRKLy2R9i60eclDjuDS8+p/ZhvTUd9G7uQVOYCsR6+BhzgEOYK/tsicXvWMZL1QUWj+WWjO7gtLHAp6yzh4ggmR5TYxOe+df4LNiUJGSedvZ1K+r6GIzQEosNxNHhh2V7yAW8uStEyfEUTbEEkKgyDlUOVRWgGFbsiOC/Uzmn5ghfd2vMNvykHBB4JNMAUG0WhTyCizezFE3eOWvscJG7VWUUa5gAAAAAO1Ih8hkuwwAAQAAAAAAAADCuVoJcm8AAAEAAAAAAAAAlFGuYAAAAAAq17B5bBMDAAEAAAAAAAAAmLhxEVn+//8AAAAAAAAAAJRRrmAAAAAA+TEN0IhNFAIBAAAAAAAAAOiJg4cDQlkAAQAAAAAAAACjgEchygfXnwdEo4sw2++jvroovFb2BReD7MwO2ycvyWJ1ExP6tUyAXZHgwFt800+q+x6ZXzsCtRysH3ay+vKU9VYQAHqylxZVK65gEg85g27YuSyvOBZAjJyRmYU9KdCO1D+4ehdPu9dQB1yI1uh75wShdAaFn2o4qrMYwq3SQQIAAAAAAAAAT1DEK0hxpSv5VHH5kTlWeJePlGQpPYZ+uqcUELR4sLKFDy1uAqR6+CTQmradxC1wyyjL+iSft+5XudJWwSdi78PjPEJTOBGbyhEgBwAAAAD1dEYfuWMjjZ/rgK0AAAAAnKsRD43mpS3XCLztBAUAAKp2XItMhJ/N4sYBAAAAAABTEKVFyYfPc+mmjQAAAAAAWCug5qta1bqvFvY5uAAAAACgmZmZmZkZAQAAAAAAAAAAMDMzMzMzMwEAAAAAAAAAS153X9szDlbg9dv9VWFE+e6Hzhj8N5Of9zJLVkbx/U3at9+SEEUZuga7O5tTUrcMDYWDg+LYaAWhSQiN2fYk7UBCDwAAAAAAgI1bAAAAAAAAdDukCwAAAAYGBgICAAAA"
    decoded_3 = base64.b64decode(encoded_3)
    group_3_account_info = fake_account_info(address=group_3_public_key, owner=owner_3_public_key, data=decoded_3)
    group_3 = mango.Group.parse(fake_context(), group_3_account_info)
    assert group_3.address == group_3_public_key


def test_group5_parse():
    # Data for group BTC_ETH_SOL_SRM_USDC
    # We need to be a little more involved in creating the Context here.
    group_5_context = mango.Context(cluster="test",
                                    cluster_url="http://localhost",
                                    program_id=fake_seeded_public_key("program ID"),
                                    dex_program_id=fake_seeded_public_key("DEX program ID"),
                                    group_name="BTC_ETH_SOL_SRM_USDC",
                                    group_id=fake_seeded_public_key("group ID"))
    group_5_public_key = fake_seeded_public_key("group5")
    owner_5_public_key = fake_seeded_public_key("owner5")
    encoded_5 = "AwAAAAAAAACCaOmpoURMK6XHelGTaFawcuQ/78/15LAemWI8jrt3SRKLy2R9i60eclDjuDS8+p/ZhvTUd9G7uQVOYCsR6+BhBpuIV/6rgYT7aH9jRhjANdrEOdwa6ztVmKDwAAAAAAEGgxCGGpgyfQVQV02EQYqm4QwzUt2qf9f1gVLM7rI4h8b6evO+2606PWXzaqvJdDGxu+TC0vbg5HymAgNFL11hDMpGlEl+w4+GTcSIxBgL21a381cY189pDZlNnJs4yeZo9SkiFPWIiqiO2WDuvWSwJtkzGT2AyosXbQAxoertF39z/OIM0RaqoX0m/ygot2ZFTFO709eZT8FMhrd6JbCWncHjVmiq7bm5jp3hx5bGZK9TJQh8fiOUaZqKsEnbvv2kh1ev9CnkA2y5WuIKYi7x4xgW5qI0rSiXLyQt2ih2OFbht2AAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAQAAAAAAAACqqrZgAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAVuG3YAAAAADu/h/j7AEAAAEAAAAAAAAAOTC1S6QAAAABAAAAAAAAAGvPt2AAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAQAAAAAAAABW4bdgAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAh6eVoSNiIJyPgV+TTHYeuVF9BY6e+SWFq+rlAay+FQY5wP5yG8+DquGM1xrK84Afdgb2FpOOvSfIrnYyhDEpNITC+xiu1hn1RmMmU+8GAp8CqGS/OCmGcYG7IN8dcVwwowmj13Uh9wkF+yqInUo8aluBd5TeyepC6vUuYKD3Pe/1VhAAerKXFlUrrmASDzmDbti5LK84FkCMnJGZhT0p0I7UP7h6F0+711AHXIjW6HvnBKF0BoWfajiqsxjCrdJBlCNajxBr0p+Nz8IPWfXR0m64sDFoIgeYv6BNfv0ZV4dafre5nIqEzPfWXGEWbQEAOFBe5S6+0UIkeaoE8kdnAwAAAAAAAAAADUJgR5d1JfsqikNyo9yTAa1U8KuCHb6XNmKlZ4hG4TmFDy1uAqR6+CTQmradxC1wyyjL+iSft+5XudJWwSdi7wAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOMVOUDhnHRrc3hIGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAKCGAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAoJmZmZmZGQEAAAAAAAAAADAzMzMzMzMBAAAAAAAAAJ3B41Zoqu25uY6d4ceWxmSvUyUIfH4jlGmairBJ27792rffkhBFGboGuzubU1K3DA2Fg4Pi2GgFoUkIjdn2JO0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABgYJBgYCAgICAAAAAAAAAA=="
    decoded_5 = base64.b64decode(encoded_5)
    group_5_account_info = fake_account_info(address=group_5_public_key, owner=owner_5_public_key, data=decoded_5)
    group_5 = mango.Group.parse(group_5_context, group_5_account_info)
    assert group_5.address == group_5_public_key
