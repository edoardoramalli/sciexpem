class IOReSpecThOS:

    @staticmethod
    def load_entries(path="./Input_Output_ReSpecTh_OS.csv"):
        entries = []

        with open(path, "r") as file:
            header_split = file.readline().strip().split(";")
            for line in file:
                line_split = line.strip().split(";")
                experiment_type = line_split[0]
                reactor = line_split[1]
                data_group_par = line_split[2].split(",")
                add_info = line_split[3]
                os_file = line_split[4]
                os_par = line_split[5].split(",")
                if 0 in (experiment_type, reactor, os_file) or ["0"] in (data_group_par, os_par):
                    continue
                else:
                    entries.append(Entry(experiment_type, reactor, data_group_par, add_info, os_file, os_par))

        return entries

    @staticmethod
    def query(experiment_type, reactor, data_group_fields, additional_info=0):
        entries = IOReSpecThOS.load_entries()
        result = None
        for entry in entries:
            if entry == Entry(experiment_type=experiment_type,
                              reactor=reactor,
                              data_group_fields=data_group_fields,
                              additional_info=additional_info):
                result = entry
                break
        if result:
            return (result.output_file, result.output_fields)
        else:
            return None


class Entry:

    def __init__(self, experiment_type, reactor, data_group_fields,
                 additional_info=None, output_file=None, output_fields=None):
        self.experiment_type = experiment_type
        self.reactor = reactor
        self.data_group_fields = data_group_fields
        self.additional_info = additional_info
        self.output_file = output_file
        self.output_fields = output_fields

    def __eq__(self, other):
        if self.experiment_type == other.experiment_type and \
            self.reactor == other.reactor and \
                set(self.data_group_fields) == set(other.data_group_fields):
            return True
        else:
            return False
