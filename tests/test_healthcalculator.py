from .data import load_data_from_directory

from decimal import Decimal


def test_empty() -> None:
    group, cache, account, open_orders = load_data_from_directory(
        "tests/testdata/empty"
    )
    frame = account.to_dataframe(group, open_orders, cache)

    # Typescript says: 0
    assert account.init_health(frame) == Decimal("0")

    # Typescript says: 0
    assert account.maint_health(frame) == Decimal("0")

    # Typescript says: 100
    assert account.init_health_ratio(frame) == Decimal("100")

    # Typescript says: 100
    assert account.maint_health_ratio(frame) == Decimal("100")

    # Typescript says: 0
    assert account.total_value(frame) == Decimal("0")

    # Typescript says: 0
    assert account.leverage(frame) == Decimal("0")

    assert not account.is_liquidatable(frame)


def test_1deposit() -> None:
    group, cache, account, open_orders = load_data_from_directory(
        "tests/testdata/1deposit"
    )
    frame = account.to_dataframe(group, open_orders, cache)

    # Typescript says: 37904260000.05905822642118252475
    assert account.init_health(frame) == Decimal(
        "37904.2600000591928892771752953600134"
    )

    # Typescript says: 42642292500.06652466908819931746
    assert account.maint_health(frame) == Decimal(
        "42642.2925000665920004368222072800150"
    )

    # Typescript says: 100
    assert account.init_health_ratio(frame) == Decimal("100")

    # Typescript says: 100
    assert account.maint_health_ratio(frame) == Decimal("100")

    # Typescript says: 47380.32499999999999928946
    assert account.total_value(frame) == Decimal(
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
    assert account.init_health(frame) == Decimal("454.88428115521887496581258174978975")

    # Typescript says: 901472688.63722587052636470162
    assert account.maint_health(frame) == Decimal(
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

    # Typescript says: 1348.25066158888197520582
    assert account.total_value(frame) == Decimal(
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
    assert account.init_health(frame) == Decimal("7516.1596048492430563556697582309637")

    # Typescript says: 9618709877.45119083596852505025
    assert account.maint_health(frame) == Decimal(
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

    # Typescript says: 11721.35669142618275273549
    assert account.total_value(frame) == Decimal(
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
    assert account.init_health(frame) == Decimal("341025.33362550396263557255539801613")

    # Typescript says: 683477170424.20340250929429970483
    assert account.maint_health(frame) == Decimal(
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

    # Typescript says: 1025929.00722205438034961844
    assert account.total_value(frame) == Decimal(
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
    assert account.init_health(frame) == Decimal(
        "-848086.87648706716344229365643382143"
    )

    # Typescript says: -433869053006.07361789143756070075
    assert account.maint_health(frame) == Decimal(
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

    # Typescript says: -19651.22952604663374742699
    assert account.total_value(frame) == Decimal("-19651.22952512716345506257487062143")

    # Typescript says: -421.56937094643044972031
    assert account.leverage(frame) == Decimal("-421.569370966155451390856326152441566")

    assert account.is_liquidatable(frame)


def test_account5() -> None:
    group, cache, account, open_orders = load_data_from_directory(
        "tests/testdata/account5"
    )
    frame = account.to_dataframe(group, open_orders, cache)

    # Typescript says: 15144959918141.09175135195858530324
    assert account.init_health(frame) == Decimal(
        "15144959.9181410924496111317578727438"
    )

    # Typescript says: 15361719060997.68276021614036608298
    assert account.maint_health(frame) == Decimal(
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

    # Typescript says: 15578478.17337437202354522015
    assert account.total_value(frame) == Decimal(
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
    assert account.init_health(frame) == Decimal(
        "14480970.0692383312566073701425189089"
    )

    # Typescript says: 15030566.251990.17026082618337312624
    assert account.maint_health(frame) == Decimal(
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

    # Typescript says: 15580162.40781940827396567784
    assert account.total_value(frame) == Decimal(
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
    assert account.init_health(frame) == Decimal(
        "16.2722722805554769752688793558604253"
    )

    # Typescript says: 16649749.17384252860704663135
    assert account.maint_health(frame) == Decimal(
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

    # Typescript says: 17.02722595090433088671
    assert account.total_value(frame) == Decimal(
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
    assert account.init_health(frame) == Decimal(
        "337.240882738638250140157452733466665"
    )

    # Typescript says: 496326340.62213476397751321656
    assert account.maint_health(frame) == Decimal(
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

    # # Typescript says: 655.41179779906788382959
    assert account.total_value(frame) == Decimal(
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
    assert account.init_health(frame) == Decimal("96.25759693294275991712014716369911")

    # # Typescript says: 511619124.36291981710078502488
    assert account.maint_health(frame) == Decimal(
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

    # # Typescript says: 926.98053240315212875089
    assert account.total_value(frame) == Decimal("926.98065179288812374302461353404140")

    # # Typescript says: 3.91944283828893702548
    assert account.leverage(frame) == Decimal("3.91944232844987663175000830924077777")

    assert not account.is_liquidatable(frame)
