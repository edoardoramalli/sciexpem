import os
import django
import requests, json
from dateutil.parser import parse
from django.db.models import Q

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()




from ExperimentManager.Models import *

species = Species.objects.all()

import xml.etree.cElementTree as ET

root = ET.Element("database")

# SPECIE
for specie in species:
    doc = ET.SubElement(root, "species", preferredKey=specie.preferredKey)
    if specie.CAS:
        ET.SubElement(doc, "CAS").text = specie.CAS
    if specie.SMILES:
        ET.SubElement(doc, "SMILES").text = specie.SMILES
    if specie.chemName:
        ET.SubElement(doc, "chemName").text = specie.chemName
    if specie.InChI:
        ET.SubElement(doc, "InChI").text = specie.InChI


tree = ET.ElementTree(root)


from xml.dom import minidom

xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")
with open("New_Database.xml", "w") as f:
    f.write(xmlstr)




# CAS = specie.createElement('CAS')
# CAS.text = 'edo'
# chemName = specie.createElement('chemName')
# chemName.text = 'ciao'
# InChI = specie.createElement('InChI')
# InChI = 'ele'
# SMILES = specie.createElement('SMILES')
# SMILES.text = 'smile'

#
# xml.appendChild(specie)
#
# xml_str = root.toprettyxml(indent="\t")
#
# save_path_file = "gfg.xml"
#
# with open(save_path_file, "w") as f:
#     f.write(xml_str)