from .context import mango


def test_constructor():
    initialized: bool = True
    group: bool = True
    margin_account: bool = True
    srm_account: bool = True
    actual = mango.MangoAccountFlags(mango.Version.V1, initialized, group,
                                     margin_account, srm_account)
    assert actual is not None
    assert actual.logger is not None
    assert actual.version == mango.Version.V1
    assert actual.initialized == initialized
    assert actual.group == group
    assert actual.margin_account == margin_account
    assert actual.srm_account == srm_account

    actual2 = mango.MangoAccountFlags(mango.Version.V2, not initialized, not group,
                                      not margin_account, not srm_account)
    assert actual2 is not None
    assert actual2.logger is not None
    assert actual2.version == mango.Version.V2
    assert actual2.initialized == (not initialized)
    assert actual2.group == (not group)
    assert actual2.margin_account == (not margin_account)
    assert actual2.srm_account == (not srm_account)
