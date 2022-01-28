class ExecutionColumnError(Exception):
    def __init__(self, message):
        super().__init__("ExecutionColumn does not exist. {}".format(message))


class PlotError(Exception):
    def __init__(self, message):
        super().__init__("PlotError. " + message)