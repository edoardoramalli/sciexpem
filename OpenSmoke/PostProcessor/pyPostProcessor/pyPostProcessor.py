from ctypes import c_int, c_double, c_void_p, c_char_p, byref, cdll

import os
import pathlib
import math



class Setting:
    ROPA = 0
    Sensitivity = 1

    ROPA_local = 0
    ROPA_global = 1
    ROPA_region = 2


def load_library(library_path=os.path.join(pathlib.Path(__file__).parent.absolute(), "pyPostProcessor.o")):
    c_library = cdll.LoadLibrary(library_path)


    c_library.pyPostProcessor.argtypes = [c_char_p,
                                          c_char_p,
                                          c_char_p,
                                          c_int,
                                          c_int,
                                          c_double,
                                          c_double,
                                          c_double,
                                          c_void_p,
                                          c_void_p,
                                          c_int]

    c_library.pyPostProcessor.restype = c_int

    return c_library


def compute_ropa(kineticFolder, outputFolder, specie, ROPA_type, local_value=0.0, lower_bound=0.0, upper_bound=0.0, n_reaction=10):
    if type(kineticFolder) != bytes:
        kineticFolder = bytes(kineticFolder, 'utf-8')
    if type(outputFolder) != bytes:
        outputFolder = bytes(outputFolder, 'utf-8')
    if type(specie) != bytes:
        specie = bytes(specie, 'utf-8')

    c_library = load_library()

    coefficients = (c_double * n_reaction)()
    reactions = (c_int * n_reaction)()

    code = c_library.pyPostProcessor(c_char_p(kineticFolder),
                                     c_char_p(outputFolder),
                                     c_char_p(specie),
                                     c_int(Setting.ROPA),
                                     c_int(ROPA_type),
                                     c_double(local_value),
                                     c_double(lower_bound),
                                     c_double(upper_bound),
                                     byref(coefficients),
                                     byref(reactions),
                                     c_int(n_reaction))

    coefficients = [0 if math.isnan(i) else i for i in coefficients]
    reactions = [r for r in reactions]

    if code == 0:
        return coefficients, reactions
    else:
        raise ValueError('Error pyPostProcessor - Code {}'.format(code))


# kineticFolder = b"/Users/edoardo/Downloads"
# outputFolder = b"/Users/edoardo/Downloads"
# specie = b"H2"
#
#
# a, b = compute_ropa(kineticFolder=kineticFolder, outputFolder=outputFolder, specie=b'C7H8', ROPA_type=Setting.ROPA_global)
# #
# print(a, b)


# FOR LINUx
# g++ -std=c++17 -O3 -Wall -DNDEBUG -shared -fPIC  -w  -I /usr/include/eigen3 -I /home/eramalli/.opensmoke/source_code_opensmoke/source/  main.cpp CollectionOfClasses.cpp PostProcessor.cpp -o pyPostProcessor.o -lboost_filesystem -L /usr/local/lib