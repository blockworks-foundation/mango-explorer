from .context import mango


def test_no_messages_to_expand() -> None:
    # https://explorer.solana.com/tx/5pJMY9JFbFDMGU4EUhR3oqxDfyGqEpj9hcrMmux5QLQKysdhy1F2qfpckqm2Sg9hLxnkwpRsL2K6z2bSq2Wpn5mZ?cluster=devnet
    logs = [
        "Program 4skJ85cdxQAFVKbcGgfun8iZPL7BadVYXG3kGEGkufqA invoke [1]",
        "Program log: Mango: PlaceSpotOrder2",
        "Program DESVgJVGajEgKGXhb6XmqDHGz3VjdgP7rEVESBgxmroY invoke [2]",
        "Program DESVgJVGajEgKGXhb6XmqDHGz3VjdgP7rEVESBgxmroY consumed 8858 of 171625 compute units",
        "Program DESVgJVGajEgKGXhb6XmqDHGz3VjdgP7rEVESBgxmroY failed: custom program error: 0x2a",
        "Program 4skJ85cdxQAFVKbcGgfun8iZPL7BadVYXG3kGEGkufqA consumed 200000 of 200000 compute units",
        "Program 4skJ85cdxQAFVKbcGgfun8iZPL7BadVYXG3kGEGkufqA failed: custom program error: 0x2a",
    ]
    actual = mango.expand_log_messages(logs)
    assert len(actual) == 7
    assert actual == logs  # Should be no change to messages


def test_expand_liquidate_perp_market() -> None:
    # https://explorer.solana.com/tx/5QXc2ssJASwwtd3THxo2d8sYMArR485oGB3k2B8QgDK1haP6W5Vii74JkC9GoEJv2aMNh7GmoQ2yHA4EZWGxAUWr?cluster=devnet
    logs = [
        "Program 4skJ85cdxQAFVKbcGgfun8iZPL7BadVYXG3kGEGkufqA invoke [1]",
        "Program log: Mango: LiquidatePerpMarket",
        "Program log: mango-log",
        "Program log: xL0/TYaKkmo9V1sXbGlWtx7PorbATlnhud1k4TouaelSIuWjq6DS+naor4jdUZPAHrtSr/wNa5D+q2Ybbpli42dDOOeJCluKHCjgTI66neHYoNpbISs2BljP2rJh/YYyevMmtXuMZigBAAAAAAAAAAAAAAAAAJg6AAAAAAAAAAAKAAAAAAAAAMDGLQAAAPCPJv////////8A",
        "Program 4skJ85cdxQAFVKbcGgfun8iZPL7BadVYXG3kGEGkufqA consumed 24022 of 200000 compute units",
        "Program 4skJ85cdxQAFVKbcGgfun8iZPL7BadVYXG3kGEGkufqA success",
    ]

    actual = mango.expand_log_messages(logs)
    assert len(actual) == 5
    assert actual[0] == logs[0]
    assert actual[1] == logs[1]
    assert (
        actual[2]
        == """Mango LiquidatePerpMarketLog Container: 
    mangoGroup = 58T8PuaCBa6FqFqcoTB2Ay6snLp2gAUxU8hnDWcLFqyB
    liqee = 8zCJ6jdHExdnNb17cxFhFtavZ7uaRHXj1nbT3VJ8E2i5
    liqor = 2tvZs8riWYKDWsGMoNxVy1YDc7qtJb4EurcfpB2PBfKm
    marketIndex = 1
    price = 4222124650659840000
    baseTransfer = 10
    quoteTransfer = -4011018418126845000000
    bankruptcy = False"""
    )
    assert actual[3] == logs[4]
    assert actual[4] == logs[5]


def test_expand_liquidate_token_and_perp() -> None:
    # https://explorer.solana.com/tx/5TmXHZbwYhXE2pN868cH72ak8GrZtVyxJPRYXY2h4jTRzhmNbAtoZrq24TSUxZBX8Bf3xMYMGLWgyuV79P5QMMxs?cluster=devnet
    logs = [
        "Program 4skJ85cdxQAFVKbcGgfun8iZPL7BadVYXG3kGEGkufqA invoke [1]",
        "Program log: Mango: LiquidateTokenAndPerp",
        "Program log: mango-log",
        "Program log: F5qwwQsqqPQ9V1sXbGlWtx7PorbATlnhud1k4TouaelSIuWjq6DS+hwo4EyOup3h2KDaWyErNgZYz9qyYf2GMnrzJrV7jGYoDwAAAAAAAAAAAAAAAADyAwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==",
        "Program log: mango-log",
        "Program log: F5qwwQsqqPQ9V1sXbGlWtx7PorbATlnhud1k4TouaelSIuWjq6DS+naor4jdUZPAHrtSr/wNa5D+q2Ybbpli42dDOOeJCluKDwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==",
        "Program log: mango-log",
        "Program log: EmyboIQCGyA9V1sXbGlWtx7PorbATlnhud1k4TouaelSIuWjq6DS+naor4jdUZPAHrtSr/wNa5D+q2Ybbpli42dDOOeJCluKHCjgTI66neHYoNpbISs2BljP2rJh/YYyevMmtXuMZigPAAAAAAAAAAEAAAAAAAAAAAEAAAAAAAABAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAICWmAAAAAAAAAAAAAAAAACAlpgAAAAAAAAAAQ==",
        "Program 4skJ85cdxQAFVKbcGgfun8iZPL7BadVYXG3kGEGkufqA consumed 34000 of 200000 compute units",
        "Program 4skJ85cdxQAFVKbcGgfun8iZPL7BadVYXG3kGEGkufqA success",
    ]

    actual = mango.expand_log_messages(logs)
    assert len(actual) == 7
    assert actual[0] == logs[0]
    assert actual[1] == logs[1]
    assert (
        actual[2]
        == """Mango TokenBalanceLog Container: 
    mangoGroup = 58T8PuaCBa6FqFqcoTB2Ay6snLp2gAUxU8hnDWcLFqyB
    mangoAccount = 2tvZs8riWYKDWsGMoNxVy1YDc7qtJb4EurcfpB2PBfKm
    tokenIndex = 15
    deposit = 284289726477762560
    borrow = 0"""
    )
    assert (
        actual[3]
        == """Mango TokenBalanceLog Container: 
    mangoGroup = 58T8PuaCBa6FqFqcoTB2Ay6snLp2gAUxU8hnDWcLFqyB
    mangoAccount = 8zCJ6jdHExdnNb17cxFhFtavZ7uaRHXj1nbT3VJ8E2i5
    tokenIndex = 15
    deposit = 0
    borrow = 0"""
    )
    assert (
        actual[4]
        == """Mango LiquidateTokenAndPerpLog Container: 
    mangoGroup = 58T8PuaCBa6FqFqcoTB2Ay6snLp2gAUxU8hnDWcLFqyB
    liqee = 8zCJ6jdHExdnNb17cxFhFtavZ7uaRHXj1nbT3VJ8E2i5
    liqor = 2tvZs8riWYKDWsGMoNxVy1YDc7qtJb4EurcfpB2PBfKm
    assetIndex = 15
    liabIndex = 1
    assetType = 0
    liabType = 1
    assetPrice = 281474976710656
    liabPrice = 281474976710656
    assetTransfer = 2814749767106560000000
    liabTransfer = 2814749767106560000000
    bankruptcy = True"""
    )
    assert actual[5] == logs[8]
    assert actual[6] == logs[9]


def test_expand_resolve_perp_bankruptcy() -> None:
    # https://explorer.solana.com/tx/64AhTnzhQDwmJKsXcDukjSRV9Te7uDaZB586dLFPNAr8KLf9DmvKhY2WvG95nVXQbTae3MqoPB14MQXhmEPYhmtY?cluster=devnet
    logs = [
        "Program 4skJ85cdxQAFVKbcGgfun8iZPL7BadVYXG3kGEGkufqA invoke [1]",
        "Program log: Mango: ResolvePerpBankruptcy",
        "Program log: mango-log",
        "Program log: ZS+iIbP3D4M9V1sXbGlWtx7PorbATlnhud1k4TouaelSIuWjq6DS+naor4jdUZPAHrtSr/wNa5D+q2Ybbpli42dDOOeJCluKHCjgTI66neHYoNpbISs2BljP2rJh/YYyevMmtXuMZigBAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANkZCAAAkOj////////////ZGQgAAJDo////////////",
        "Program 4skJ85cdxQAFVKbcGgfun8iZPL7BadVYXG3kGEGkufqA consumed 11097 of 200000 compute units",
        "Program 4skJ85cdxQAFVKbcGgfun8iZPL7BadVYXG3kGEGkufqA success",
    ]

    actual = mango.expand_log_messages(logs)
    assert len(actual) == 5
    assert actual[0] == logs[0]
    assert actual[1] == logs[1]
    assert (
        actual[2]
        == """Mango PerpBankruptcyLog Container: 
    mangoGroup = 58T8PuaCBa6FqFqcoTB2Ay6snLp2gAUxU8hnDWcLFqyB
    liqee = 8zCJ6jdHExdnNb17cxFhFtavZ7uaRHXj1nbT3VJ8E2i5
    liqor = 2tvZs8riWYKDWsGMoNxVy1YDc7qtJb4EurcfpB2PBfKm
    liabIndex = 1
    insuranceTransfer = 0
    socializedLoss = 0
    cacheLongFunding = -6597069766125095
    cacheShortFunding = -6597069766125095"""
    )
    assert actual[3] == logs[4]
    assert actual[4] == logs[5]


def test_expand_caches() -> None:
    # https://explorer.solana.com/tx/5qyQkpiHX1CmuHw1GeoMq5vfq6usAt53st83dcF4SjKDJG9Agjogf8ADnv1TYohYL6vggbLuFdbfUM9mC2mQd1js
    logs = [
        "Program mv3ekLzLbnVPNxjSKvqBpU3ZeZXPQdEC3bp5MDEBG68 invoke [1]",
        "Program log: Mango: CacheRootBanks",
        "Program log: mango-log",
        "Program log: IVXYca/Gfeh43ogDQe0xql0u2Ff66cc9XSGzkyyZdqoGDHUXDByC3QgAAAAAAAAAAAAAAAEAAAAAAAAAAgAAAAAAAAADAAAAAAAAAAQAAAAAAAAABQAAAAAAAAAGAAAAAAAAAAcAAAAAAAAACAAAAELaJcNAa+xJDwAAAAAAAACC1na5PCm5Rg8AAAAAAAAAjztXoMULkEIPAAAAAAAAAJVVDNpkE0JCDwAAAAAAAABA2c9fQYiKYg8AAAAAAAAAo++LymCkJWMPAAAAAAAAACBsPdGraDNqDwAAAAAAAADqLFzyVtE8RA8AAAAAAAAACAAAAHtzSBeucE1TDwAAAAAAAACG0Js41HnRSA8AAAAAAAAAUk/yUs80G0QPAAAAAAAAANE/cZNML5lCDwAAAAAAAADJ9E7vZyvebg8AAAAAAAAAIsKHpCisxnQPAAAAAAAAABnd0Ei+/7x5DwAAAAAAAAC3LEjaicpSSA8AAAAAAAAA",
        "Program mv3ekLzLbnVPNxjSKvqBpU3ZeZXPQdEC3bp5MDEBG68 consumed 13538 of 200000 compute units",
        "Program mv3ekLzLbnVPNxjSKvqBpU3ZeZXPQdEC3bp5MDEBG68 success",
        "Program mv3ekLzLbnVPNxjSKvqBpU3ZeZXPQdEC3bp5MDEBG68 invoke [1]",
        "Program log: Mango: CachePrices",
        "Program log: mango-log",
        "Program log: ux0uSxX5tBt43ogDQe0xql0u2Ff66cc9XSGzkyyZdqoGDHUXDByC3QgAAAAAAAAAAAAAAAEAAAAAAAAAAgAAAAAAAAADAAAAAAAAAAQAAAAAAAAABQAAAAAAAAAGAAAAAAAAAAcAAAAAAAAACAAAAMBbIEHxQwAAAAAAAAAAAAChRbbz/dSu4AAAAAAAAAAA/Bhz1xLivg4AAAAAAAAAAMU9HHhDJgAAAAAAAAAAAABWx9imBAABAAAAAAAAAAAAgpSOKKOYBwAAAAAAAAAAANEzYgvm4gkAAAAAAAAAAABUSvhzRFoBAAAAAAAAAAAA",
        "Program mv3ekLzLbnVPNxjSKvqBpU3ZeZXPQdEC3bp5MDEBG68 consumed 59177 of 200000 compute units",
        "Program mv3ekLzLbnVPNxjSKvqBpU3ZeZXPQdEC3bp5MDEBG68 success",
        "Program mv3ekLzLbnVPNxjSKvqBpU3ZeZXPQdEC3bp5MDEBG68 invoke [1]",
        "Program log: Mango: CachePerpMarkets",
        "Program log: mango-log",
        "Program log: 9lt9JxCzqw543ogDQe0xql0u2Ff66cc9XSGzkyyZdqoGDHUXDByC3QIAAAABAAAAAAAAAAMAAAAAAAAAAgAAAMqkWEieuOP5BAAAAAAAAAAMaEaZks1h/QAAAAAAAAAAAgAAAFDep7S5sr/zBAAAAAAAAAAMaEaZks1h/QAAAAAAAAAA",
        "Program mv3ekLzLbnVPNxjSKvqBpU3ZeZXPQdEC3bp5MDEBG68 consumed 5723 of 200000 compute units",
        "Program mv3ekLzLbnVPNxjSKvqBpU3ZeZXPQdEC3bp5MDEBG68 success",
    ]

    actual = mango.expand_log_messages(logs)
    assert len(actual) == 15
    assert actual[0] == logs[0]
    assert actual[1] == logs[1]
    assert (
        actual[2]
        == """Mango CacheRootBanksLog Container: 
    mangoGroup = 98pjRuQjK3qA6gXts96PqZT4Ze5QmnCmt3QYjhbUSPue
    tokenIndexes_count = 8
    tokenIndexes = ListContainer: 
        0
        1
        2
        3
        4
        5
        6
        7
    depositIndexes_count = 8
    depositIndexes = ListContainer: 
        282027911490811845186
        281797310899776050818
        281497507652219386767
        281475560984485320085
        283801798682507991360
        283845458225158418339
        284353736384635038752
        281618196170188532970
    borrowIndexes_count = 8
    borrowIndexes = ListContainer: 
        282703738877015257979
        281948270098896375942
        281608735389648047954
        281500079989520941009
        284690031620041667785
        285115763349990654498
        285473328472584674585
        281912611517885852855"""
    )
    assert actual[3] == logs[4]
    assert actual[4] == logs[5]
    assert actual[5] == logs[6]
    assert actual[6] == logs[7]
    assert (
        actual[7]
        == """Mango CachePricesLog Container: 
    mangoGroup = 98pjRuQjK3qA6gXts96PqZT4Ze5QmnCmt3QYjhbUSPue
    oracleIndexes_count = 8
    oracleIndexes = ListContainer: 
        0
        1
        2
        3
        4
        5
        6
        7
    oraclePrices_count = 8
    oraclePrices = ListContainer: 
        74703458819008
        16190111897624135073
        1062535132657948924
        42071219781061
        281494955804502
        2138151364498562
        2782752451736529
        380725026638420"""
    )
    assert actual[8] == logs[10]
    assert actual[9] == logs[11]
    assert actual[10] == logs[12]
    assert actual[11] == logs[13]
    assert (
        actual[12]
        == """Mango CachePerpMarketsLog Container: 
    mangoGroup = 98pjRuQjK3qA6gXts96PqZT4Ze5QmnCmt3QYjhbUSPue
    marketIndexes_count = 2
    marketIndexes = ListContainer: 
        1
        3
    longFundings_count = 2
    longFundings = ListContainer: 
        91793415019953693898
        18258100393857148940
    shortFundings_count = 2
    shortFundings = ListContainer: 
        91350929877276024400
        18258100393857148940"""
    )
    assert actual[13] == logs[16]
    assert actual[14] == logs[17]
