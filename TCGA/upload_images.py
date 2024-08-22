import girder_client
import json
import getpass

from datetime import datetime
from pathlib import Path


DOWNLOADS_FOLDER = Path(__file__).parent / 'downloads'


with open('conf.json') as f:
    conf = json.load(f)

target_server = conf.get('target_server', {})
api_root = target_server.get('api_root')
folder_id = target_server.get('folder_id')
username = input('Username: ')
password = getpass.getpass()

if not api_root or not folder_id:
    raise ValueError(
        "Configuration file must specify target_server.api_root and target_server.folder_id"
    )

print(f'Uploading images to {api_root}...')
start = datetime.now()
client = girder_client.GirderClient(apiUrl=api_root)
client.authenticate(username, password)

for case in DOWNLOADS_FOLDER.glob('*'):
    for image in case.glob('*'):
        if image.is_file():
            print('\t', image.name)
            with open(image) as f:
                item = client.createItem(folder_id, case.name, 'TCGA Example Data')
                client.addMetadataToItem(item['_id'], {
                    'project': 'Atlascope'
                })
                client.uploadFileToItem(item['_id'], str(image))


print(f'Completed upload in {datetime.now() - start} seconds.')
