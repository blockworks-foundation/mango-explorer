from .context import mango

from decimal import Decimal
from solana.publickey import PublicKey


def context_has_default_values(ctx: mango.Context):
    assert ctx.mango_program_address == PublicKey("mv3ekLzLbnVPNxjSKvqBpU3ZeZXPQdEC3bp5MDEBG68")
    assert ctx.serum_program_address == PublicKey("9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin")
    assert ctx.group_name == "mainnet.1"
    assert ctx.group_address == PublicKey("98pjRuQjK3qA6gXts96PqZT4Ze5QmnCmt3QYjhbUSPue")
    assert ctx.gma_chunk_size == Decimal(100)
    assert ctx.gma_chunk_pause == Decimal(0)


def test_context_default_exists():
    assert mango.ContextBuilder.default() is not None


def test_context_default_values():
    context_has_default_values(mango.ContextBuilder.default())


# Need to have more than one working cluster for this test.
# def test_new_from_cluster():
#     context_has_default_values(mango.ContextBuilder.default())
#     derived = mango.ContextBuilder.default().new_from_cluster("mainnet")
#     assert derived.cluster_name == "mainnet"
#     assert derived.cluster_url == "https://solana-api.projectserum.com"
#     assert derived.mango_program_address == PublicKey("mv3ekLzLbnVPNxjSKvqBpU3ZeZXPQdEC3bp5MDEBG68")
#     assert derived.serum_program_address == PublicKey("9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin")
#     assert derived.group_name == "mainnet.0"
#     assert derived.group_address == PublicKey("98pjRuQjK3qA6gXts96PqZT4Ze5QmnCmt3QYjhbUSPue")
#     context_has_default_values(mango.ContextBuilder.default())


def test_new_from_group_name():
    context_has_default_values(mango.ContextBuilder.default())
    derived = mango.ContextBuilder.from_group_name(mango.ContextBuilder.default(), "mainnet.0")
    assert derived.mango_program_address == PublicKey("mv3ekLzLbnVPNxjSKvqBpU3ZeZXPQdEC3bp5MDEBG68")
    assert derived.serum_program_address == PublicKey("9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin")

    # Should update both of these values on new group name.
    assert derived.group_name == "mainnet.0"
    assert derived.group_address == PublicKey("4yJ2Vx3kZnmHTNCrHzdoj5nCwriF2kVhfKNvqC6gU8tr")
