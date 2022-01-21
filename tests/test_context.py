from .context import mango

from decimal import Decimal
from solana.publickey import PublicKey


def context_has_default_values(ctx: mango.Context) -> None:
    assert ctx.mango_program_address == PublicKey("mv3ekLzLbnVPNxjSKvqBpU3ZeZXPQdEC3bp5MDEBG68")
    assert ctx.serum_program_address == PublicKey("9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin")
    assert ctx.group_name == "mainnet.1"
    assert ctx.group_address == PublicKey("98pjRuQjK3qA6gXts96PqZT4Ze5QmnCmt3QYjhbUSPue")
    assert ctx.gma_chunk_size == Decimal(100)
    assert ctx.gma_chunk_pause == Decimal(0)


def test_context_default_exists() -> None:
    assert mango.ContextBuilder.default() is not None


def test_context_default_values() -> None:
    context_has_default_values(mango.ContextBuilder.default())


def test_new_from_cluster() -> None:
    context_has_default_values(mango.ContextBuilder.default())
    derived = mango.ContextBuilder.build(cluster_name="devnet")
    assert derived.client.cluster_name == "devnet"
    assert derived.client.cluster_rpc_url == "https://mango.devnet.rpcpool.com"
    assert derived.client.cluster_ws_url == "wss://mango.devnet.rpcpool.com"
    assert derived.mango_program_address == PublicKey("4skJ85cdxQAFVKbcGgfun8iZPL7BadVYXG3kGEGkufqA")
    assert derived.serum_program_address == PublicKey("DESVgJVGajEgKGXhb6XmqDHGz3VjdgP7rEVESBgxmroY")
    assert derived.group_name == "devnet.2"
    assert derived.group_address == PublicKey("Ec2enZyoC4nGpEfu2sUNAa2nUGJHWxoUWYSEJ2hNTWTA")
    context_has_default_values(mango.ContextBuilder.default())
