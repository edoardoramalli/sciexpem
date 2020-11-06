import xml.etree.ElementTree as ET
import pandas as pd
import xmltodict


class ReSpecTh():
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

    def get_ignition_type(self):
        return self.root.find("./ignitionType")

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

    # DEPRECATED
    def extract_initial_composition(self):
        initial_composition = dict()
        for component in self.get_common_property("initial composition"):
            initial_composition[component.find('speciesLink').attrib['preferredKey']] = component.find('amount').text
        return initial_composition

    def initial_composition(self):
        initial_composition = self.get_common_property("initial composition")
        if not initial_composition:
            return []

        initial_species = []
        for component in initial_composition:
            name = component.find('speciesLink').attrib.get('preferredKey')
            amount = component.find('amount').text
            cas = component.find('speciesLink').attrib.get('CAS')
            units = component.find('amount').attrib.get("units")
            initial_specie = {"name": name, "amount": amount, "cas": cas, "units": units}
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
            sourcetype = prop.attrib.get("sourcetype")
            props.append({"name": name, "units": units, "value": value, "sourcetype": sourcetype})
        return props

    # deprecated
    def extract_columns(self):
        columns = []
        dataGroup = self.root.find("dataGroup")
        for prop in dataGroup.findall("property"):
            name = prop.attrib.get('name')
            units = prop.attrib.get('units')
            label = prop.attrib.get('label')

            species = None
            xml_species = prop.findall('speciesLink')
            if xml_species:
                species = [specie.attrib['preferredKey'] for specie in xml_species]

            data = [float(dp.find(prop.attrib['id']).text) for dp in dataGroup.findall('dataPoint')]
            columns.append({'name': name, "units": units, "label": label, "species": species, "data": data})

        return columns

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

                species = None
                xml_species = prop.findall('speciesLink')
                if xml_species:
                    species = [specie.attrib['preferredKey'] for specie in xml_species]

                data = [float(dp.find(prop.attrib['id']).text) for dp in dataGroup.findall('dataPoint')]
                dg_columns.append(
                    {'name': name, "units": units, "label": label, "species": species, "data": data, "dg_id": dg_id})

                # extract dataPoint attributes
            dataPoints = dataGroup.findall('dataPoint')
            dp_attributes = dataPoints[0].attrib
            for k in dp_attributes.keys():
                data = [float(dp.attrib[k]) for dp in dataPoints]
                dg_columns.append(
                    {'name': k, "units": "unitless", "label": k, "species": None, "data": data, "dg_id": dg_id})

            result.append(dg_columns)
        return result

    def extract_uncertainties(self):
        columns = []
        dataGroup = r.root.find("dataGroup")
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

    # DEPRECATED
    def extract_data_groups(self):
        return [xmltodict.parse(ET.tostring(dg), attr_prefix="") for dg in self.root.findall("./dataGroup")]

    @classmethod
    def from_file(cls, path):
        tree = ET.parse(path)
        return cls(tree)