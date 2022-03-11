import pandas
import typing

from .data import load_data_from_directory

from decimal import Decimal


def __compare_series(
    expected: typing.Sequence[str], frame: pandas.DataFrame, column_name: str
) -> None:
    non_quote = frame.loc[frame["Symbol"] != "USDC"]
    series = non_quote[column_name]
    for index, perp_value in enumerate(series):
        assert perp_value == Decimal(
            expected[index]
        ), f"Incorrect {column_name} value at index: {index}, actual: {perp_value}, expected: {expected[index]}, all: {series}"


def test_empty() -> None:
    group, cache, account, open_orders = load_data_from_directory(
        "tests/testdata/empty"
    )
    frame = account.to_dataframe(group, open_orders, cache)

    # Typescript says: 0
    assert account.init_health(frame).value == Decimal("0")

    # Typescript says: 0
    assert account.maint_health(frame).value == Decimal("0")

    # Typescript says: 100
    assert account.init_health_ratio(frame) == Decimal("100")

    # Typescript says: 100
    assert account.maint_health_ratio(frame) == Decimal("100")

    expected_perp_asset_values = [
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_perp_asset_values, frame, "PerpAsset")

    expected_perp_liability_values = [
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_perp_liability_values, frame, "PerpLiability")

    expected_unsettled_funding_values = [
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_unsettled_funding_values, frame, "UnsettledFunding")

    # # Typescript says: 0
    assert account.redeemable_pnl(frame).value == Decimal("0")

    # Typescript says: 0
    assert account.total_value(frame).value == Decimal("0")

    # Typescript says: 0
    assert account.leverage(frame) == Decimal("0")

    assert not account.is_liquidatable(frame)


def test_1deposit() -> None:
    group, cache, account, open_orders = load_data_from_directory(
        "tests/testdata/1deposit"
    )
    frame = account.to_dataframe(group, open_orders, cache)

    # Typescript says: 37904260000.05905822642118252475
    assert account.init_health(frame).value == Decimal(
        "37904.2600000591928892771752953600134"
    )

    # Typescript says: 42642292500.06652466908819931746
    assert account.maint_health(frame).value == Decimal(
        "42642.2925000665920004368222072800150"
    )

    # Typescript says: 100
    assert account.init_health_ratio(frame) == Decimal("100")

    # Typescript says: 100
    assert account.maint_health_ratio(frame) == Decimal("100")

    expected_perp_asset_values = [
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_perp_asset_values, frame, "PerpAsset")

    expected_perp_liability_values = [
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_perp_liability_values, frame, "PerpLiability")

    expected_unsettled_funding_values = [
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_unsettled_funding_values, frame, "UnsettledFunding")

    # # Typescript says: 0
    assert account.redeemable_pnl(frame).value == Decimal("0")

    # Typescript says: 47380.32499999999999928946
    assert account.total_value(frame).value == Decimal(
        "47380.3250000739911115964691192000167"
    )

    # Typescript says: 0
    assert account.leverage(frame) == Decimal("0")

    assert not account.is_liquidatable(frame)


def test_account1() -> None:
    group, cache, account, open_orders = load_data_from_directory(
        "tests/testdata/account1"
    )
    frame = account.to_dataframe(group, open_orders, cache)

    # Typescript says: 454884281.15520619643754685058
    assert account.init_health(frame).value == Decimal(
        "454.88428115521887496581258174978975"
    )

    # Typescript says: 901472688.63722587052636470162
    assert account.maint_health(frame).value == Decimal(
        "901.47268863723220971375597908220329"
    )

    # Typescript says: 10.48860467608925262084
    assert account.init_health_ratio(frame) == Decimal(
        "10.4886046760897514671034971997305770"
    )

    # Typescript says: 20.785925232226531989
    assert account.maint_health_ratio(frame) == Decimal(
        "20.7859252322269328739250898812969450"
    )

    expected_perp_asset_values = [
        "0",
        "0",
        "0",
        "2444.20361099997762715000000",  # TypeScript answer: 2444.20361099997762721614
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_perp_asset_values, frame, "PerpAsset")

    expected_perp_liability_values = [
        "0",
        "-0.11103041194074558353577231",  # TypeScript answer: 0.11103041194074236842
        "0",
        "-2231.02793460350823695499399607",  # TypeScript answer: 2231.02793460350823551153
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_perp_liability_values, frame, "PerpLiability")

    expected_unsettled_funding_values = [
        "0",
        "0",
        "0",
        "-0.151004760364538024575146",  # TypeScript answer: 0.15100476036453613915
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_unsettled_funding_values, frame, "UnsettledFunding")

    # # Typescript says: 213064645.98452864467761003198
    assert account.redeemable_pnl(frame).value == Decimal(
        "213.06464598452864461147023162"
    )

    # Typescript says: 1348.25066158888197520582
    assert account.total_value(frame).value == Decimal(
        "1348.25066711924554446169937641461683"
    )

    # Typescript says: 3.21671490144456129201
    assert account.leverage(frame) == Decimal("3.21671488765457268128834463982425497")

    assert not account.is_liquidatable(frame)


def test_account2() -> None:
    group, cache, account, open_orders = load_data_from_directory(
        "tests/testdata/account2"
    )
    frame = account.to_dataframe(group, open_orders, cache)

    # Typescript says: 7516159604.84918334545095675026
    assert account.init_health(frame).value == Decimal(
        "7516.1596048492430563556697582309637"
    )

    # Typescript says: 9618709877.45119083596852505025
    assert account.maint_health(frame).value == Decimal(
        "9618.7098774512206992595893853316522"
    )

    # Typescript says: 24.80680004365716229131
    assert account.init_health_ratio(frame) == Decimal(
        "24.8068000436574936267384623925241840"
    )

    # Typescript says: 31.74618756817508824497
    assert account.maint_health_ratio(frame) == Decimal(
        "31.7461875681752057505441268626950890"
    )

    expected_perp_asset_values = [
        "0",
        "0",
        "0",
        "42015.62498699979641965300000",  # TypeScript answer: 42015.62498699979641969549
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_perp_asset_values, frame, "PerpAsset")

    expected_perp_liability_values = [
        "0",
        "-0.46957178494402274073848957",  # TypeScript answer: 0.46957178494401929925
        "0",
        "-41767.25007673670626095621121997",  # TypeScript answer: 41767.25007673670625862883
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_perp_liability_values, frame, "PerpLiability")

    expected_unsettled_funding_values = [
        "0",
        "0",
        "0",
        "-2.2481874376993845569217526",  # TypeScript answer: 2.24818743769938222954
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_unsettled_funding_values, frame, "UnsettledFunding")

    # # Typescript says: 247905338.47814613599853572623
    assert account.redeemable_pnl(frame).value == Decimal(
        "247.90533847814613595605029046"
    )

    # Typescript says: 11721.35669142618275273549
    assert account.total_value(frame).value == Decimal(
        "11721.3566920531983421635090124323407"
    )

    # Typescript says: 3.56338611204225585993
    assert account.leverage(frame) == Decimal("3.56338611185164025806595342485346312")

    assert not account.is_liquidatable(frame)


def test_account3() -> None:
    group, cache, account, open_orders = load_data_from_directory(
        "tests/testdata/account3"
    )
    frame = account.to_dataframe(group, open_orders, cache)

    # Typescript says: 341025333625.51856223547208912805
    assert account.init_health(frame).value == Decimal(
        "341025.33362550396263557255539801613"
    )

    # Typescript says: 683477170424.20340250929429970483
    assert account.maint_health(frame).value == Decimal(
        "683477.17042418393637609525383421613"
    )

    # Typescript says: 4.52652018845647319267
    assert account.init_health_ratio(frame) == Decimal(
        "4.52652018845639596719637165673707200"
    )

    # Typescript says: 9.50397353076404272088
    assert account.maint_health_ratio(frame) == Decimal(
        "9.50397353076384339420572268801026600"
    )

    expected_perp_asset_values = [
        "0",
        "6695937.04678345438030156017933326",  # TypeScript answer: 6695937.04678345438030007131
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_perp_asset_values, frame, "PerpAsset")

    expected_perp_liability_values = [
        "0",
        "-6670154.105958399999950961574656",  # TypeScript answer: 6670154.10595839999994893788
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_perp_liability_values, frame, "PerpLiability")

    expected_unsettled_funding_values = [
        "0",
        "-10.21039760429788439887016704",  # TypeScript answer: 10.21039760429788145757
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_unsettled_funding_values, frame, "UnsettledFunding")

    # # Typescript says: 25782940825.05438035059867374343
    assert account.redeemable_pnl(frame).value == Decimal(
        "25782.94082505438035059860467726"
    )

    # Typescript says: 1025929.00722205438034961844
    assert account.total_value(frame).value == Decimal(
        "1025929.00722286391011661795227041613"
    )

    # Typescript says: 6.50157472788435697453
    assert account.leverage(frame) == Decimal("6.50157472787922998475118662978475117")

    assert not account.is_liquidatable(frame)


def test_account4() -> None:
    group, cache, account, open_orders = load_data_from_directory(
        "tests/testdata/account4"
    )
    frame = account.to_dataframe(group, open_orders, cache)

    # Typescript says: -848086876487.04950427436299875694
    assert account.init_health(frame).value == Decimal(
        "-848086.87648706716344229365643382143"
    )

    # Typescript says: -433869053006.07361789143756070075
    assert account.maint_health(frame).value == Decimal(
        "-433869.05300609716344867811565222143"
    )

    # Typescript says: -9.30655353087566084014
    assert account.init_health_ratio(frame) == Decimal(
        "-9.30655353087574422134411842983207950"
    )

    # Typescript says: -4.98781798472691662028
    assert account.maint_health_ratio(frame) == Decimal(
        "-4.98781798472697013664621930744313090"
    )

    expected_perp_asset_values = [
        "0",
        "7264559.1735603533661262332096973",  # TypeScript answer: 7264559.17356035336612407605
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_perp_asset_values, frame, "PerpAsset")

    expected_perp_liability_values = [
        "0",
        "-8284356.469619399999872310815632",  # TypeScript answer: 8284356.46961939999987123429
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_perp_liability_values, frame, "PerpLiability")

    expected_unsettled_funding_values = [
        "0",
        "-664519.2252516606319659778192923",  # TypeScript answer: 664519.22525166063196522259
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_unsettled_funding_values, frame, "UnsettledFunding")

    # # Typescript says: -1019797296059.04663374607682513329
    assert account.redeemable_pnl(frame).value == Decimal(
        "-1019797.2960590466337460776059347"
    )

    # Typescript says: -19651.22952604663374742699
    assert account.total_value(frame).value == Decimal(
        "-19651.22952512716345506257487062143"
    )

    # Typescript says: -421.56937094643044972031
    assert account.leverage(frame) == Decimal("-421.569370966155451390856326152441566")

    assert account.is_liquidatable(frame)


def test_account5() -> None:
    group, cache, account, open_orders = load_data_from_directory(
        "tests/testdata/account5"
    )
    frame = account.to_dataframe(group, open_orders, cache)

    # Typescript says: 15144959918141.09175135195858530324
    assert account.init_health(frame).value == Decimal(
        "15144959.9181410924496111317578727438"
    )

    # Typescript says: 15361719060997.68276021614036608298
    assert account.maint_health(frame).value == Decimal(
        "15361719.0609976820704356689151633723"
    )

    # Typescript says: 878.88913077823325181726
    assert account.init_health_ratio(frame) == Decimal(
        "878.889130778232107967643669989641770"
    )

    # Typescript says: 946.44498820888003365326
    assert account.maint_health_ratio(frame) == Decimal(
        "946.444988208877836980861464823408690"
    )

    expected_perp_asset_values = [
        "1273.61269133691491457262754662",  # TypeScript answer: 1273.61269133691491362015
        "10916456.07050622382794430924595425",  # TypeScript answer: 10916456.07050622382794102805
        "863331.92364778832710021687586321",  # TypeScript answer: 863331.92364778832709859557
        "174610.4024343442520579575687243",  # TypeScript answer: 174610.40243434425205748539
        "0",
        "0",
        "0",
        "14633.04150478681525824567799537",  # TypeScript answer: 14633.04150478681525626712
        "16805.69099999999941985400",  # TypeScript answer: 16805.69099999999941985607
        "137915.48069440506524617258991507",  # TypeScript answer: 137915.48069440506524330203
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_perp_asset_values, frame, "PerpAsset")

    expected_perp_liability_values = [
        "-4840.92399999998631809110",  # TypeScript answer: 4840.92399999998631798803
        "0",
        "-767288.86646559999954763459376",  # TypeScript answer: 767288.86646559999954675391
        "-167720.92749999994865377000000",  # TypeScript answer: 167720.92749999994865106601
        "0",
        "0",
        "0",
        "-1026.61699999999799359836",  # TypeScript answer: 1026.61699999999799359784
        "-16788.37122433173017963312649121",  # TypeScript answer: 16788.37122433173017910235
        "-110453.27723675812123560240000",  # TypeScript answer: 110453.27723675812123360629
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_perp_liability_values, frame, "PerpLiability")

    expected_unsettled_funding_values = [
        "-3103.4100396321438082463473248",  # TypeScript answer: 3103.41003963214380689806
        "10159.21051005666226760254040463",  # TypeScript answer: -10159.21051005666226529911
        "-24694.52420961676693137917442256",  # TypeScript answer: 24694.52420961676692812148
        "-0.328686469969476673113973",  # TypeScript answer: 0.32868646996947603611
        "0",
        "0",
        "0",
        "-66.45867935453308210650646965",  # TypeScript answer: 66.45867935453308206206
        "-44.441224331730812300378412",  # TypeScript answer: 44.4412243317308117696
        "15298.57214184517950788229926852",  # TypeScript answer: -15298.57214184517950528175
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_unsettled_funding_values, frame, "UnsettledFunding")

    # # Typescript says: 11056907239052.19541801780440337666
    assert account.redeemable_pnl(frame).value == Decimal(
        "11056907.23905219541801299900574761"
    )

    # Typescript says: 15578478.17337437202354522015
    assert account.total_value(frame).value == Decimal(
        "15578478.2038542716912602060724540009"
    )

    # Typescript says: 0.09884076560217636143
    assert account.leverage(frame) == Decimal("0.0988407635236814851193291170841739152")

    assert not account.is_liquidatable(frame)


def test_account6() -> None:
    group, cache, account, open_orders = load_data_from_directory(
        "tests/testdata/account6"
    )
    frame = account.to_dataframe(group, open_orders, cache)

    # Typescript says: 14480970069238.33686487450164648294
    assert account.init_health(frame).value == Decimal(
        "14480970.0692383312566073701425189089"
    )

    # Typescript says: 15030566.251990.17026082618337312624
    assert account.maint_health(frame).value == Decimal(
        "15030566.2519901615291113644851708626"
    )

    # Typescript says: 215.03167137712999590349
    assert account.init_health_ratio(frame) == Decimal(
        "215.031671377129731140294440951729501"
    )

    # Typescript says: 236.77769605824430243501
    assert account.maint_health_ratio(frame) == Decimal(
        "236.777696058243876968239282498979720"
    )

    expected_perp_asset_values = [
        "509.04481457486920158948960772",  # TypeScript answer: 509.04481457486919993016
        "10831730.01433129633670876168480840",  # TypeScript answer: 10831730.01433129633670660041
        "863100.47162162728756771510067553",  # TypeScript answer: 863100.47162162728756484853
        "54819.20758920613437368210796204",  # TypeScript answer: 54819.20758920613437226166
        "0",
        "0",
        "0",
        "14632.99379123635924610633551575",  # TypeScript answer: 14632.99379123635924315749
        "15945.13199999999883971220",  # TypeScript answer: 15945.13199999999883971213
        "137931.25478163725913813680472569",  # TypeScript answer: 137931.25478163725913560711
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_perp_asset_values, frame, "PerpAsset")

    expected_perp_liability_values = [
        "-4587.29287500003797718375",  # TypeScript answer: 4587.29287500003797717341
        "0",
        "-667788.07238879999951240105184",  # TypeScript answer: 667788.07238879999951208788
        "-26741.02804999988158855700000",  # TypeScript answer: 26741.02804999988158840551
        "0",
        "0",
        "0",
        "-901.57549999999859125167",  # TypeScript answer: 901.57549999999859124955
        "-16788.69364044275739133027515121",  # TypeScript answer: 16788.69364044275738834244
        "-90977.10634675426490241460000",  # TypeScript answer: 90977.10634675426490503014
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_perp_liability_values, frame, "PerpLiability")

    expected_unsettled_funding_values = [
        "-3867.9779163941895212294852637",  # TypeScript answer: 3867.97791639418952058804
        "46.41303398421391671544430544",  # TypeScript answer: -46.41303398421391435136
        "-24925.97623577780646388094961024",  # TypeScript answer: 24925.97623577780646186852
        "-0.0010116082181441060328108",  # TypeScript answer: 0.00101160821814261226
        "0",
        "0",
        "0",
        "-66.50639290498909424584894927",  # TypeScript answer: 66.50639290498909161897
        "-44.763640442758023997527072",  # TypeScript answer: 44.76364044275802100969
        "15314.34622907737339984651407914",  # TypeScript answer: -15314.34622907737339758683
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_unsettled_funding_values, frame, "UnsettledFunding")

    # # Typescript says: 11110884350128.58130511011427898893
    assert account.redeemable_pnl(frame).value == Decimal(
        "11110884.35012858130511256537630392"
    )

    # Typescript says: 15580162.40781940827396567784
    assert account.total_value(frame).value == Decimal(
        "15580162.4347419918016153588278228163"
    )

    # Typescript says: 0.07913870989902704878
    assert account.leverage(frame) == Decimal("0.0791387081247153498553556005902933099")

    assert not account.is_liquidatable(frame)


def test_account7() -> None:
    group, cache, account, open_orders = load_data_from_directory(
        "tests/testdata/account7"
    )
    frame = account.to_dataframe(group, open_orders, cache)

    # Typescript says: 16272272.28055547965738014682
    assert account.init_health(frame).value == Decimal(
        "16.2722722805554769752688793558604253"
    )

    # Typescript says: 16649749.17384252860704663135
    assert account.maint_health(frame).value == Decimal(
        "16.6497491738425205606631394095387232"
    )

    # Typescript says: 359.23329723261616663876
    assert account.init_health_ratio(frame) == Decimal(
        "359.233297232615934356690098616636253"
    )

    # Typescript says: 400.98177879921834687593
    assert account.maint_health_ratio(frame) == Decimal(
        "400.981778799217382934571016672694094"
    )

    expected_perp_asset_values = [
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_perp_asset_values, frame, "PerpAsset")

    expected_perp_liability_values = [
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_perp_liability_values, frame, "PerpLiability")

    expected_unsettled_funding_values = [
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_unsettled_funding_values, frame, "UnsettledFunding")

    # # Typescript says: 0
    assert account.redeemable_pnl(frame).value == Decimal("0")

    # Typescript says: 17.02722595090433088671
    assert account.total_value(frame).value == Decimal(
        "17.0272260671295641460573994632170211"
    )

    # Typescript says: 0.22169019545401269511
    assert account.leverage(frame) == Decimal("0.221690187114945806055453687883677967")

    assert not account.is_liquidatable(frame)


def test_account8() -> None:
    group, cache, account, open_orders = load_data_from_directory(
        "tests/testdata/account8"
    )
    frame = account.to_dataframe(group, open_orders, cache)

    # Typescript says: 337240882.73863372865950083224
    assert account.init_health(frame).value == Decimal(
        "337.240882738638250140157452733466665"
    )

    # Typescript says: 496326340.62213476397751321656
    assert account.maint_health(frame).value == Decimal(
        "496.326340622137024717841136284723945"
    )

    # Typescript says: 36.05147100711967311781
    assert account.init_health_ratio(frame) == Decimal(
        "36.0514710071205027252506258755278450"
    )

    # Typescript says: 53.05790488301020957351
    assert account.maint_health_ratio(frame) == Decimal(
        "53.0579048830105655659069541099688270"
    )

    expected_perp_asset_values = [
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_perp_asset_values, frame, "PerpAsset")

    expected_perp_liability_values = [
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_perp_liability_values, frame, "PerpLiability")

    expected_unsettled_funding_values = [
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
    ]
    __compare_series(expected_unsettled_funding_values, frame, "UnsettledFunding")

    # # Typescript says: 0
    assert account.redeemable_pnl(frame).value == Decimal("0")

    # # Typescript says: 655.41179779906788382959
    assert account.total_value(frame).value == Decimal(
        "655.411798505635799295524819835981215"
    )

    # Typescript says: 1.42725960097346415978
    assert account.leverage(frame) == Decimal("1.42725959841155987038895685868685529")

    assert not account.is_liquidatable(frame)


def test_account9() -> None:
    group, cache, account, open_orders = load_data_from_directory(
        "tests/testdata/account9"
    )
    frame = account.to_dataframe(group, open_orders, cache)

    # Typescript says: 96257596.93294236504926786324
    assert account.init_health(frame).value == Decimal(
        "96.25759693294275991712014716369911"
    )

    # # Typescript says: 511619124.36291981710078502488
    assert account.maint_health(frame).value == Decimal(
        "511.61912436291544183007238034887025"
    )

    # # Typescript says: 2.97693824341962454127
    assert account.init_health_ratio(frame) == Decimal(
        "2.97693824341971618997872883075634300"
    )

    # # Typescript says: 17.21126913561050741919
    assert account.maint_health_ratio(frame) == Decimal(
        "17.2112691356106767688292266736041770"
    )

    expected_perp_asset_values = [
        "500.04990000000077543970",  # TypeScript answer: 500.04990000000077543518
        "2.5236326049434386961181076",  # TypeScript answer: 2.52363260494343677465
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "638.8986403999995289363000",  # TypeScript answer: 638.89864039999952893822
        "3.9174126338586286841731976",  # TypeScript answer: 3.91741263385862836799
    ]
    __compare_series(expected_perp_asset_values, frame, "PerpAsset")

    expected_perp_liability_values = [
        "-495.17376736598619965572252857",  # TypeScript answer: 495.17376736598619757501
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "-2.17483424573713542372388474",  # TypeScript answer: 2.17483424573713435279
        "-561.66384985128874896711437574",  # TypeScript answer: 561.66384985128874873794
        "0",
    ]
    __compare_series(expected_perp_liability_values, frame, "PerpLiability")

    expected_unsettled_funding_values = [
        "0.0007598402777512624268905",  # TypeScript answer: -0.00075984027774822493
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0.0643417436628480437832391",  # TypeScript answer: -0.0643417436628475059
        "0",
    ]
    __compare_series(expected_unsettled_funding_values, frame, "UnsettledFunding")

    # # Typescript says: 86377134.1757902877071373382
    assert account.redeemable_pnl(frame).value == Decimal(
        "86.37713417579028770973051615"
    )

    # # Typescript says: 926.98053240315212875089
    assert account.total_value(frame).value == Decimal(
        "926.98065179288812374302461353404140"
    )

    # # Typescript says: 3.91944283828893702548
    assert account.leverage(frame) == Decimal("3.91944232844987663175000830924077777")

    assert not account.is_liquidatable(frame)


def test_account10() -> None:
    group, cache, account, open_orders = load_data_from_directory(
        "tests/testdata/account10"
    )
    frame = account.to_dataframe(group, open_orders, cache)

    # Typescript says: 835447528.00765534142685098118
    assert account.init_health(frame).value == Decimal(
        "835.46645800765893486219036355771104"
    )

    # # Typescript says: 1104560586.65938873999447622509
    assert account.maint_health(frame).value == Decimal(
        "1104.57951665938912571043538155175809"
    )

    # # Typescript says: 72.79490618339146124072
    assert account.init_health_ratio(frame) == Decimal(
        "72.7965556078356442718192409419052420"
    )

    # # Typescript says: 103.85025532240703682874
    assert account.maint_health_ratio(frame) == Decimal(
        "103.852035111906331055293099609661003"
    )

    expected_perp_asset_values = [
        "161.82500000000032969000",  # TypeScript answer: 161.82500000000032969183
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "794.2111854749995814000000",  # TypeScript answer: 794.21118547499958140179
        "0",
    ]
    __compare_series(expected_perp_asset_values, frame, "PerpAsset")

    expected_perp_liability_values = [
        "-173.90619573205822608841230366",  # TypeScript answer: 173.90619573205822590012
        "-24.39281775757780770256744063",  # TypeScript answer: 24.39281775757780579283
        "0",
        "-15.68883989096833131782204873",  # TypeScript answer: 15.68883989096832820564
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "-3.31116257349291076117481225",  # TypeScript answer: 3.31116257349290776801
        "-921.47040719505843175340943039",  # TypeScript answer: 921.47040719505843142656
        "-320.9761930508690390496440159",  # TypeScript answer: 320.97619305086903551683
    ]
    __compare_series(expected_perp_liability_values, frame, "PerpLiability")

    expected_unsettled_funding_values = [
        "2.993804267941609065673",  # TypeScript answer: -2.99380426794160570125
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "9.27420470494136462491496",  # TypeScript answer: -9.27420470494136139905
        "0",
    ]
    __compare_series(expected_unsettled_funding_values, frame, "UnsettledFunding")

    # # Typescript says: -503709430.72502483557941133085
    assert account.redeemable_pnl(frame).value == Decimal(
        "-503.70943072502483558303005156"
    )

    # # Typescript says: 1373.66979736174514670211
    assert account.total_value(frame).value == Decimal(
        "1373.69257531111931655868039954580515"
    )

    # # Typescript says: 2.22052732148808473767
    assert account.leverage(frame) == Decimal("2.22049050105379598429453331051484650")

    assert not account.is_liquidatable(frame)


def test_account11() -> None:
    group, cache, account, open_orders = load_data_from_directory(
        "tests/testdata/account11"
    )
    frame = account.to_dataframe(group, open_orders, cache)

    # Typescript says: 39961574027436.07695988276125120819
    assert account.init_health(frame).value == Decimal(
        "39961577.7541140575937901784660215036"
    )

    # # Typescript says: 46927302394129.7680569215865240551
    assert account.maint_health(frame).value == Decimal(
        "46927306.1208077677791283014235843010"
    )

    # # Typescript says: 58.58402019010213734873
    assert account.init_health_ratio(frame) == Decimal(
        "58.5840256534451777443158312211609930"
    )

    # # Typescript says: 72.54246867510758534081
    assert account.maint_health_ratio(frame) == Decimal(
        "72.5424744359848982880635960332503130"
    )

    expected_perp_asset_values = [
        "0",
        "9619318.95868651314757580577463614",  # TypeScript answer: 9619318.95868651314757258319
        "0",
        "42399491.9099689001359835982000",  # TypeScript answer: 42399491.90996890013586551049
        "0",
        "0",
        "0",
        "981.36318971222336926847873742",  # TypeScript answer: 981.3631897122233667119
        "16996.97999999999900922000",  # TypeScript answer: 16996.97999999999900921921
        "182875.91208141305408559981841751",  # TypeScript answer: 182875.91208141305408219068
        "0",
        "0",
        "5829.91485809974665610157628682",  # TypeScript answer: 5829.91485809974665599498
    ]
    __compare_series(expected_perp_asset_values, frame, "PerpAsset")

    expected_perp_liability_values = [
        "-8189.09699235532022899334735808",  # TypeScript answer: 8189.09699235532022854045
        "-4484552.3672399999998043969741",  # TypeScript answer: 4484552.3672399999998035014
        "-5114738.04900667368854212337076194",  # TypeScript answer: 5114738.04900667368854172423
        "-55898444.45343306971322517256987433",  # TypeScript answer: 55898444.4534330697132240573
        "0",
        "0",
        "0",
        "-601.22399999999873898624",  # TypeScript answer: 601.2239999999987389856
        "-16374.41774432560688035542287994",  # TypeScript answer: 16374.41774432560687912996
        "-71748.83339503044979153120000",  # TypeScript answer: 71748.83339503044979323931
        "0",
        "0",
        "-1418.1166999996928982050000",  # TypeScript answer: 1418.11669999969289790442
    ]
    __compare_series(expected_perp_liability_values, frame, "PerpLiability")

    expected_unsettled_funding_values = [
        "-4.61795774701042989870087054",  # TypeScript answer: 4.61795774701042915922
        "0",
        "7111.06002774763295324565867477",  # TypeScript answer: -7111.06002774763295093408
        "-42808.65865757522896625454159996",  # TypeScript answer: 42808.6586575752289647312
        "0",
        "0",
        "0",
        "-52.01280125205020596973781408",  # TypeScript answer: 52.01280125205020254953
        "36.973672535594410596360114",  # TypeScript answer: -36.9736725355944102489
        "1500.27980607061239707051995726",  # TypeScript answer: -1500.27980607061239481936
        "0",
        "0",
        "-303.7365587783103264314199573",  # TypeScript answer: 303.73655877831032512404
    ]
    __compare_series(expected_unsettled_funding_values, frame, "UnsettledFunding")

    # # Typescript says: -13370571519726.81616354968236848322
    assert account.redeemable_pnl(frame).value == Decimal(
        "-13370571.51972681616343017027689640"
    )

    # # Typescript says: 53893030.74839379973506936494
    assert account.total_value(frame).value == Decimal(
        "53893034.4875014779644664243811470993"
    )

    # # Typescript says: 1.27578614104216114811
    assert account.leverage(frame) == Decimal("1.27578605252723391668163890995627867")

    assert not account.is_liquidatable(frame)
