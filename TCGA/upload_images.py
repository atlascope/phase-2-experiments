from datetime import datetime
import girder_client
import getpass
import requests

from .constants import DOWNLOADS_FOLDER, CONF


target_server = CONF.get('target_server', {})
atlascope_server = CONF.get('atlascope_server', {})
girder_api_root = target_server.get('api_root')
atlascope_api_root = atlascope_server.get('api_root')
username = input('Username: ')
password = getpass.getpass()

if not girder_api_root or not atlascope_api_root:
    raise ValueError(
        "Configuration file must specify target_server.api_root and atlascope_server.api_root"
    )

print(f'Uploading images to {girder_api_root}...')
start = datetime.now()
client = girder_client.GirderClient(apiUrl=girder_api_root)
client.authenticate(username, password)

collection = list(client.listCollection())
if len(collection) == 0:
    collection = client.createCollection('TCGA', public=True)
else:
    collection = collection[0]

folder = client.createFolder(
    collection.get('_id'),
    'TCGA',
    parentType='collection',
    public=True,
    reuseExisting=True,
)

for case in DOWNLOADS_FOLDER.glob('*'):
    for image in case.glob('*'):
        if image.is_file():
            print(image.name)
            with open(image) as f:
                item = client.createItem(
                    folder.get('_id'),
                    case.name,
                    reuseExisting=True,
                )
                item_id = item.get('_id')
                client.addMetadataToItem(item_id, {
                    'project': 'Atlascope'
                })
                client.uploadFileToItem(item_id, str(image))

                response = requests.post(f'{atlascope_api_root}images/', json=dict(
                    imageId=item_id,
                    imageName=case.name,
                    apiURL=girder_api_root,
                ))
                if response.status_code == 200:
                    print(f'Recorded ImageItem {case.name} in Atlascope.')

response = requests.get(f'{atlascope_api_root}images/')
print(response.json())

print(f'Completed upload in {datetime.now() - start} seconds.')
