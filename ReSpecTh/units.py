from pint import UnitRegistry
import math
from django.conf import settings
from ReSpecTh.Tool import applyTransformation
import os
u_reg = UnitRegistry()
u_reg.load_definitions(os.path.join(settings.BASE_DIR, "Files/unit"))


def convert_list(my_list: list, unit: str, desired_unit: str) -> list:
    unit = unit.replace(' ', '')
    desired_unit = desired_unit.replace(' ', '')
    tmp = [float(y) for y in my_list] * u_reg(unit)
    return [x.to(u_reg(desired_unit)).magnitude for x in tmp]


def convert(list_a: list, unit_a: str, list_b: list, unit_b: str, plotscale: str = 'lin') -> (list[float], list[float]):
    if plotscale is not None and plotscale not in ['lin', 'log', 'log10', 'ln', 'inv']:
        raise ValueError("convert. Plotscale type '{}' is not valid.".format(plotscale))  # TODO custom exception

    plotscale = plotscale if plotscale is not None else 'lin'

    # Trasformo una delle due due liste nell'unità dell'altra

    list_b = convert_list(my_list=list_b, unit=unit_b, desired_unit=unit_a)

    # Applico la transformazione

    list_a = applyTransformation(list_a, plotscale)
    list_b = applyTransformation(list_b, plotscale)

    return list_a, list_b

