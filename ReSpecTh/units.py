from pint import UnitRegistry
import math
from ReSpecTh.Tool import applyTransformation
u_reg = UnitRegistry()


def convert_list(my_list: list, unit: str, desired_unit: str) -> list:
    tmp = [float(y) for y in my_list] * u_reg(unit)
    return [x.to(u_reg(desired_unit)).magnitude for x in tmp]


def convert(list_a: list, unit_a: str, list_b: list, unit_b: str, plotscale: str = 'lin') -> (list[float], list[float]):
    if plotscale is not None and plotscale not in ['lin', 'log', 'log10', 'ln', 'inv']:
        raise ValueError("convert. Plotscale type '{}' is not valid.".format(plotscale))

    plotscale = plotscale if plotscale is not None else 'lin'

    # Trasformo una delle due due liste nell'unità dell'altra

    list_b = convert_list(my_list=list_b, unit=unit_b, desired_unit=unit_a)

    # Applico la transformazione

    list_a = applyTransformation(list_a, plotscale)
    list_b = applyTransformation(list_b, plotscale)

    return list_a, list_b

