import os
from django.conf import settings


class ExperimentClassifier:
    def __init__(self, name, model, experiment_type, reactor,ignition_definition, solver, output_file, mapping):
        # Input
        self.name = name
        self.model = model
        self.experiment_type = experiment_type
        self.reactor = reactor
        self.ignition_definition = ignition_definition
        self.inputs = list(mapping.keys())
        self.inputs_ignition = list(ignition_definition.values())

        # Output
        self.solver = solver
        self.output_file = output_file
        self.mapping = mapping

    def __eq__(self, other):
        if self.name == other.name:
            return True
        if self.experiment_type != other.experiment_type:
            return False
        if self.reactor != other.reactor:
            return False
        if self.ignition_definition != other.ignition_definition:
            return False
        if self.inputs != other.inputs:
            return False
        if self.inputs_ignition != other.inputs_ignition:
            return False
        return True

    @classmethod
    def create_exp(cls, name, model, experiment_type, reactor, ignition_definition, solver, output_file, mapping):
        ignition_definition = {item.strip().split("->")[0]: item.strip().split("->")[1] for item in
                               ignition_definition.strip().split(",") if ignition_definition}
        mapping = {item.strip().split("->")[0]: item.strip().split("->")[1] for item in mapping.strip().split(",")}
        return ExperimentClassifier(name=name,
                                    model=model,
                                    experiment_type=experiment_type,
                                    reactor=reactor,
                                    ignition_definition=ignition_definition,
                                    solver=solver,
                                    output_file=output_file,
                                    mapping=mapping)

    def __repr__(self):
        return "< Exp %s : %s - %s - %s - %s >" % (
        self.name, self.model, self.experiment_type, self.reactor, self.inputs)


class Classifier:

    def __init__(self, file=os.path.join(settings.BASE_DIR, "Files/experiment_classifier")):
        self.experiments = []
        with open(file, "r") as file:
            for line in file:
                if line.startswith("#"):
                    continue
                split = line.split("|")
                name = split[0].strip()
                experiment_type = split[1].strip()
                reactor = split[2].strip()
                ignition_definition = split[3].strip()
                model = split[4].strip()
                solver = split[5].strip()
                output_file = split[6].strip()
                mapping = split[7].strip()

                exp = ExperimentClassifier.create_exp(name=name,
                                                      model=model,
                                                      experiment_type=experiment_type,
                                                      reactor=reactor,
                                                      ignition_definition=ignition_definition,
                                                      solver=solver,
                                                      output_file=output_file,
                                                      mapping=mapping)

                self.append_unique(exp)
        file.close()

    def append_unique(self, new_experiment):
        if new_experiment not in self.experiments:
            self.experiments.append(new_experiment)

    def get_ExperimentClassifier(self, experiment_type, reactor, par_input_list, ignition_type=None):
        for e in self.experiments:
            if e.experiment_type == experiment_type and e.reactor == reactor and set(e.inputs) == set(par_input_list):
                if ignition_type is not None and e.inputs_ignition is not None:
                    if set(e.inputs_ignition) == set(ignition_type):
                        return e
                elif ignition_type is None and e.inputs_ignition is None:
                    return e
                else:
                    return None
        return None



