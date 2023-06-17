import re
species_of_interest = ['C', 'H', 'O', 'S']


def getSpeciesOfInterest(fuel_string: str) -> dict:
    """
    For each specie returns the number of atoms
    :param fuel_string: the composition formula of a fuel. If only one atom you have to specify 1. Ex: C1H4, not CH4
    :return: a dictionary {specie: number of atoms in the fuel}
    """
    fuel_split = re.split('(\d+)', fuel_string)
    if '' in fuel_split:
        fuel_split.remove('')
    if len(fuel_split) % 2:
        raise ValueError('Missing number of atoms for one species')

    result = {}
    for index in range(0, len(fuel_split), 2):
        if fuel_split[index] not in result:
            result[fuel_split[index]] = int(fuel_split[index + 1])
        else:
            result[fuel_split[index]] += int(fuel_split[index + 1])

    return result


def GetMoleFractionsFromEquivalenceRatio(equivalence_ratio: float, fuels: dict, oxidizers: dict) -> dict:
    nFuel = equivalence_ratio * sum(fuels.values())

    tot_nC = 0
    tot_nH = 0
    tot_nS = 0
    tot_nO = 0

    for fuel in fuels:
        token_species = getSpeciesOfInterest(fuel)

        nC = token_species['C'] if 'C' in token_species else 0
        nH = token_species['H'] if 'H' in token_species else 0
        nS = token_species['S'] if 'S' in token_species else 0
        nO = token_species['O'] if 'O' in token_species else 0

        tot_nC += nC * fuels[fuel]
        tot_nH += nH * fuels[fuel]
        tot_nS += nS * fuels[fuel]
        tot_nO += nO * fuels[fuel]

    n02 = ((2.0 * tot_nC) + (2.0 * tot_nS) + (0.5 * tot_nH) + (1.0 * tot_nO)) / 2

    moles_O2 = oxidizers['O2'] if 'O2' in oxidizers else oxidizers[list(oxidizers.keys())[0]]

    n_oxidizers = {oxi: (oxidizers[oxi] / moles_O2) * n02 for oxi in oxidizers}

    n = nFuel + sum(n_oxidizers.values())

    mole = {}

    for fuel in fuels:
        if fuel not in mole:
            mole[fuel] = equivalence_ratio * fuels[fuel] / n
        else:
            mole[fuel] += equivalence_ratio * fuels[fuel] / n

    for oxi in oxidizers:
        if oxi not in mole:
            mole[oxi] = n_oxidizers[oxi] / n
        else:
            mole[oxi] += n_oxidizers[oxi] / n

    return {x: round(mole[x], 6) for x in mole}

# my_fuels = {'N1H3': 1}
# my_oxidizers = {'O2': 0.25, 'N2': 0.75}
# phi = 2.0

# my_fuels = {'C1H4': 1}
# my_oxidizers = {'AR': 0.4, 'HE': 0.6}
# phi = 0.5
#
# m = GetMoleFractionsFromEquivalenceRatio(equivalence_ratio=phi, fuels=my_fuels, oxidizers=my_oxidizers)
# print(m)
