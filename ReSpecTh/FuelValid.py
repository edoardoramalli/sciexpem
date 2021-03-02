from django.conf import settings
import os


class ValidFuel:

    def __init__(self, file=os.path.join(settings.BASE_DIR, "Files/fuels")):
        self.fuels = []  # fuels list in LOWERCASE only
        with open(file, "r") as file:
            for line in file:
                self.fuels.append(line.strip().lower())
        self.fuels = list(set(self.fuels))

    def isValid(self, name):
        return name.lower() in self.fuels
