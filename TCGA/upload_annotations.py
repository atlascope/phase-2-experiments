import girder_client

import json
import getpass

from datetime import datetime
from .constants import ANNOTATIONS_FOLDER, CONF, OVERWRITE


target_server = CONF.get('target_server', {})
api_root = target_server.get('api_root')
folder_id = target_server.get('folder_id')
username = input('Username: ')
password = getpass.getpass()

if not api_root or not folder_id:
    raise ValueError(
        "Configuration file must specify target_server.api_root and target_server.folder_id"
    )

print(f'Uploading annotations to {api_root}...')
start = datetime.now()
client = girder_client.GirderClient(apiUrl=api_root)
client.authenticate(username, password)

for case in ANNOTATIONS_FOLDER.glob('*.json'):
    case_name = case.name.split('.')[0]
    with open(case) as f:
        annotation_contents = json.load(f)
    for item in client.listItem(folder_id, case_name):
        print('\t', item.get('name'))
        if OVERWRITE:
            for old_annotation in client.get(
                'annotation',
                parameters=dict(itemId=item['_id']),
            ):
                old_id = old_annotation.get('_id')
                print(f'\t Deleting old annotation {old_id}.')
                client.delete(
                    f'annotation/{old_id}',
                )
        client.post(
            'annotation',
            parameters=dict(itemId=item['_id']),
            json=annotation_contents
        )

print(f'Completed upload in {datetime.now() - start} seconds.')
