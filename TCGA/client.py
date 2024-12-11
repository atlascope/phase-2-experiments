import girder_client
import getpass
from .constants import CONF


def get_client(username, password):
    target_server = CONF.get('target_server', {})
    girder_api_root = target_server.get('api_root')
    if not girder_api_root:
        raise ValueError(
            "Configuration file must specify target_server.api_root"
        )
    if username is None:
        username = input('Girder Username: ')
    if password is None:
        password = getpass.getpass('Girder Password: ')
    client = girder_client.GirderClient(apiUrl=girder_api_root)
    client.authenticate(username, password)
    return client


def get_case_folder_item(client, case_name):
    collection = list(client.listCollection())
    if len(collection) == 0:
        collection = client.createCollection('TCGA', public=True)
    else:
        collection = collection[0]

    examples_folder = client.createFolder(
        collection.get('_id'),
        'Examples',
        parentType='collection',
        public=True,
        reuseExisting=True,
    )
    case_folder_item = client.createFolder(
        examples_folder.get('_id'),
        case_name,
        public=True,
        reuseExisting=True
    )
    return case_folder_item

def sync_file(client, folder_item, filepath, **metadata):
    with open(filepath) as f:
        item = client.createItem(
            folder_item.get('_id'),
            filepath.name,
            reuseExisting=True,
        )
        item_id = item.get('_id')
        metadata.update({
            'project': 'Atlascope'
        })
        client.addMetadataToItem(item_id, metadata)
        file_id, current = client.isFileCurrent(item_id, filepath.name, str(filepath))
        if not current:
            file_obj = client.uploadFileToItem(item_id, str(filepath))
