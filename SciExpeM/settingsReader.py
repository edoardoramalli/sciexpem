class SettingsReader:
    def __init__(self, path='./settingsFile'):
        self.settings = {}
        with open(path, 'r') as file:
            for line in file:
                line_split = line.strip().split("=")
                key, value = line_split[0], line_split[1]
                self.settings[key] = value