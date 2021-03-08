def data():
    from hx711 import HX711
    import datetime

    hx = HX711(5, 6)
    hx.set_gain(128)
    hx.tare()

    for i in range(10):
        start = datetime.datetime.now()
        a = hx.get_weight()
        stop = datetime.datetime.now()
        time_ = stop - start
        time_ = time_.total_seconds()
        print(time_)