from .context import mango


def test_decode_binary():
    data = mango.decode_binary(["SGVsbG8gV29ybGQ=", "base64"])  # "Hello World"
    assert len(data) == 11
