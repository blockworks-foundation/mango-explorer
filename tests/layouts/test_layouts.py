from decimal import Decimal
from solana.publickey import PublicKey

import base64

import mango.layouts as layouts


def test_3_group_layout():
    encoded_3_token_group = "AwAAAAAAAACCaOmpoURMK6XHelGTaFawcuQ/78/15LAemWI8jrt3SRKLy2R9i60eclDjuDS8+p/ZhvTUd9G7uQVOYCsR6+BhmqGCiO6EPYP2PQkf/VRTvw7JjXvIjPFJy06QR1Cq1WfTonHl0OjCkyEf60SD07+MFJu5pVWNFGGEO/8AiAYfduaKdnFTaZEHPcK5Eq72WWHeHg2yIbBF09kyeOhlCJwOoG8O5SgpPV8QOA64ZNV4aKroFfADg6kEy/wWCdp3fv0O4GJgAAAAAPH6Ud6jtjwAAQAAAAAAAADiDkkCi9UOAAEAAAAAAAAADuBiYAAAAACNS5bSy7soAAEAAAAAAAAACMvgO+2jCwABAAAAAAAAAA7gYmAAAAAAZFeDUBNVhwABAAAAAAAAABtRNytozC8AAQAAAAAAAABIBGiCcyaEZdNhrTyeqUY692vOzzPdHaxAxguht3JQGlkzjtd05dX9LENHkl2z1XvUbTNKZlweypNRetmH0lmQ9VYQAHqylxZVK65gEg85g27YuSyvOBZAjJyRmYU9KdCO1D+4ehdPu9dQB1yI1uh75wShdAaFn2o4qrMYwq3SQQEAAAAAAAAAAiH1PPJKAuh6oGiE35aGhUQhFi/bxgKOudpFv8HEHNCFDy1uAqR6+CTQmradxC1wyyjL+iSft+5XudJWwSdi7wvphsxb96x7Obj/AgAAAAAKlV4LL5ow6r9LMhIAAAAADvsOtqcVFmChDPzPnwAAAE33lx1h8hPFD04AAAAAAAA8YRV3Oa309B2wGwAAAAAA+yPBZRlZz7b605n+AQAAAACgmZmZmZkZAQAAAAAAAAAAMDMzMzMzMwEAAAAAAAAA25D1XcAtRzSuuyx3U+X7aE9vM1EJySU9KprgL0LMJ/vat9+SEEUZuga7O5tTUrcMDYWDg+LYaAWhSQiN2fYk7aCGAQAAAAAAgIQeAAAAAAAA8gUqAQAAAAYGBgICAAAA"
    decoded_3_token_group = base64.b64decode(encoded_3_token_group)

    group = layouts.GROUP_V1.parse(decoded_3_token_group)

    # Not an exhaustive check, just a few key areas
    assert len(group.tokens) == 3
    assert group.tokens[0] == PublicKey("9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E")
    assert group.tokens[1] == PublicKey("2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk")
    assert group.tokens[2] == PublicKey("BQcdHdAQW1hczDbBi9hiegXAR7A98Q9jx3X3iBBBDiq4")

    assert len(group.vaults) == 3
    assert group.vaults[0] == PublicKey("FF8h6eCSqoGQyuYmh3BzxdaTfomCBPrCctRq9Yo6nCcd")
    assert group.vaults[1] == PublicKey("GWwECYXmTUumcUsjbwdJDc9ws4KDWYBJ1GGmckZr2hTK")
    assert group.vaults[2] == PublicKey("BoGTDjtbEtK8HPCu2VPNJfA7bTLuVDPETDoHvztm6Mqe")

    assert len(group.total_deposits) == 3
    assert group.total_deposits[0] == Decimal("50313273.4831080054396143109020182738")
    assert group.total_deposits[1] == Decimal("305286079.914804111943676127025916467")
    assert group.total_deposits[2] == Decimal("686389202081.375336984105214031197210")


def test_5_group_layout():
    encoded_5_token_group = "AwAAAAAAAACk6bHzfLvX/YZNskK+2brLGvXTPR3P4qF2Hkc2HZANL3QVQJS5HzYh3sTbcf99JgISg7g07yK6MxP5nzzTyEy8BpuIV/6rgYT7aH9jRhjANdrEOdwa6ztVmKDwAAAAAAF6mkC+0kyNlxFPeKUyBpYL11A4a/pUcOYunlw92EFaYV3OcRQkdPidUvY2YtaR52uqW752f+Ufcci7ei8SWZYWgwYD6XWYDToBxFf2L2JoXCKqjFDfQ8+dfYUGnLBupwJdSa0UH20tWtHJh6VlhzFcMCQSU8LYiS6z6cR/GWXcWKd36DfFLhkULOxma3DDEBmYIqDsEZC02N3Vm5lJSc+okeVxcJzdQ48XVJuyTEli9TP2HAbrNqFJSyFbQo0f+dKsTopavA5ndrNOk9So4ANgHdwBGUVGY0SLS7+TVXkcCgwgqGAAAAAALYxEAuIBAAABAAAAAAAAAErLeL8QAAAAAQAAAAAAAAAMIKhgAAAAACwC4BEHAAAAAQAAAAAAAACByD0AAAAAAAEAAAAAAAAADCCoYAAAAABJpmxt87MCAAEAAAAAAAAArwaaHqGSAgABAAAAAAAAAAwgqGAAAAAANHqKx8PiAwABAAAAAAAAACyFpt5myQMAAQAAAAAAAAAMIKhgAAAAAIrCIhLj2gUAAQAAAAAAAACd0UEiFPsAAAEAAAAAAAAATVH2gvK/JiB7fCRmoBvLuTcba2/qHCRnzOjDFFYNStgzmK/Q8Wk0MLLXAIvgBrVJW1RiSvwiqrTezEkb3zUF4m47JYDk9DZOvmCGR63JwGv8BXI/DLCdMIagQ6MUC4krqaznZiQhDOVuXXpiS+7Q4PgE8V9wkGVQHFpDgVQVx6VSNqBWdfB5O0wXcsXSAxviIZnpzZb8yVPAJhqxFNViEC+Y1L1+ULx6KHTSRIwn5wXTktPuZEsRtSpUJpqZD9V5y+8i6KVSbQNBUDzf0xeAFH85lOlowgaoBW/MjycjsrXlD0s7jbPTK2SvlK0fgerysq1O8y7bk5yp6001Zr/sLAEAAAAAAAAAkE0bF+zrix2vIYYIDbjjQiF/B5h1fwDNpfltVuG2QD61vZ7LZ502Gt8wb/WL0dyrOS4eySbPnOiFlVUBjsVtHweAuy088r4ZtPPGxCoAAABG2qkYb53x/zKdhfmqjgMA+NOnThFN5Rte4iNxcwIAACjnpx/Yisq5DiDQQgAAAAAGSKNb2bYXz1S4odlZDwAAxfiZZdXRLGMAAAAAAAAAALNmZBB7GyHIDgAAAAAAAABPGsO1PmFjqp3jcQAAAAAAil3Lhe3fP1HPAgAAAAAAANnFw5TROkYQ1B82OwkAAAAAoJmZmZmZGQEAAAAAAAAAADAzMzMzMzMBAAAAAAAAAIOo484GpuWM2iV176h0nKGu2lHIio/GeSYKkkptjxvYBpU3RtcibIXhdSaNSvboTLAKz91Es3OeaoUjHgSxfAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACQkJBgYCAgICAAAAAAAAAA=="
    decoded_5_token_group = base64.b64decode(encoded_5_token_group)

    group = layouts.GROUP_V2.parse(decoded_5_token_group)

    # Not an exhaustive check, just a few key areas
    assert len(group.tokens) == 5
    assert group.tokens[0] == PublicKey("C6kYXcaRUMqeBF5fhg165RWU7AnpT9z92fvKNoMqjmz6")
    assert group.tokens[1] == PublicKey("8p968u9m7jZzKSsqxFDqki69MjqdFkwPM9FN4AN8hvHR")
    assert group.tokens[2] == PublicKey("So11111111111111111111111111111111111111112")
    assert group.tokens[3] == PublicKey("9FbAMDvXqNjPqZSYt4EWTguJuDrGkfvwr3gSFpiSbX9S")
    assert group.tokens[4] == PublicKey("7KBVenLz5WNH4PA5MdGkJNpDDyNKnBQTwnz1UqJv9GUm")

    assert len(group.vaults) == 5
    assert group.vaults[0] == PublicKey("9pTjFBB3xheuqR9iDG63x2TLZjeb6f3yCBZE6EjYtqV3")
    assert group.vaults[1] == PublicKey("7HA5Ne1g2t8cRvzEYdoMwGJch1AneMQLiJRJccm1tw9y")
    assert group.vaults[2] == PublicKey("CGj8exjKg88byyjRCEuYGB5CXvAqB1YzHEHrDiUFLwYK")
    assert group.vaults[3] == PublicKey("ApX38vWvRybQHKoj6AsQHQDa7gQPChYkNHgqAj2kDxDo")
    assert group.vaults[4] == PublicKey("CbcaxuYfe53NTX5eRUaRzxGyRyMLTt7JT6p2p6VZVnh7")

    assert len(group.total_deposits) == 5
    assert group.total_deposits[0] == Decimal("183689999284.100569858257342659537455")
    assert group.total_deposits[1] == Decimal("1001289911999794.99978050195992499251")
    assert group.total_deposits[2] == Decimal("2694842671710.10896760628261797877389")
    assert group.total_deposits[3] == Decimal("1120935950.72574680115181388001879825")
    assert group.total_deposits[4] == Decimal("16878577760340.8089556008013804037004")
