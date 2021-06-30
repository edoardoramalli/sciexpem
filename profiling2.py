import requests, json
import multiprocessing
from tqdm import tqdm

def test_link(doi):
    r = requests.get('https://www.doi.org/{doi}'.format(doi=doi), allow_redirects=True)
    if r.status_code == 200:
        return True, None
    else:
        return False, r.status_code


# if __name__ == '__main__':
#     dois = None
#     with open('dois.out', 'r') as file:
#         dois = json.load(file)
#
#     for doi in tqdm(dois):
#         try:
#             test, info = test_link(doi)
#             if not test:
#                 print(doi, info)
#         except Exception:
#             print(doi)
#             pass
#



dois = None
with open('date_reference_doi.out', 'r') as file:
    dois = json.load(file)

for doi in dois:
    if not dois[doi]:
        print(doi)
