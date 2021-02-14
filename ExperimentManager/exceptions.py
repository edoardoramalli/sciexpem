class DuplicateExperimentError(Exception):
    def __init__(self):
        super().__init__("Duplicate Experiment")


class MandatoryFieldExperimentError(Exception):
    def __init__(self, message):
        super().__init__("Mandatory Field Experiment Error. Missing '{}'".format(message))


class ConstraintFieldExperimentError(Exception):
    def __init__(self, message):
        super().__init__("Constraint Model Field Error. " + message)


class MissingRequirementsVerificationExperimentError(Exception):
    def __init__(self, message):
        super().__init__("Missing Requirements for Experiment Verification. " + message)


class OptimaPPError(Exception):
    def __init__(self, message):
        super().__init__("OptimaPP Error. " + message)
