class ExecutionColumnError(Exception):
    def __init__(self):
        super().__init__("ExecutionColumn does not exist.")


class PlotError(Exception):
    def __init__(self, message):
        super().__init__("PlotError. " + message)