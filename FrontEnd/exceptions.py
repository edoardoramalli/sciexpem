class ExecutionColumnError(Exception):
    def __init__(self):
        super().__init__("ExecutionColumn does not exist.")
