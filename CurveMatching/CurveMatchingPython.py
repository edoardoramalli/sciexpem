# Built-In Packages
import sys
import pathlib
import os

# Third parties Packages
from ctypes import c_int, c_double, c_int16, c_void_p, c_char_p, byref, cdll
import numpy as np


class CurveMatching:

    @staticmethod
    def get_parameter(**kwargs):
        class parameter:
            # Order of the basis functions
            m = 4
            # Degree of the basis functions
            g = 3

            # Orders of magnitude of difference between the smallest and the largest
            # possible value of the smoothing parameter lambda
            lambdaSearchInterval = 6

            # Number of steps in the for cycle for minimizing the smoothing parameter lambda
            numberOfStepsLambda = 13

            # Fraction of the range of a spline on the y-axis for determining which
            # segments of the spline count as asymptotes. If the oscillations of the spline
            # at one of its extremities are contained within a horizontal area with size
            # determined by this value, the corresponding segment is identified as an asymptote
            fractionOfOrdinateRangeForAsymptoteIdentification = 0.005

            # Fraction of the range of a spline on the y-axis for determining which pos
            # count as well-defined maxima. In order to be considered a well-defined maximum,
            # a po in a spline must not only have first derivative equal to 0 and negative
            # second derivative, it must also be sufficiently distant from the two surrounding
            # minima. The minimum admissible distance is determined using this variable
            fractionOfOrdinateRangeForMaximumIdentification = 0.025

            # Fraction of the range of the experimental data on the y-axis for determining
            # whether a model can be considered a flat line with ordinate = 0 when compared to
            # the experimental data. This is useful for identifying situations that are
            # problematic for the calculation of the similarity indexes
            fractionOfExpHeightForZeroLineIdentification = 0.02

            # Minimum range on the x-axis of the models, before the addition of segments at
            # the extremes, required for comparison with the experimental data, expressed as a
            # fraction of the range of the experimental data on the x-axis
            fractionOfExpRangeForModelExtrapolation = 0.5

            # Fraction of the range of the experimental data on the x-axis used to
            # calculate the minimum shift possible
            fractionOfExpRangeForMinShift = 0.005

            # Fraction of the range of the experimental data on the x-axis used to shift
            # the models around the position of perfect alignment between their well-defined
            # maximum and the well-defined maximum of the experimental data
            fractionOfExpRangeForShiftAroundMaximum = 0.05

            # Specifies whether negative segments on the y-axis are admissible for the
            # splines or whether they should be replaced with straight lines with ordinate 0

            possibleNegativeOrdinates = False

            # Number of plausible versions of the experimental data generated during the
            # bootstrap procedure. numberOfBootstrapVariations = 1 : no bootstrap
            numberOfBootstrapVariations = 20

            # Specifies whether the program should attempt to line up the maxima of
            # experimental data and models during the shift procedure
            lineUpMaxima = True

            # Specifies whether the program should use the sum of the four dissimilarity
            # indexes when calculating the shift, thus finding a single shift amount, or
            # whether the program should consider each of the four indexes separately, thus
            # obtaining four different values for the shift
            useSumOfIndexesForAlignment = True

            # Number of trapezoids for the numerical calculation of the indexes
            numberOfTrapezoids = 99

            # Default value for the relative experimental error. Used in case relative
            # errors are not provided along with the experimental data
            defaultRelativeError = 0.1

            #################################################################################
            #################################################################################

        parameters = parameter()
        parameters.__dict__.update(kwargs)

        return parameters

    @staticmethod
    def listToArray(ll):
        return (c_double * len(ll))(*ll)

    @staticmethod
    def getValue(list_indexes, model, index, variation, n_models, n_variations):
        return list_indexes[((n_models * n_variations) * index) + variation * n_models + model]

    @staticmethod
    def dictToPoint(diz):
        x = diz.keys()[0]
        y = diz[x]
        return x, y

    @staticmethod
    def my_zip(x_list, y_list):
        result = {}
        for index, x_i in enumerate(x_list):
            if x_i not in result:
                result[x_i] = y_list[index]
            else:
                result[x_i] = (result[x_i] + y_list[index]) / 2
        return result

    @staticmethod
    def execute(x_exp, y_exp, x_sim, y_sim,
                uncertainty=[],
                calculate_shift=True,
                verbose=False,
                library_path=os.path.join(pathlib.Path(__file__).parent.absolute(), "CurveMatchingPython.o"),
                **kwargs):

        try:
            c_library = cdll.LoadLibrary(library_path)
        except OSError:
            raise OSError("Unable to load the system C library")

        c_library.curveMatching.argtypes = [c_int,
                                            c_int,
                                            c_double,
                                            c_int,
                                            c_double,
                                            c_double,
                                            c_double,
                                            c_double,
                                            c_double,
                                            c_double,
                                            c_int16,
                                            c_int,
                                            c_int16,
                                            c_int16,
                                            c_int,
                                            c_int16,
                                            # c_void_p,
                                            c_void_p,
                                            c_void_p,
                                            c_void_p,
                                            c_void_p,
                                            c_int,
                                            c_void_p,
                                            c_void_p,
                                            c_int,
                                            c_void_p]

        n_models = 1
        n_indexes = 5

        parameters = CurveMatching.get_parameter(**kwargs)

        if len(x_exp) != len(y_exp) or (len(uncertainty) != len(x_exp) if uncertainty else False):
            # Case mismatch length simulation and experiment
            raise ValueError("Mismatched length x_exp, y_exp, uncertainty")

        if len(x_sim) != len(y_sim):
            # Case mismatch length simulation and experiment
            raise ValueError("Mismatched length simulation and experiment")

        # Check if single point
        if len(x_exp) == 1:
            if len(x_sim) == 1:
                # Case Single Point
                a = (x_exp[0], y_exp[0])
                b = (x_sim[0, y_sim[0]])
                dist = np.linalg.norm(a - b)
                return dist, 0  # TODO Adjust error
            else:
                # Case mismatch length simulation and experiment
                return -2, 0

        # Check if all elements of simulation are the same --> Model limitation
        if len(set(y_sim)) == 1:
            return -3, 0

        # return_array_indexes = (c_double * (self.numberOfBootstrapVariations * n_models * n_indexes))()
        return_array_scores = (c_double * n_models)()
        return_array_errors = (c_double * n_models)()

        experiment_diz = CurveMatching.my_zip(x_list=x_exp, y_list=y_exp)
        experiment_error_diz = CurveMatching.my_zip(x_list=x_exp,
                                                    y_list=[parameters.defaultRelativeError] * len(x_exp) if uncertainty == [] else uncertainty)

        sim_diz = CurveMatching.my_zip(x_list=x_sim, y_list=y_sim)

        x_experiment = CurveMatching.listToArray(sorted(experiment_diz.keys()))
        y_experiment = CurveMatching.listToArray([experiment_diz[key] for key in sorted(experiment_diz.keys())])
        relative_error = CurveMatching.listToArray(
            [experiment_error_diz[key] for key in sorted(experiment_error_diz.keys())])

        x_simulation = CurveMatching.listToArray(sorted(sim_diz.keys()))
        y_simulation = CurveMatching.listToArray([sim_diz[key] for key in sorted(sim_diz.keys())])

        c_library.curveMatching(
            c_int(parameters.m),
            c_int(parameters.g),
            c_double(parameters.lambdaSearchInterval),
            c_int(parameters.numberOfStepsLambda),
            c_double(parameters.fractionOfOrdinateRangeForAsymptoteIdentification),
            c_double(parameters.fractionOfOrdinateRangeForMaximumIdentification),
            c_double(parameters.fractionOfExpHeightForZeroLineIdentification),
            c_double(parameters.fractionOfExpRangeForModelExtrapolation),
            c_double(parameters.fractionOfExpRangeForMinShift),
            c_double(parameters.fractionOfExpRangeForShiftAroundMaximum),
            c_int16(parameters.possibleNegativeOrdinates),
            c_int(parameters.numberOfBootstrapVariations),
            c_int16(parameters.lineUpMaxima),
            c_int16(parameters.useSumOfIndexesForAlignment),
            c_int(parameters.numberOfTrapezoids),
            c_int16(calculate_shift),
            # ctypes.byref(return_array_indexes),
            byref(return_array_scores),
            byref(return_array_errors),
            x_experiment,
            y_experiment,
            c_int(len(experiment_diz.keys())),
            x_simulation,
            y_simulation,
            c_int(len(sim_diz.keys())),
            relative_error)

        # indexes = [x for x in return_array_indexes]
        score = return_array_scores[0]
        error = return_array_errors[0]

        if verbose:
            print("Curve Matching - Score: ", score, " - Error: ", error)

        return score, error
