from django.conf import settings
import os


class GetReactor:

    def __init__(self, file=os.path.join(settings.BASE_DIR, "Files/getReactor")):
        self.mapping = {}
        with open(file, "r") as file:
            for line in file:
                split_line = line.strip().split('=')
                exp_type = split_line[0].strip().lower()
                reactors = split_line[1].strip().split(',')
                self.mapping[exp_type] = reactors

    def getMapping(self, name):
        return self.mapping.get(name)