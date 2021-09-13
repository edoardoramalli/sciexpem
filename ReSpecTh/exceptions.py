class ZenodoError(Exception):
    def __init__(self, message):
        super().__init__("Zenodo Error. " + message)