class MissingOpenSmokeOutputFile(Exception):
    def __init__(self):
        super().__init__("The OpenSMOKE output file is missing.")


class OpenSmokeWrongInputFile(Exception):
    def __init__(self):
        super().__init__("The OpenSMOKE input file is not valid.")

