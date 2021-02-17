from pint import UnitRegistry
import math
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

    if plotscale == 'lin':
        pass
    elif plotscale == 'log' or plotscale == 'log10':
        list_a = [math.log10(x) for x in list_a]
        list_b = [math.log10(x) for x in list_b]
    elif plotscale == 'inv':
        list_a = [1/x for x in list_a]
        list_b = [1/x for x in list_b]
    elif plotscale == 'ln':
        list_a = [math.log(x, math.e) for x in list_a]
        list_b = [math.log(x, math.e) for x in list_b]

    return list_a, list_b

