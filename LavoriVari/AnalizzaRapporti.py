import json
import statistics

with open('POLIMI_1212_C1C3_exp.json', 'r') as file:
    POLIMI_1212_C1C3_exp = json.load(file)


with open('POLIMI_1212_C1C3_sim.json', 'r') as file:
    POLIMI_1212_C1C3_sim = json.load(file)


with open('CRECK_2003_C1C3_DME_LTHT_exp.json', 'r') as file:
    CRECK_2003_C1C3_DME_LTHT_exp = json.load(file)


with open('CRECK_2003_C1C3_DME_LTHT_sim.json', 'r') as file:
    CRECK_2003_C1C3_DME_LTHT_sim = json.load(file)


with open('POLIMI_1212_C1C3_tot.json', 'r') as file:
    POLIMI_1212_C1C3_tot = json.load(file)


with open('CRECK_2003_C1C3_DME_LTHT_tot.json', 'r') as file:
    CRECK_2003_C1C3_DME_LTHT_tot = json.load(file)


for couple in CRECK_2003_C1C3_DME_LTHT_tot:
    print(f'{couple} -> Mean {statistics.mean(CRECK_2003_C1C3_DME_LTHT_tot[couple]):.2f}, Stdev {statistics.stdev(CRECK_2003_C1C3_DME_LTHT_tot[couple])}')

