import xml.etree.ElementTree as ET
import pandas as pd
import xmltodict
from django.conf import settings
import os
from functools import reduce


class ReSpecThParser:
    def __init__(self, tree):
        self.tree = tree
        self.root = self.tree.getroot()

    @property
    def apparatus(self):
        a = self.root.find("./apparatus/kind")
        if a is None:
            return None
        return a.text

    @property
    def experiment_type(self):
        e = self.root.find("./experimentType")
        if e is None:
            return None
        return e.text

    @property
    def fileDOI(self):
        e = self.root.find("./fileDOI")
        if e is None:
            return None
        return e.text

    @property
    def fileAuthor(self):
        e = self.root.find("./fileAuthor")
        if e is None:
            return None
        return e.text

    def getBiblio(self):
        e = self.root.find("./bibliographyLink/description")
        return e.text

    def get_common_property(self, s):
        return self.root.find("./commonProperties/property/[@name='%s']" % s)

    def valid_ignition_type(self, ignition_type):
        if ignition_type is not None:
            types = [x.strip() for x in
                     open(os.path.join(settings.BASE_DIR, "Files/ignition_definition_types")).read().split("\n")]

            target = [[i.strip() for i in x.strip().split(",")]
                      for x in
                      open(os.path.join(settings.BASE_DIR, "Files/ignition_definition_measured_quantity")).read().
                          split("\n")]
            c_type = ignition_type.attrib.get("type")
            c_target = ignition_type.attrib.get("target").replace(";", "")
            if c_type not in types:
                raise ValueError("Ignition type '%s' is not valid. Possible values are: %s" % (c_type, str(types)))
            c_target_result = None
            for ll in target:
                if c_target in ll:
                    c_target_result = ll[0]
                    break
            if c_target_result is None:
                raise ValueError("Ignition target '%s' is not valid. Possible values are: %s" % (c_target, str(target)))
            return str(c_target_result) + "-" + str(c_type)
        else:
            return None

    def get_ignition_type(self):
        return self.valid_ignition_type(self.root.find("./ignitionType"))

    def get_common_property_value_units(self, s):
        element = self.get_common_property(s)
        if element is None:
            return None, None
        value = element.find("value").text
        unit = element.attrib['units']
        return value, unit

    def _extract_columns(self):
        # columns: a dict like {column1 : {dict column 1}, column2 : {dict column 2}, ... }
        # where keys are "preferredKey" if available, "name otherwise"
        columns = {p.find("speciesLink").attrib['preferredKey'] if p else p.attrib['name']: p.attrib for p in
                   self.root.findall("./dataGroup/property")}
        return columns

    def extract_data(self):
        # columns are "preferredKey" if available, "name otherwise"
        columns = [p.find("speciesLink").attrib['preferredKey'] if p else p.attrib['name'] for p in
                   self.root.findall("./dataGroup/property")]

        columns_data = []
        for dp in self.root.findall("./dataGroup/dataPoint"):
            columns_data.append([float(p.text) for p in dp.findall("./")])

        return pd.DataFrame.from_records(columns_data, columns=columns)

    # # DEPRECATED
    # def extract_initial_composition(self):
    #     initial_composition = dict()
    #     for component in self.get_common_property("initial composition"):
    #         initial_composition[component.find('speciesLink').attrib['preferredKey']] = component.find('amount').text
    #     return initial_composition

    def initial_composition(self):
        initial_composition = self.get_common_property("initial composition")
        if not initial_composition:
            return []

        initial_species = []
        for component in initial_composition:
            name = component.find('speciesLink').attrib.get('preferredKey')
            value = component.find('amount').text
            # cas = component.find('speciesLink').attrib.get('CAS')
            units = component.find('amount').attrib.get("units")
            # initial_specie = {"name": name, "value": value, "cas": cas, "units": units}
            initial_specie = {"name": name, "value": value, "units": units}

            initial_species.append(initial_specie)
        return initial_species

    def includes_comp(self, name):
        ic = self.initial_composition()
        for i in ic:
            if i['name'] == name:
                return True

    def common_properties(self):  # not initial composition
        common_properties = self.root.find("./commonProperties")
        if not common_properties:
            return []

        props = []
        for prop in common_properties:  # IMPROVABLE IN XML TO DISCARD initial comp. directly
            name = prop.attrib.get("name")
            if not name or name == 'initial composition':
                continue
            units = prop.attrib.get("units")
            value = prop.find("value").text
            # sourcetype = prop.attrib.get("sourcetype")
            # props.append({"name": name, "units": units, "value": value, "sourcetype": sourcetype})
            props.append({"name": name, "units": units, "value": value})
        return props

    # # deprecated
    # def extract_columns(self):
    #     columns = []
    #     dataGroup = self.root.find("dataGroup")
    #     for prop in dataGroup.findall("property"):
    #         name = prop.attrib.get('name')
    #         units = prop.attrib.get('units')
    #         label = prop.attrib.get('label')
    #
    #         species = None
    #         xml_species = prop.findall('speciesLink')
    #         if xml_species:
    #             species = [specie.attrib['preferredKey'] for specie in xml_species]
    #
    #         data = [float(dp.find(prop.attrib['id']).text) for dp in dataGroup.findall('dataPoint')]
    #         columns.append({'name': name, "units": units, "label": label, "species": species, "data": data})
    #
    #     return columns

    def extract_columns_multi_dg(self):
        dataGroups = self.root.findall("dataGroup")
        result = []
        for dataGroup in dataGroups:
            dg_id = dataGroup.attrib['id']
            dg_columns = []

            for prop in dataGroup.findall("property"):
                name = prop.attrib.get('name')
                units = prop.attrib.get('units')
                label = prop.attrib.get('label')


                ignore = prop.attrib.get('ignore') if prop.attrib.get('ignore') is not None else False
                nominal = prop.attrib.get('nominal')
                plotscale = prop.attrib.get('plotscale') if prop.attrib.get('plotscale') is not None else "lin"

                species = None
                xml_species = prop.findall('speciesLink')
                if xml_species:
                    species = [specie.attrib['preferredKey'] for specie in xml_species]

                data = [float(dp.find(prop.attrib['id']).text) for dp in dataGroup.findall('dataPoint')]
                dg_columns.append(
                    {'name': name, "units": units, "label": label,
                     "species": species, "data": data, "dg_id": dg_id,
                     'ignore': ignore, 'nominal': nominal, 'plotscale': plotscale})

                # extract dataPoint attributes
            dataPoints = dataGroup.findall('dataPoint')
            dp_attributes = dataPoints[0].attrib
            for k in dp_attributes.keys():
                data = [float(dp.attrib[k]) for dp in dataPoints]
                dg_columns.append(
                    {'name': k, "units": "unitless", "label": k, "species": None, "data": data, "dg_id": dg_id,
                     'ignore': False, 'nominal': None, 'plotscale': 'lin'})

            result.append(dg_columns)
        return result

    def extract_uncertainties(self):
        columns = []
        dataGroup = self.root.find("dataGroup")
        at = dataGroup.findall("property[@name='uncertainty']") + dataGroup.findall("uncertainty")
        for uncertainty in at:
            units = uncertainty.attrib.get('units')
            label = uncertainty.attrib.get('label')
            reference = uncertainty.attrib.get('reference')
            bound = uncertainty.attrib.get('bound')
            kind = uncertainty.attrib.get('kind')

            data = [float(dp.find(uncertainty.attrib['id']).text) for dp in dataGroup.findall('dataPoint')]
            columns.append(
                {'reference': reference, "units": units, "label": label, "bound": bound, "kind": kind, "data": data})

        return columns

    # # DEPRECATED
    # def extract_data_groups(self):
    #     return [xmltodict.parse(ET.tostring(dg), attr_prefix="") for dg in self.root.findall("./dataGroup")]

    @classmethod
    def from_file(cls, path):
        tree = ET.parse(path)
        return cls(tree)

    @classmethod
    def from_string(cls, string):
        tree = ET.ElementTree(ET.fromstring(string))
        return cls(tree)


class Property:
    def __init__(self, names, symbols, units):
        self.names = names
        self.symbols = symbols
        self.units = units

    def __repr__(self):
        return str(self.names) + " = " + str(self.symbols) + " = " + str(self.units)


class ReSpecThValidProperty:

    def __init__(self, file=os.path.join(settings.BASE_DIR, "Files/prop")):
        self.props = []
        with open(file, 'r') as file:
            for line in file:
                if line.startswith("#"):
                    continue
                line_split = line.strip().split("=")
                names_list = [name.strip().lower() for name in line_split[0].split(",")]
                symbols_list = [symbol.strip() for symbol in line_split[1].split(",") if symbol.strip()]
                units_list = [unit.strip() for unit in line_split[2].split(",")]

                self.insertUnique(Property(names_list, symbols_list, units_list))

    def insertUnique(self, prop):
        candidate_names = set(prop.names)
        candidate_symbols = set(prop.symbols)

        for prop_inserted in self.props:
            c_prop_names = set(prop_inserted.names)
            c_prop_symbols = set(prop_inserted.symbols)
            if candidate_names.intersection(c_prop_names) or candidate_symbols.intersection(c_prop_symbols):
                raise ValueError("Name or Symbol not unique! " + str(candidate_names) + " = " + str(candidate_symbols))

        self.props.append(prop)

    def getSymbol(self, name):
        name = name.lower()
        for prop in self.props:
            if name in prop.names:
                return prop.symbols[0]

    def isValidName(self, name):
        name = name.lower()
        for prop in self.props:
            if name in prop.names:
                return True
        return False

    def isValidSymbol(self, symbol):
        for prop in self.props:
            if symbol in prop.symbols:
                return True
        return False

    def isValidSymbolName(self, symbol, name):
        name = name.lower()
        for prop in self.props:
            if symbol in prop.symbols and name in prop.names:
                return True
        return False

    def isValid(self, unit, symbol=None, name=None):
        if symbol is None and name is None:
            return False
        elif symbol is not None and name is not None:
            for prop in self.props:
                if symbol in prop.symbols and name in prop.names and unit in prop.units:
                    return True
            return False
        elif symbol is not None and name is None:
            for prop in self.props:
                if symbol in prop.symbols and unit in prop.units:
                    return True
            return False
        elif symbol is None and name is not None:
            for prop in self.props:
                if name in prop.names and unit in prop.units:
                    return True
            return False


class ReSpecThValidSpecie:

    def __init__(self, file=os.path.join(settings.BASE_DIR, "Files/Nomenclatura_originale_POLIMI.txt")):
        self.species = []  # Species name list in UPPERCASE only
        with open(file, "r") as file:
            file.readline()
            file.readline()
            for line in file:
                line_split = line.strip().split()
                self.species.append(line_split[2])

    def isValid(self, name):
        if type(name) is list:
            return reduce(lambda x, y: x and (y.upper() in self.species), name, True)
        else:
            return name.upper() in self.species


class ReSpecThValidExperimentType:

    def __init__(self, file=os.path.join(settings.BASE_DIR, "Files/experiment_type")):
        self.experiment_type = []  # Species name list in LOWERCASE only
        with open(file, "r") as file:
            for line in file:
                self.experiment_type.append(line.strip())

    def isValid(self, name):
        return name.lower() in self.experiment_type


class ReSpecThValidReactorType:

    def __init__(self, file=os.path.join(settings.BASE_DIR, "Files/reactor")):
        self.reactor_type = []  # Species name list in LOWERCASE only
        with open(file, "r") as file:
            for line in file:
                self.reactor_type.append(line.strip())

    def isValid(self, name):
        return name.lower() in self.reactor_type
