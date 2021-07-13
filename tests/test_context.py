from .context import mango

from solana.publickey import PublicKey


def context_has_default_values(ctx):
    assert ctx.cluster == "devnet"
    assert ctx.cluster_url == "https://api.devnet.solana.com"
    assert ctx.program_id == PublicKey("32WeJ46tuY6QEkgydqzHYU5j85UT9m1cPJwFxPjuSVCt")
    assert ctx.dex_program_id == PublicKey("DESVgJVGajEgKGXhb6XmqDHGz3VjdgP7rEVESBgxmroY")
    assert ctx.group_name == "mango_test_v3.4"
    assert ctx.group_id == PublicKey("CNd6bmeM1q7yS1C54xwT4fKpF3EquLWhFmF9xVweGjrM")


def test_context_default_exists():
    assert mango.Context.default() is not None


def test_context_default_values():
    context_has_default_values(mango.Context.default())


# Need to have more than one working cluster for this test.
# def test_new_from_cluster():
#     context_has_default_values(mango.Context.default())
#     derived = mango.Context.default().new_from_cluster("mainnet-beta")
#     assert derived.cluster == "mainnet-beta"
#     assert derived.cluster_url == "https://solana-api.projectserum.com"
#     assert derived.program_id == PublicKey("32WeJ46tuY6QEkgydqzHYU5j85UT9m1cPJwFxPjuSVCt")
#     assert derived.dex_program_id == PublicKey("DESVgJVGajEgKGXhb6XmqDHGz3VjdgP7rEVESBgxmroY")
#     assert derived.group_name == "mango_test_v3.4"
#     assert derived.group_id == PublicKey("CNd6bmeM1q7yS1C54xwT4fKpF3EquLWhFmF9xVweGjrM")
#     context_has_default_values(mango.Context.default())


def test_new_from_cluster_url():
    context_has_default_values(mango.Context.default())
    derived = mango.Context.default().new_from_cluster_url("https://some-dev-host")
    assert derived.cluster == "devnet"
    assert derived.cluster_url == "https://some-dev-host"
    assert derived.program_id == PublicKey("32WeJ46tuY6QEkgydqzHYU5j85UT9m1cPJwFxPjuSVCt")
    assert derived.dex_program_id == PublicKey("DESVgJVGajEgKGXhb6XmqDHGz3VjdgP7rEVESBgxmroY")
    assert derived.group_name == "mango_test_v3.4"
    assert derived.group_id == PublicKey("CNd6bmeM1q7yS1C54xwT4fKpF3EquLWhFmF9xVweGjrM")
    context_has_default_values(mango.Context.default())


def test_new_from_group_name():
    context_has_default_values(mango.Context.default())
    derived = mango.Context.default().new_from_group_name("mango_test_v3.4")
    assert derived.cluster == "devnet"
    assert derived.cluster_url == "https://api.devnet.solana.com"
    assert derived.program_id == PublicKey("32WeJ46tuY6QEkgydqzHYU5j85UT9m1cPJwFxPjuSVCt")
    assert derived.dex_program_id == PublicKey("DESVgJVGajEgKGXhb6XmqDHGz3VjdgP7rEVESBgxmroY")

    # Should update both of these values on new group name.
    assert derived.group_name == "mango_test_v3.4"
    assert derived.group_id == PublicKey("CNd6bmeM1q7yS1C54xwT4fKpF3EquLWhFmF9xVweGjrM")
    context_has_default_values(mango.Context.default())


def test_new_from_group_id():
    context_has_default_values(mango.Context.default())
    derived = mango.Context.default().new_from_group_id(PublicKey("CNd6bmeM1q7yS1C54xwT4fKpF3EquLWhFmF9xVweGjrM"))
    assert derived.cluster == "devnet"
    assert derived.cluster_url == "https://api.devnet.solana.com"
    assert derived.program_id == PublicKey("32WeJ46tuY6QEkgydqzHYU5j85UT9m1cPJwFxPjuSVCt")
    assert derived.dex_program_id == PublicKey("DESVgJVGajEgKGXhb6XmqDHGz3VjdgP7rEVESBgxmroY")

    # Should update both of these values on new group ID.
    assert derived.group_name == "mango_test_v3.4"
    assert derived.group_id == PublicKey("CNd6bmeM1q7yS1C54xwT4fKpF3EquLWhFmF9xVweGjrM")
    context_has_default_values(mango.Context.default())
