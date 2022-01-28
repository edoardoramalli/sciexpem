from ExperimentManager.Models import *
from django.db.models import Q
from ReSpecTh.units import convert_list

def create_profile_string(a_name: str, a_value: float, a_unit: str,
                          b_name: str, b_value: float, b_unit: str,
                          x_name: str, x_unit: str, x_data,
                          y_name: str, y_unit: str, y_data,
                          delimiter=';'):
    if len(x_data) != len(y_data):
        raise ValueError('Invalid profile data')
    elif len(x_data) == 0:
        raise ValueError('Invalid profile data')

    profile_text = ''
    profile_text += a_name + delimiter + str(a_value) + ' ' + a_unit + '\n'
    profile_text += b_name + delimiter + str(b_value) + ' ' + b_unit + '\n'
    profile_text += x_name + delimiter + ' ' + x_unit + '\n'
    profile_text += y_name + delimiter + ' ' + y_unit + '\n'
    profile_text += 'profile;' + '\n'

    for index in range(len(x_data)):
        profile_text += str(float(x_data[index])) + delimiter + str(float(y_data[index])) + '\n'

    return profile_text


def create_list_string_profiles(exp_id):
    profiles = DataColumn.objects.filter(Q(experiment__id=exp_id) & ~Q(data_group_profile=None))

    profile_result = {}

    for profile in profiles:
        row_numbers = [int(row_number) for row_number in profile.data_group_profile]

        for row in row_numbers:
            num = row - 1
            if num not in profile_result:
                profile_result[num] = [profile]
            else:
                if profile not in profile_result[num]:
                    if profile.name == 'time':
                        profile_result[num].insert(0, profile)
                    else:
                        profile_result[num].append(profile)

    query_initial = DataColumn.objects.filter(experiment__id=exp_id, dg_label='initial_condition')

    if not 0 < len(query_initial) < 3:
        raise ValueError('error initial conditions')

    a = query_initial[0]
    b = query_initial[1]

    if a.name != 'temperature':
        c = a
        a = b
        b = c

    # ASSUMO CHE A si T e B pressione

    a_name = a.name
    a_unit = a.units
    a_desired_unit = 'K'
    a_data = convert_list(my_list=a.data, unit=a_unit, desired_unit=a_desired_unit)

    b_name = b.name
    b_unit = b.units
    b_desired_unit = 'Pa'
    b_data = convert_list(my_list=b.data, unit=b_unit, desired_unit=b_desired_unit)

    r = []

    for index in range(len(a.data)):
        x = profile_result[index][0]
        y = profile_result[index][1]

        if x.name != 'time' and x.name != 'length':
            zz = x
            x = y
            y = zz

        r.append(create_profile_string(a_name=a_name, a_value=a_data[index], a_unit=a_desired_unit,
                                       b_name=b_name, b_value=b_data[index], b_unit=b_desired_unit,
                                       x_name=x.name, x_unit=x.units, x_data=x.data,
                                       y_name=y.name, y_unit=y.units, y_data=y.data))

    return r
