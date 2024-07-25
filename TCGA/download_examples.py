import girder_client
import json

from datetime import datetime
from pathlib import Path


DOWNLOADS_FOLDER = Path(__file__).parent / 'downloads'


with open('conf.json') as f:
    conf = json.load(f)

sample_data_server = conf.get('sample_data_server', {})
api_root = sample_data_server.get('api_root')
folder_id = sample_data_server.get('folder_id')

if not api_root or not folder_id:
    raise ValueError(
        "Configuration file must specify sample_data_server.api_root and sample_data_server.folder_id"
    )

print(f'Downloading example data from {api_root}...')
start = datetime.now()
client = girder_client.GirderClient(apiUrl=api_root)
client.downloadFolderRecursive(folder_id, DOWNLOADS_FOLDER)

print(f'Completed download in {datetime.now() - start} seconds.')
