from ctypes import c_int, c_double, c_int16, c_void_p, c_char_p, byref, cdll


def spline(x_data, y_data, x: list, splineType=0, numberOfAbscissaeSeparatingConsecutiveKnots=0):
    x_data = list(x_data)
    y_data = list(y_data)

    # splineType --> Type of spline. 0: Experimental data;  1: Model;  2: Error spline */
    # numberOfAbscissaeSeparatingConsecutiveKnots --> 0, 2, 5

    if len(x_data) != len(y_data):
        raise ValueError('Lunghezza differente')

    if type(x) != list:
        x = [x]

    x = list(x)

    try:
        c_library = cdll.LoadLibrary('Spline.o')
    except OSError:
        raise OSError("Unable to load the system C library")

    c_library.edoardo.argtypes = [c_void_p, c_void_p, c_int, c_void_p, c_void_p, c_int, c_int, c_int]

    x_data_c = (c_double * len(x_data))(*x_data)
    y_data_c = (c_double * len(y_data))(*y_data)
    data_len = c_int(len(x_data))

    x_points_c = (c_double * len(x))(*x)
    x_results_c = (c_double * len(x))()
    results_len = c_int(len(x))

    splineType = c_int(splineType)
    numberOfAbscissaeSeparatingConsecutiveKnots = c_int(numberOfAbscissaeSeparatingConsecutiveKnots)

    # start = time.time()
    c_library.edoardo(x_data_c, y_data_c, data_len,
                      x_points_c, byref(x_results_c),
                      results_len, splineType, numberOfAbscissaeSeparatingConsecutiveKnots)
    # end = time.time() - start
    # print('Call {} sec.', end)
    return [r for r in x_results_c]
