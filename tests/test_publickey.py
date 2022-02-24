from .context import mango

from solana.publickey import PublicKey


# Public keys in Rust are sorted using the underlying integers of the public key (details in publickey.py).
#
# Here we have 100 random public keys, and we sort them and compare our sort results with Rust's answer.
#
# This is the simple Rust program that sorted the `expected` results.
#
# use solana_program::pubkey::Pubkey;
# use std::str::FromStr;
#
# fn main() {
#     let mut keys: [Pubkey; 100] = [
#         Pubkey::from_str("FaQzFknCYS1Dt1T8d7wXr6a8dxSZwgb1YyiR1pmWJBC").unwrap(),
#         ...
#         Pubkey::from_str("E127URgoUVjVmuvwLEbvtEdiSkrsMjBL8J6zrV1djN7a").unwrap(),
#     ];
#
#     let mut tree_keys = BTreeSet::new();
#     for key in keys {
#         tree_keys.insert(pubkey_to_ints(key));
#     }
#
#     for key in keys {
#         println!("{:?}", ints_to_pubkey(key));
#     }
# }
def test_publickey_sorting() -> None:
    test_keys = [
        PublicKey("FaQzFknCYS1Dt1T8d7wXr6a8dxSZwgb1YyiR1pmWJBC"),
        PublicKey("AuAYgwDerZryPif7Zw1ZqACYgJFRqmKwy3ZqASr2Wu7d"),
        PublicKey("79bShRscEARLjd1gzYz7LMC76ft87AQZxcRk3ZPg7thf"),
        PublicKey("HMbNVVb6uqqhuTaQU4RmKDeG3VZ1pvRn3PgnhfevbjWJ"),
        PublicKey("FFzYWt9K2ZDeyxpDbvKbma6232baDHoCFGL1gZAKiox1"),
        PublicKey("CpFj2d5uYjeh34FKh6iYRTE2dL3N9NaSrZtyZVZ7eQwa"),
        PublicKey("FyjuBBN5fUHjtpB5LbSVW1mMocWCBebWJEecr1YN1TaQ"),
        PublicKey("2zBRHRBd8mieLZ4nvYpJqw8D9Bc9tRhgnrBvLxw5rswv"),
        PublicKey("GFQFVSEYN9ho4UwA4KJefTGrrnV8xKwyT2U5VoY4ABRw"),
        PublicKey("E9UL1uyqoU6KNvQhn4dRhJ85jzu9zSQ8mnKK6zG6K2LH"),
        PublicKey("789UPSUbj9TYSm12e66qo8PCE7RvDygqFKyy7qvCjtBD"),
        PublicKey("Hgbt3PYF3CPjJxwgurNPtU7PxKWZawxbVYAY3PHuqcRY"),
        PublicKey("jD2gcCANgvQM54brip9jT9L3PHfG3YmoBALQeWQ2QFt"),
        PublicKey("8ZuYuQdGesgcKs6UaiHZNo44iijnsFJ4zUEF3KymUhjw"),
        PublicKey("8CvG7fomKP6sKkQyXjfDHsR136sp9u5ZpNJ729WCkZfU"),
        PublicKey("8vwLZcSLSbzVcRdFnaZwt9NuKD4bg5uBGJAYhMGoFPcP"),
        PublicKey("2cajckordhWNcwvQJYS5J9LJh7RPqhcv9czHQ95tnkxK"),
        PublicKey("3YScXQsTBbgk18nGg5afhn79moaJg2PdejiEcZ7ht2SH"),
        PublicKey("2oTmVYHwgdB8fjPENK3xsrTCBobTeKbmpZ4yLtkEkqzL"),
        PublicKey("FHu3CPsdfWXNHqBBiN8JTCEm6zC17cDYGtoTfePToQrw"),
        PublicKey("Ft2129Jmb97wiMdxVS1BdMJWF2ERa2YBG8AQUCmPqmy"),
        PublicKey("14igF9QQM3ogY12P7oPNRDKkYo3iVyon8Fn83pE8SHts"),
        PublicKey("63hKqN5GRRgrzCRWu6sCJwQTTdTXUYJ8ETMbB4Mt67iD"),
        PublicKey("GM84K5sn1QQYtjYxYFtz3jTNbSvV2G8BpgJCqjwdfcCb"),
        PublicKey("4B1Tbqz81pvxEVpMPf2FM4NWSXuSQhRnmRZM2FhTrgF7"),
        PublicKey("H49zWE7fG4urtLVeh2zW59tfjvVQwABVgpSSnYnZEeMz"),
        PublicKey("5eYqA3p7r5s3zU1pgQmcvfjCX5LF8bubpWPEjrqmX7Dw"),
        PublicKey("CtMW9aHoeWje6F3xg69e2PpEwymR5Ui5pX54tBhxtzQZ"),
        PublicKey("9XRyYK2A8rTexY53ejayVj8fHTaWCN5pNkZhKLcut76L"),
        PublicKey("GV29z82JwRmHiSeN9PENbqv4AFfyJf2H4cgaAJaD8Vto"),
        PublicKey("DY52aLKPJvaKsSaZKDF2c7KwtJzjFz7cqKZBJXNAwSar"),
        PublicKey("HNEq27KbPirQg2p4hxWGTqV5SVHZ6hgWFPztgiPsR6hn"),
        PublicKey("5hZ5rcX1DqueKr7qzkezocb5ZHtcMj33q6uCmPntzYYi"),
        PublicKey("EM78jyFe9zuUbRP4GgaQWzno2KXVomtcg9goo1hNdAb9"),
        PublicKey("6zbwRzg4iF1X4EGt6HDPxN7MhhMQ24AbLnvKQayavPWX"),
        PublicKey("BBkkUWGUc9kKfwozXcUcLorjwHoXRmKA8qRRVPqpvjXq"),
        PublicKey("Gw8p8azXmdpvLx47vVDTPL4T5p3VEPa8hZuEusbTJSMy"),
        PublicKey("7NgPHoJ5ivfpjRLgACiH1TDMmEhjVwyhVJaH3aDZVsJ1"),
        PublicKey("C9kBeUC6hcEtwcKJkTHgpdP6a9SMUDxGjXnN4e8Tontw"),
        PublicKey("FWSvYWHxyFNFYbrVPhpnCGNyUGSkdKgPsc6DBrqLmbEe"),
        PublicKey("4y8ADg7MQb1nCmjBLzSPj3WaH8jm2qEja7NegjgZBKqi"),
        PublicKey("4LFA8z3GhC5EWx3SWVdod5QFD3MPLXddoGpSAQK27SNf"),
        PublicKey("C4sgUMwSPvG7ZjKAmar1TM7LFgMCDVyjckNTrV86hXWH"),
        PublicKey("4b5LV9Bs6em5vTDDVUFF19qawaYQDn1addoJBTbfmX1c"),
        PublicKey("4s7bwjQobUbNDppQwMQFTVpymFfEpBef7gqBuMfULRXK"),
        PublicKey("B57BzdoQ46x1onVjHErdywm9sj8jbfLUj5ZebP949Wh9"),
        PublicKey("Frpw9wPRPBZVU3zeo68QNG5TUYE7CppBs95fMW4sPE65"),
        PublicKey("62rcaLmakWcrgY2gx9RRUFPMCtJLdQTZxBN7e9GjMk7e"),
        PublicKey("4kLDJZC1mqPmdHqh8kcimPXgTuc1LTJ675yGbBSEgsCi"),
        PublicKey("DP1amGmG3vYwuhA7f4zBy53w1FnwXDjfWq3XDjFxMkws"),
        PublicKey("7yjA7YRs8F9vJuFAumppeUyPru1F1pWq6LCCZyEz7DPM"),
        PublicKey("55khzPSejjeszQGxTLBbSpQCsxgua4rJd8oVLS2Y2Bph"),
        PublicKey("HMSQA4yR3pDGrqTHv1aoWCpq9XsCTEuJxDuXm1yXsCnL"),
        PublicKey("2ZStGBQB6DSqp8F2ViWTkpPmUM7ftUCw3w792f4ueabV"),
        PublicKey("21YQ894x99ZTuURyTN1s7m487UfkM879NXLh5UEM2vNR"),
        PublicKey("6BPG3PJVXXYDh5BuPfZ9T1LkJUze963zDEYzq8jkMpAa"),
        PublicKey("4oDYXx7porfa9RNQ5GqCFRJus9QdAghaZRGfYpKcDdV9"),
        PublicKey("537kPFLDsGAfFDdyUGscUwh7H3KCyyJPKU5zjMbGz5GQ"),
        PublicKey("2WJ7pn8EA2WwnUjiSt8dGG49Phhbdv5BZDsMHKnET4mu"),
        PublicKey("BPECKNAWf8UtUWYzw2d43SiymZnZ929gqSav3UPhYpyr"),
        PublicKey("D5Sicgv9HTRMPLdKbbjbn41zRwTkhkqkbq7zogjbhm2X"),
        PublicKey("Fkmm1KUQ6QTxiBK7553sf6uw7BnX1uuNydow1GrYMq2"),
        PublicKey("74sfsHxXaynNGVCs71xaJaammoSHVEpBxpE2F9wzVVSd"),
        PublicKey("CX2mNmcNiUMBWx88TmnXBvQ7faXvA2RSNJgvUWjzfZMn"),
        PublicKey("4krpm3UNZsdy4AYw46QqPj9rUELqtFZQ1CcL5Lgh1ML2"),
        PublicKey("AUWEeSwhjQAjZQxjbAQVqE9LYnzUsB34HtoJ7hkn6Nrc"),
        PublicKey("C6LTAaXhbQEk7H9R1JtYkAyXiyAuQpNguDo5UL7HqGC1"),
        PublicKey("FLtXdbBqyt1ZWeHXUWSLn97DgvLeKno2MF8rhFETYJLR"),
        PublicKey("7s8LE1PbXVpXLEmoP5P87srxaRxgosyi7YwdnkeY7m47"),
        PublicKey("EtNymGqGVivS83AxyNv5HS9Qrx51p2iDm7Fff7FxiGwp"),
        PublicKey("4xTwcGLNVb4TopkB26261nbuXruiNsdoPQnQuJdauAJs"),
        PublicKey("Fh5B29PTD674my1BKmRNeZC7J5FwB8YpodwQGTZpfMUk"),
        PublicKey("CisVfVq2hn59emj6WKicRmkPpMr471PrGATBu1WYTvZg"),
        PublicKey("5orrw1iBsRGdDmUddgtKY8xwGWjcACdGxxRrroE2VXj2"),
        PublicKey("GiN6Z2gszbiEG9TeCBhNKKJJzkUNx5oopWayRtH9EzDZ"),
        PublicKey("H1QLi2LzP6sX2yrUFxtDSQbFSCb5BkyX5RkTzqJ6Xys8"),
        PublicKey("FBeiSC3xqiiBJZzD2iPZjXM6BhPPYeuy2pmHkkuPgcK4"),
        PublicKey("3N1dJLeninTjqvrAG3FE57wm33YxpxNZfNZ4gkEQQJYA"),
        PublicKey("FUaUit7aJNAZN8Nw4k8mB7o6wcmJH1roCsQHj8GdRiVm"),
        PublicKey("FAGHSmdfKiA7LXroX7sUkgoQnxVXt7yXhsJjBcVQRRCZ"),
        PublicKey("J9DXnDPgxpvyGfXULryE8GXWe7DawwbcrJGrGqfEtLa1"),
        PublicKey("63eN8edxvhJR2nUcGMM856e9bNTDfEM9d6ovu4USdvbw"),
        PublicKey("DupkfDPApCzzmv7tsFuwZVFBnmmMKV4UUrzmmNCpy8E3"),
        PublicKey("87Sjjrg5FHmZVDTLUYnvdeLrVZyDe8un7xYyPiHNEm9x"),
        PublicKey("HGU98QR8XxwPha8nZg13zkFCmWpfc3dWK8UkoaByzs9p"),
        PublicKey("4cu7NafTC7hvCCANgKZGag3DFNXTJqMVoT5eJGqHL4oG"),
        PublicKey("DXdiJtxsF2RDpjtrMhfMZuHBaQwURnQyuRLX2q6dhzry"),
        PublicKey("22t641xPeFpifwfukJu38ehQBtGoaVfXGdiMLz2nZPRF"),
        PublicKey("JCxwtTLkh83ArtcnZtT4KAKB774MvnYTLpLj9sR751rb"),
        PublicKey("9jde9Fk849sFtPrN4mbREeUAepLhoZQcA5dw2JRtqhmU"),
        PublicKey("CYfcWfLwJUp24Vzpj33bujduaULh6GjHa3jsY68ckWuq"),
        PublicKey("27xu2d4Sp66ELdt4U2HrNe3VVR9dYw8w4y2xvtkbxF4J"),
        PublicKey("AXDaZsV9yvRaB7os8Xp5cXMLHraXgZPAeb4C7vCnpNvv"),
        PublicKey("6GXdgaK36niHpdyg56ffUaMkX7xnbvP4EtC9SCpoj5N3"),
        PublicKey("4DmvwtNjDupK4bW3zBEoEFEAuGjPzntZy3eJEC2gXqNa"),
        PublicKey("GPJbua6w7mfbyqGEPwo7tk7iBAHUjvyjTvNBVVAL1LWm"),
        PublicKey("2jXpCvzJkDxUSxpP3U7VUGSDCDpWDZqZGg2LGsGrhUDp"),
        PublicKey("7wDMKabpaBC1kj41hmotn1qBQhKSqRpGvAb1x347m6zT"),
        PublicKey("DcRaC7n2ws825JGXqf4cRr8mbXWXf9k5e2xDbFYC1EH7"),
        PublicKey("E127URgoUVjVmuvwLEbvtEdiSkrsMjBL8J6zrV1djN7a"),
    ]

    expected = [
        PublicKey("AXDaZsV9yvRaB7os8Xp5cXMLHraXgZPAeb4C7vCnpNvv"),
        PublicKey("4kLDJZC1mqPmdHqh8kcimPXgTuc1LTJ675yGbBSEgsCi"),
        PublicKey("C9kBeUC6hcEtwcKJkTHgpdP6a9SMUDxGjXnN4e8Tontw"),
        PublicKey("FBeiSC3xqiiBJZzD2iPZjXM6BhPPYeuy2pmHkkuPgcK4"),
        PublicKey("Ft2129Jmb97wiMdxVS1BdMJWF2ERa2YBG8AQUCmPqmy"),
        PublicKey("AUWEeSwhjQAjZQxjbAQVqE9LYnzUsB34HtoJ7hkn6Nrc"),
        PublicKey("6zbwRzg4iF1X4EGt6HDPxN7MhhMQ24AbLnvKQayavPWX"),
        PublicKey("9XRyYK2A8rTexY53ejayVj8fHTaWCN5pNkZhKLcut76L"),
        PublicKey("27xu2d4Sp66ELdt4U2HrNe3VVR9dYw8w4y2xvtkbxF4J"),
        PublicKey("EM78jyFe9zuUbRP4GgaQWzno2KXVomtcg9goo1hNdAb9"),
        PublicKey("D5Sicgv9HTRMPLdKbbjbn41zRwTkhkqkbq7zogjbhm2X"),
        PublicKey("5orrw1iBsRGdDmUddgtKY8xwGWjcACdGxxRrroE2VXj2"),
        PublicKey("Frpw9wPRPBZVU3zeo68QNG5TUYE7CppBs95fMW4sPE65"),
        PublicKey("GiN6Z2gszbiEG9TeCBhNKKJJzkUNx5oopWayRtH9EzDZ"),
        PublicKey("4xTwcGLNVb4TopkB26261nbuXruiNsdoPQnQuJdauAJs"),
        PublicKey("C4sgUMwSPvG7ZjKAmar1TM7LFgMCDVyjckNTrV86hXWH"),
        PublicKey("2oTmVYHwgdB8fjPENK3xsrTCBobTeKbmpZ4yLtkEkqzL"),
        PublicKey("CX2mNmcNiUMBWx88TmnXBvQ7faXvA2RSNJgvUWjzfZMn"),
        PublicKey("GM84K5sn1QQYtjYxYFtz3jTNbSvV2G8BpgJCqjwdfcCb"),
        PublicKey("GPJbua6w7mfbyqGEPwo7tk7iBAHUjvyjTvNBVVAL1LWm"),
        PublicKey("BPECKNAWf8UtUWYzw2d43SiymZnZ929gqSav3UPhYpyr"),
        PublicKey("CYfcWfLwJUp24Vzpj33bujduaULh6GjHa3jsY68ckWuq"),
        PublicKey("3N1dJLeninTjqvrAG3FE57wm33YxpxNZfNZ4gkEQQJYA"),
        PublicKey("Hgbt3PYF3CPjJxwgurNPtU7PxKWZawxbVYAY3PHuqcRY"),
        PublicKey("FyjuBBN5fUHjtpB5LbSVW1mMocWCBebWJEecr1YN1TaQ"),
        PublicKey("C6LTAaXhbQEk7H9R1JtYkAyXiyAuQpNguDo5UL7HqGC1"),
        PublicKey("DY52aLKPJvaKsSaZKDF2c7KwtJzjFz7cqKZBJXNAwSar"),
        PublicKey("6BPG3PJVXXYDh5BuPfZ9T1LkJUze963zDEYzq8jkMpAa"),
        PublicKey("4cu7NafTC7hvCCANgKZGag3DFNXTJqMVoT5eJGqHL4oG"),
        PublicKey("2jXpCvzJkDxUSxpP3U7VUGSDCDpWDZqZGg2LGsGrhUDp"),
        PublicKey("4LFA8z3GhC5EWx3SWVdod5QFD3MPLXddoGpSAQK27SNf"),
        PublicKey("DXdiJtxsF2RDpjtrMhfMZuHBaQwURnQyuRLX2q6dhzry"),
        PublicKey("62rcaLmakWcrgY2gx9RRUFPMCtJLdQTZxBN7e9GjMk7e"),
        PublicKey("4B1Tbqz81pvxEVpMPf2FM4NWSXuSQhRnmRZM2FhTrgF7"),
        PublicKey("55khzPSejjeszQGxTLBbSpQCsxgua4rJd8oVLS2Y2Bph"),
        PublicKey("FAGHSmdfKiA7LXroX7sUkgoQnxVXt7yXhsJjBcVQRRCZ"),
        PublicKey("4krpm3UNZsdy4AYw46QqPj9rUELqtFZQ1CcL5Lgh1ML2"),
        PublicKey("FUaUit7aJNAZN8Nw4k8mB7o6wcmJH1roCsQHj8GdRiVm"),
        PublicKey("GV29z82JwRmHiSeN9PENbqv4AFfyJf2H4cgaAJaD8Vto"),
        PublicKey("21YQ894x99ZTuURyTN1s7m487UfkM879NXLh5UEM2vNR"),
        PublicKey("AuAYgwDerZryPif7Zw1ZqACYgJFRqmKwy3ZqASr2Wu7d"),
        PublicKey("J9DXnDPgxpvyGfXULryE8GXWe7DawwbcrJGrGqfEtLa1"),
        PublicKey("79bShRscEARLjd1gzYz7LMC76ft87AQZxcRk3ZPg7thf"),
        PublicKey("63eN8edxvhJR2nUcGMM856e9bNTDfEM9d6ovu4USdvbw"),
        PublicKey("63hKqN5GRRgrzCRWu6sCJwQTTdTXUYJ8ETMbB4Mt67iD"),
        PublicKey("JCxwtTLkh83ArtcnZtT4KAKB774MvnYTLpLj9sR751rb"),
        PublicKey("FaQzFknCYS1Dt1T8d7wXr6a8dxSZwgb1YyiR1pmWJBC"),
        PublicKey("7s8LE1PbXVpXLEmoP5P87srxaRxgosyi7YwdnkeY7m47"),
        PublicKey("7yjA7YRs8F9vJuFAumppeUyPru1F1pWq6LCCZyEz7DPM"),
        PublicKey("GFQFVSEYN9ho4UwA4KJefTGrrnV8xKwyT2U5VoY4ABRw"),
        PublicKey("2ZStGBQB6DSqp8F2ViWTkpPmUM7ftUCw3w792f4ueabV"),
        PublicKey("DupkfDPApCzzmv7tsFuwZVFBnmmMKV4UUrzmmNCpy8E3"),
        PublicKey("DcRaC7n2ws825JGXqf4cRr8mbXWXf9k5e2xDbFYC1EH7"),
        PublicKey("2WJ7pn8EA2WwnUjiSt8dGG49Phhbdv5BZDsMHKnET4mu"),
        PublicKey("4b5LV9Bs6em5vTDDVUFF19qawaYQDn1addoJBTbfmX1c"),
        PublicKey("14igF9QQM3ogY12P7oPNRDKkYo3iVyon8Fn83pE8SHts"),
        PublicKey("HMSQA4yR3pDGrqTHv1aoWCpq9XsCTEuJxDuXm1yXsCnL"),
        PublicKey("FLtXdbBqyt1ZWeHXUWSLn97DgvLeKno2MF8rhFETYJLR"),
        PublicKey("8ZuYuQdGesgcKs6UaiHZNo44iijnsFJ4zUEF3KymUhjw"),
        PublicKey("CtMW9aHoeWje6F3xg69e2PpEwymR5Ui5pX54tBhxtzQZ"),
        PublicKey("FFzYWt9K2ZDeyxpDbvKbma6232baDHoCFGL1gZAKiox1"),
        PublicKey("FHu3CPsdfWXNHqBBiN8JTCEm6zC17cDYGtoTfePToQrw"),
        PublicKey("7wDMKabpaBC1kj41hmotn1qBQhKSqRpGvAb1x347m6zT"),
        PublicKey("8CvG7fomKP6sKkQyXjfDHsR136sp9u5ZpNJ729WCkZfU"),
        PublicKey("E127URgoUVjVmuvwLEbvtEdiSkrsMjBL8J6zrV1djN7a"),
        PublicKey("2zBRHRBd8mieLZ4nvYpJqw8D9Bc9tRhgnrBvLxw5rswv"),
        PublicKey("BBkkUWGUc9kKfwozXcUcLorjwHoXRmKA8qRRVPqpvjXq"),
        PublicKey("CisVfVq2hn59emj6WKicRmkPpMr471PrGATBu1WYTvZg"),
        PublicKey("789UPSUbj9TYSm12e66qo8PCE7RvDygqFKyy7qvCjtBD"),
        PublicKey("4DmvwtNjDupK4bW3zBEoEFEAuGjPzntZy3eJEC2gXqNa"),
        PublicKey("7NgPHoJ5ivfpjRLgACiH1TDMmEhjVwyhVJaH3aDZVsJ1"),
        PublicKey("74sfsHxXaynNGVCs71xaJaammoSHVEpBxpE2F9wzVVSd"),
        PublicKey("22t641xPeFpifwfukJu38ehQBtGoaVfXGdiMLz2nZPRF"),
        PublicKey("HMbNVVb6uqqhuTaQU4RmKDeG3VZ1pvRn3PgnhfevbjWJ"),
        PublicKey("4oDYXx7porfa9RNQ5GqCFRJus9QdAghaZRGfYpKcDdV9"),
        PublicKey("H49zWE7fG4urtLVeh2zW59tfjvVQwABVgpSSnYnZEeMz"),
        PublicKey("EtNymGqGVivS83AxyNv5HS9Qrx51p2iDm7Fff7FxiGwp"),
        PublicKey("537kPFLDsGAfFDdyUGscUwh7H3KCyyJPKU5zjMbGz5GQ"),
        PublicKey("HNEq27KbPirQg2p4hxWGTqV5SVHZ6hgWFPztgiPsR6hn"),
        PublicKey("E9UL1uyqoU6KNvQhn4dRhJ85jzu9zSQ8mnKK6zG6K2LH"),
        PublicKey("3YScXQsTBbgk18nGg5afhn79moaJg2PdejiEcZ7ht2SH"),
        PublicKey("Fkmm1KUQ6QTxiBK7553sf6uw7BnX1uuNydow1GrYMq2"),
        PublicKey("HGU98QR8XxwPha8nZg13zkFCmWpfc3dWK8UkoaByzs9p"),
        PublicKey("5eYqA3p7r5s3zU1pgQmcvfjCX5LF8bubpWPEjrqmX7Dw"),
        PublicKey("87Sjjrg5FHmZVDTLUYnvdeLrVZyDe8un7xYyPiHNEm9x"),
        PublicKey("9jde9Fk849sFtPrN4mbREeUAepLhoZQcA5dw2JRtqhmU"),
        PublicKey("4s7bwjQobUbNDppQwMQFTVpymFfEpBef7gqBuMfULRXK"),
        PublicKey("FWSvYWHxyFNFYbrVPhpnCGNyUGSkdKgPsc6DBrqLmbEe"),
        PublicKey("5hZ5rcX1DqueKr7qzkezocb5ZHtcMj33q6uCmPntzYYi"),
        PublicKey("jD2gcCANgvQM54brip9jT9L3PHfG3YmoBALQeWQ2QFt"),
        PublicKey("H1QLi2LzP6sX2yrUFxtDSQbFSCb5BkyX5RkTzqJ6Xys8"),
        PublicKey("Gw8p8azXmdpvLx47vVDTPL4T5p3VEPa8hZuEusbTJSMy"),
        PublicKey("CpFj2d5uYjeh34FKh6iYRTE2dL3N9NaSrZtyZVZ7eQwa"),
        PublicKey("DP1amGmG3vYwuhA7f4zBy53w1FnwXDjfWq3XDjFxMkws"),
        PublicKey("8vwLZcSLSbzVcRdFnaZwt9NuKD4bg5uBGJAYhMGoFPcP"),
        PublicKey("4y8ADg7MQb1nCmjBLzSPj3WaH8jm2qEja7NegjgZBKqi"),
        PublicKey("6GXdgaK36niHpdyg56ffUaMkX7xnbvP4EtC9SCpoj5N3"),
        PublicKey("B57BzdoQ46x1onVjHErdywm9sj8jbfLUj5ZebP949Wh9"),
        PublicKey("2cajckordhWNcwvQJYS5J9LJh7RPqhcv9czHQ95tnkxK"),
        PublicKey("Fh5B29PTD674my1BKmRNeZC7J5FwB8YpodwQGTZpfMUk"),
    ]

    test_keys.sort(key=mango.encode_public_key_for_sorting)

    for counter in range(len(test_keys)):
        assert (
            test_keys[counter] == expected[counter]
        ), f"Index {counter} - {test_keys[counter]} does not match expected {expected[counter]}"


# This is the same test but with a smaller array to help with debugging.
#
def test_publickey_shorter_sorting() -> None:
    test_keys = [
        PublicKey("FaQzFknCYS1Dt1T8d7wXr6a8dxSZwgb1YyiR1pmWJBC"),
        PublicKey("AuAYgwDerZryPif7Zw1ZqACYgJFRqmKwy3ZqASr2Wu7d"),
        PublicKey("79bShRscEARLjd1gzYz7LMC76ft87AQZxcRk3ZPg7thf"),
        PublicKey("HMbNVVb6uqqhuTaQU4RmKDeG3VZ1pvRn3PgnhfevbjWJ"),
        PublicKey("FFzYWt9K2ZDeyxpDbvKbma6232baDHoCFGL1gZAKiox1"),
        PublicKey("CpFj2d5uYjeh34FKh6iYRTE2dL3N9NaSrZtyZVZ7eQwa"),
        PublicKey("FyjuBBN5fUHjtpB5LbSVW1mMocWCBebWJEecr1YN1TaQ"),
        PublicKey("2zBRHRBd8mieLZ4nvYpJqw8D9Bc9tRhgnrBvLxw5rswv"),
        PublicKey("GFQFVSEYN9ho4UwA4KJefTGrrnV8xKwyT2U5VoY4ABRw"),
        PublicKey("E9UL1uyqoU6KNvQhn4dRhJ85jzu9zSQ8mnKK6zG6K2LH"),
        PublicKey("789UPSUbj9TYSm12e66qo8PCE7RvDygqFKyy7qvCjtBD"),
        PublicKey("Hgbt3PYF3CPjJxwgurNPtU7PxKWZawxbVYAY3PHuqcRY"),
        PublicKey("jD2gcCANgvQM54brip9jT9L3PHfG3YmoBALQeWQ2QFt"),
        PublicKey("8ZuYuQdGesgcKs6UaiHZNo44iijnsFJ4zUEF3KymUhjw"),
    ]

    expected = [
        PublicKey("Hgbt3PYF3CPjJxwgurNPtU7PxKWZawxbVYAY3PHuqcRY"),
        PublicKey("FyjuBBN5fUHjtpB5LbSVW1mMocWCBebWJEecr1YN1TaQ"),
        PublicKey("AuAYgwDerZryPif7Zw1ZqACYgJFRqmKwy3ZqASr2Wu7d"),
        PublicKey("79bShRscEARLjd1gzYz7LMC76ft87AQZxcRk3ZPg7thf"),
        PublicKey("FaQzFknCYS1Dt1T8d7wXr6a8dxSZwgb1YyiR1pmWJBC"),
        PublicKey("GFQFVSEYN9ho4UwA4KJefTGrrnV8xKwyT2U5VoY4ABRw"),
        PublicKey("8ZuYuQdGesgcKs6UaiHZNo44iijnsFJ4zUEF3KymUhjw"),
        PublicKey("FFzYWt9K2ZDeyxpDbvKbma6232baDHoCFGL1gZAKiox1"),
        PublicKey("2zBRHRBd8mieLZ4nvYpJqw8D9Bc9tRhgnrBvLxw5rswv"),
        PublicKey("789UPSUbj9TYSm12e66qo8PCE7RvDygqFKyy7qvCjtBD"),
        PublicKey("HMbNVVb6uqqhuTaQU4RmKDeG3VZ1pvRn3PgnhfevbjWJ"),
        PublicKey("E9UL1uyqoU6KNvQhn4dRhJ85jzu9zSQ8mnKK6zG6K2LH"),
        PublicKey("jD2gcCANgvQM54brip9jT9L3PHfG3YmoBALQeWQ2QFt"),
        PublicKey("CpFj2d5uYjeh34FKh6iYRTE2dL3N9NaSrZtyZVZ7eQwa"),
    ]

    test_keys.sort(key=mango.encode_public_key_for_sorting)

    for counter in range(len(test_keys)):
        assert (
            test_keys[counter] == expected[counter]
        ), f"Index {counter} - {test_keys[counter]} does not match expected {expected[counter]}"
