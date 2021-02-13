from pint import UnitRegistry
u_reg = UnitRegistry()


def covert_list(my_list: list, unit: str, desired_unit: str) -> list:
    tmp = [float(y) for y in my_list] * u_reg(unit)
    return [x.to(u_reg(desired_unit)).magnitude for x in tmp]
