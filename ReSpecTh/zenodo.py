import requests
import json
from io import BytesIO
from django.conf import settings

from ReSpecTh.exceptions import ZenodoError

params = {'access_token': settings.ZENODO_ACCESS_TOKEN}
headers = {"Content-Type": "application/json"}


def reserved_doi():
    try:
        r = requests.post('https://zenodo.org/api/deposit/depositions',
                          params=params,
                          json={},
                          headers=headers)
        response = r.json()
        bucket = response["links"]["bucket"]
        edit = response["links"]["edit"]
        discard = response["links"]["discard"]
        publish = response["links"]["publish"]
        prereserve_doi = response["metadata"]["prereserve_doi"]["doi"]
        deposition_id = response['id']
    except Exception:
        raise ZenodoError('Error reserving.')

    return bucket, publish, prereserve_doi, deposition_id

def upload_respecth(file_string, doi, bucket_url):
    try:
        filename = doi + '.xml'
        file_like = BytesIO(bytes(file_string.encode()))
        r = requests.put("%s/%s" % (bucket_url, filename), data=file_like, params=params, )
    except Exception:
        raise ZenodoError('Error uplaoding file.')

def update_description(title, description, deposition_id):
    try:
        data = {
            'metadata': {
                'prereserve_doi': 'true',
                'title': 'SciExpeM - %s' % title,
                'access_right': 'open',
                'license': 'CC-BY-4.0',
                'upload_type': 'dataset',
                'description': description,
                'creators': [{'name': 'SciExpeM', 'affiliation': 'Politecnico di Milano '}]}}
        r = requests.put('https://zenodo.org/api/deposit/depositions/%s' % deposition_id,
                         params=params, data=json.dumps(data), headers=headers)
    except Exception:
        raise ZenodoError('Error updating description.')

def publish_doi(url):
    try:
        r = requests.post(url, params=params, headers=headers)
    except Exception:
        raise ZenodoError('Error publishing.')

def delete_doi(deposition_id):
    try:
        r = requests.delete('https://zenodo.org/api/deposit/depositions/%s' % deposition_id, params=params, headers=headers)
    except Exception:
        raise ZenodoError('Error deleting.')

