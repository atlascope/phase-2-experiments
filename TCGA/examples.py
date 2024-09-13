import argparse
import getpass
import json
import sys
from datetime import datetime
from pathlib import Path

import girder_client
import requests

from .constants import CONF, DOWNLOADS_FOLDER
from .read_vectors import get_case_vector


FEATURE_BATCH_SIZE = 10000


def download_examples(cases):
    sample_data_server = CONF.get('sample_data_server', {})
    api_root = sample_data_server.get('api_root')
    folder_id = sample_data_server.get('folder_id')

    if not api_root or not folder_id:
        raise ValueError(
            "Configuration file must specify sample_data_server.api_root and sample_data_server.folder_id"
        )

    print(f'Downloading example data from {api_root}...')
    start = datetime.now()
    client = girder_client.GirderClient(apiUrl=api_root)

    for case_folder in client.listFolder(folder_id):
        case_name = case_folder.get('name')
        if (cases is None and 'test' not in case_name) or (cases is not None and case_name in cases):
            print(f'Downloading {case_name}.')
            client.downloadFolderRecursive(case_folder.get('_id'), DOWNLOADS_FOLDER / case_name)

    print(f'Completed download in {datetime.now() - start} seconds.')


def upload_images(cases, username=None, password=None):
    target_server = CONF.get('target_server', {})
    atlascope_server = CONF.get('atlascope_server', {})
    girder_api_root = target_server.get('api_root')
    atlascope_api_root = atlascope_server.get('api_root')

    if username is None:
        username = input('Girder Username: ')
    if password is None:
        password = getpass.getpass('Girder Password: ')

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
        'Examples',
        parentType='collection',
        public=True,
        reuseExisting=True,
    )

    for case in DOWNLOADS_FOLDER.glob('*'):
        case_name = case.name.split('.')[0]
        if (cases is None and 'test' not in case_name) or (cases is not None and case_name in cases):
            for image in case.glob('*'):
                if image.is_file():
                    print(f'Uploading image for {case_name}.')
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
                        file_id, current = client.isFileCurrent(item_id, image.name, str(image))
                        if not current:
                            file_obj = client.uploadFileToItem(item_id, str(image))

                        # create large images for all items in folder
                        client.put(f'/large_image/folder/{folder.get("_id")}/tiles?recurse=true')

                        # create ImageItem & Feature records in Atlascope
                        response = requests.post(f'{atlascope_api_root}images/', json=dict(
                            girderId=item_id,
                            name=case.name,
                            apiURL=girder_api_root,
                        ))
                        image_item = response.json()
                        image_item_id = image_item.get('id')
                        if response.status_code == 200:
                            print(f'Recorded ImageItem {case.name} in Atlascope.')
                        else:
                            print(response)

    # fetch list of Atlascope image records
    atl_images = requests.get(f'{atlascope_api_root}images/').json()
    print(f'Atlascope server has {len(atl_images)} images.')

    print(f'Completed upload in {datetime.now() - start} seconds.')


def main(raw_args=None):
    parser = argparse.ArgumentParser(
        prog="ExampleDataLoader",
        description="Transfer data from example server to target server.",
    )
    parser.add_argument('command', choices=['upload', 'download'], help='Action to perform.')
    parser.add_argument(
        '--cases', nargs='*',
        help='List of case names to process. If not specified, process all non-test cases.'
    )
    parser.add_argument(
        '--username', type=str, help='Girder username for upload'
    )
    parser.add_argument(
        '--password', type=str, help='Girder password for upload'
    )
    args = vars(parser.parse_args(raw_args))
    command, cases, username, password = (
        args.get('command'),
        args.get('cases'),
        args.get('username'),
        args.get('password'),
    )

    if command == 'upload':
        upload_images(cases, username=username, password=password)
    elif command == 'download':
        download_examples(cases)


if __name__ == '__main__':
    main()
