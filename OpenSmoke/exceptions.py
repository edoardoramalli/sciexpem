class MissingOpenSmokeOutputFile(Exception):
    def __init__(self, msg=''):
        super().__init__("The OpenSMOKE output file is missing. {}.".format(msg))


class OpenSmokeWrongInputFile(Exception):
    def __init__(self, msg):
        super().__init__("The OpenSMOKE input file is not valid." + msg)


class MissingColumnExecution(Exception):
    def __init__(self, msg):
        super().__init__("In the file are missing some values: " + msg)

