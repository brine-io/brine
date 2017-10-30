import requests

from brine.env import Env
from brine.exceptions import BrineError


def get_dataset_for_info(dataset_name):
    query = '''
    query ($datasetName: String!) {
        dataset(name: $datasetName) {
            name
            description
            versions(first: 100) {
                edges {
                    node {
                        number
                    }
                }
            }
        }
    }
    '''
    variables = {'datasetName': dataset_name}
    data = _graphql(query, variables)
    try:
        return {
            'name': data['dataset']['name'],
            'description': data['dataset']['description'],
            'versions': list(map(lambda x: x['node']['number'], data['dataset']['versions']['edges'])),
        }
    except KeyError:
        raise ApiError('Invalid server response.')
    except TypeError:
        raise ApiError('Dataset %s does not exist.' % dataset_name)


def get_version_for_install(dataset_name):
    query = '''
    query ($datasetName: String!) {
        dataset(name: $datasetName) {
            latestVersion {
                number
                signedUrl
            }
        }
    }
    '''
    variables = {'datasetName': dataset_name}
    data = _graphql(query, variables)
    try:
        return {
            'version_number': data['dataset']['latestVersion']['number'],
            'signed_url': data['dataset']['latestVersion']['signedUrl'],
        }
    except KeyError:
        raise ApiError('Invalid server response.')
    except TypeError:
        raise ApiError('Dataset %s does not exist.' % dataset_name)


def create_upload_session(dataset_name):
    query = '''
    mutation ($datasetName: String!) {
        createUploadSession(input: {datasetName: $datasetName, clientMutationId: "1"}) {
            uploadSession {
                id
            }
        }
    }'''
    variables = {'datasetName': dataset_name}
    data = _graphql(query, variables)
    try:
        return {
            'upload_session_id': data['createUploadSession']['uploadSession']['id']
        }
    except KeyError:
        raise ApiError('Invalid server response.')


def get_upload_session_signed_url(upload_session_id, filename):
    query = '''
    query ($id: ID!, $filename: String!) {
        uploadSession(id: $id) {
            signedUrl(filename: $filename)
        }
    }'''
    variables = {'id': upload_session_id, 'filename': filename}
    data = _graphql(query, variables)
    try:
        return {
            'signed_url': data['uploadSession']['signedUrl']
        }
    except KeyError:
        raise ApiError('Invalid server response.')


def complete_upload_session(upload_session_id):
    query = '''
    mutation ($id: ID!) {
        completeUploadSession(input: {id: $id, clientMutationId: "1"}) {
            version {
                id
                number
            }
        }
    }'''
    variables = {'id': upload_session_id}
    data = _graphql(query, variables)
    try:
        return {
            'version_id': data['completeUploadSession']['version']['id'],
            'version_number': data['completeUploadSession']['version']['number'],
        }
    except KeyError:
        raise ApiError('Invalid server response.')


def _graphql(query, variables):
    payload = {'query': query, 'variables': variables}
    headers = {'Content-Type': 'application/json',
               'Accept': 'application/json'}
    try:
        r = requests.post(Env.ENDPOINT, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()['data']
    except requests.exceptions.RequestException as ex:
        raise ApiError('Unable to reach server.')
    except KeyError:
        raise ApiError('Invalid server response.')


class ApiError(BrineError):
    pass
