from .context import mango

from solana.publickey import PublicKey


def context_has_default_values(ctx):
    assert ctx.cluster == "mainnet-beta"
    assert ctx.cluster_url == "https://solana-api.projectserum.com"
    assert ctx.program_id == PublicKey("JD3bq9hGdy38PuWQ4h2YJpELmHVGPPfFSuFkpzAd9zfu")
    assert ctx.dex_program_id == PublicKey("9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin")
    assert ctx.group_name == "BTC_ETH_USDT"
    assert ctx.group_id == PublicKey("7pVYhpKUHw88neQHxgExSH6cerMZ1Axx1ALQP9sxtvQV")


def test_default_context_exists():
    assert mango.default_context is not None


def test_default_context_values():
    context_has_default_values(mango.default_context)


def test_new_from_cluster():
    context_has_default_values(mango.default_context)
    derived = mango.default_context.new_from_cluster("devnet")
    assert derived.cluster == "devnet"
    assert derived.cluster_url == "https://devnet.solana.com"
    assert derived.program_id == PublicKey("9XzhtAtDXxW2rjbeVFhTq4fnhD8dqzr154r5b2z6pxEp")
    assert derived.dex_program_id == PublicKey("DESVgJVGajEgKGXhb6XmqDHGz3VjdgP7rEVESBgxmroY")
    assert derived.group_name == "BTC_ETH_USDT"
    assert derived.group_id == PublicKey("2PUXjaYb9XHP6fBLrbz12jFDinzUcQuz7jWu8v2VLTNm")
    context_has_default_values(mango.default_context)


def test_new_from_cluster_url():
    context_has_default_values(mango.default_context)
    derived = mango.default_context.new_from_cluster_url("https://some-dev-host")
    assert derived.cluster == "mainnet-beta"
    assert derived.cluster_url == "https://some-dev-host"
    assert derived.program_id == PublicKey("JD3bq9hGdy38PuWQ4h2YJpELmHVGPPfFSuFkpzAd9zfu")
    assert derived.dex_program_id == PublicKey("9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin")
    assert derived.group_name == "BTC_ETH_USDT"
    assert derived.group_id == PublicKey("7pVYhpKUHw88neQHxgExSH6cerMZ1Axx1ALQP9sxtvQV")
    context_has_default_values(mango.default_context)


def test_new_from_group_name():
    context_has_default_values(mango.default_context)
    derived = mango.default_context.new_from_group_name("BTC_ETH_SOL_SRM_USDC")
    assert derived.cluster == "mainnet-beta"
    assert derived.cluster_url == "https://solana-api.projectserum.com"
    assert derived.program_id == PublicKey("JD3bq9hGdy38PuWQ4h2YJpELmHVGPPfFSuFkpzAd9zfu")
    assert derived.dex_program_id == PublicKey("9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin")

    # Should update both of these values on new group name.
    assert derived.group_name == "BTC_ETH_SOL_SRM_USDC"
    assert derived.group_id == PublicKey("2oogpTYm1sp6LPZAWD3bp2wsFpnV2kXL1s52yyFhW5vp")
    context_has_default_values(mango.default_context)


def test_new_from_group_id():
    context_has_default_values(mango.default_context)
    derived = mango.default_context.new_from_group_id(PublicKey("2oogpTYm1sp6LPZAWD3bp2wsFpnV2kXL1s52yyFhW5vp"))
    assert derived.cluster == "mainnet-beta"
    assert derived.cluster_url == "https://solana-api.projectserum.com"
    assert derived.program_id == PublicKey("JD3bq9hGdy38PuWQ4h2YJpELmHVGPPfFSuFkpzAd9zfu")
    assert derived.dex_program_id == PublicKey("9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin")

    # Should update both of these values on new group ID.
    assert derived.group_name == "BTC_ETH_SOL_SRM_USDC"
    assert derived.group_id == PublicKey("2oogpTYm1sp6LPZAWD3bp2wsFpnV2kXL1s52yyFhW5vp")
    context_has_default_values(mango.default_context)


def test_solana_context_exists():
    assert mango.solana_context is not None


def test_serum_context_exists():
    assert mango.serum_context is not None


def test_rpcpool_context_exists():
    assert mango.rpcpool_context is not None
