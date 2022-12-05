from django.db import models
from django.contrib.postgres.fields import ArrayField
from ExperimentManager.exceptions import *
import re


def check(test_str, pattern):
    if re.search(pattern, test_str):
        return False
    else:
        return True


def checkInChI(test_str):
    if not test_str.startswith("1S"):
        raise SpecieConsistencyError("InChI not valid. InChI has to start with '1S'.")

    slash_number = test_str.count('/')

    if not 1 <= slash_number <= 8:
        raise SpecieConsistencyError("InChI not valid. Number of slash should be in [1, 8].")

    if not check(test_str, pattern=r'[^a-zA-Z0-9\-\(\)\,\+]\/'):
        raise SpecieConsistencyError("InChI not valid. In the third layer only a-z A-z 0-9 + - , ( ) /")

    # split_test_str = test_str.split('/')
    #
    # if len(split_test_str) >= 3:
    #     if not check(split_test_str[2], pattern=r'[^a-z\-\(\)]'):
    #         raise SpecieConsistencyError("InChI not valid. In the third layer only a-z - ( )")
    #
    # if len(split_test_str) >= 4:
    #     if not split_test_str[3].startswith('h'):
    #         raise SpecieConsistencyError("InChI not valid. The fourth has to start with h.")
    #
    #     if not check(split_test_str[3], pattern=r'[^0-9H\-\(\)\,]'):
    #         raise SpecieConsistencyError("InChI not valid. In the fourth layer only 0-9 H - ( ) ,")
    #
    # if len(split_test_str) >= 5:
    #     for i in range(5, len(split_test_str)):
    #         if not check(split_test_str[3], pattern=r'[^a-z0-9\+\-]'):
    #             raise SpecieConsistencyError("InChI not valid. In the 5° to 8° layer only 0-9 a-z + -")


class Specie(models.Model):
    InChI = models.CharField(max_length=150, unique=True)
    preferredKey = models.CharField(max_length=150)
    formula = models.CharField(max_length=150)

    names = ArrayField(models.CharField(max_length=150), blank=True, null=True)
    CAS = models.CharField(max_length=10, blank=True, null=True)
    SMILES = models.CharField(max_length=150, blank=True, null=True)
    chemName = models.CharField(max_length=150, blank=True, null=True)

    # fuel = models.BooleanField(default=False)

    # TODO caratteri consentiti, tutto in uppercase? cosa deve essere unique?

    @staticmethod
    def createSpecie(text_dict):
        # Mandatory
        try:
            InChI = text_dict['InChI']
            preferredKey = text_dict['preferredKey']
            formula = text_dict['formula']

        except KeyError as error:
            raise MandatoryFieldError(error)

        CAS = text_dict.get('CAS')
        SMILES = text_dict.get('SMILES')
        chemName = text_dict.get('chemName')
        if text_dict.get('names', []):
            names = [e.strip() for e in text_dict.get('names', [])]
        else:
            names = None

        specie = Specie(InChI=InChI, preferredKey=preferredKey, names=names,
                        CAS=CAS, SMILES=SMILES, chemName=chemName, formula=formula)
        return [specie]

    def check_fields(self):
        preferredKey = self.preferredKey
        names = list(self.names) if self.names is not None or [] else []

        InChI = self.InChI
        formula = self.formula if self.formula is not None else None
        CAS = self.CAS if self.CAS is not None else None
        SMILES = self.SMILES if self.SMILES is not None else None
        chemName = self.chemName if self.chemName is not None else None

        if InChI:
            self.InChI = InChI.strip()
            checkInChI(self.InChI)

        if formula:
            self.formula = formula.strip().upper()

        if CAS:
            self.CAS = CAS.strip()
            if self.CAS.count('-') != 2:
                raise SpecieConsistencyError('CAS Missing correct number of "-".')
            if not self.CAS.replace('-', '').isdecimal():
                raise SpecieConsistencyError('CAS can contains only numbers.')

        if SMILES:
            self.SMILES = SMILES.strip()
            if not check(self.SMILES, pattern=r'[^a-zA-Z0-9\(\)\[\]\=\@\+\-\/\\\#]'):
                raise SpecieConsistencyError('SMILES can contains only numbers, letters and ( ) [ ] = @ + - / \ #')

        if chemName:
            self.chemName = chemName.strip().lower()

        if names:
            names = [e.strip() for e in names]

        if preferredKey:
            self.preferredKey = preferredKey.upper().strip()

        # Add the preferredKey in the alternative names, remove duplicates
        self.names = list(set([preferredKey] + names))

    def save(self, *args, **kwargs):
        self.check_fields()
        super().save(*args, **kwargs)
