import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import girder_client
import requests

from .constants import CONF, DOWNLOADS_FOLDER
from .read_vectors import get_case_vector
from .client import get_client, get_case_folder_item, sync_file


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

    for case_folder_item in client.listFolder(folder_id):
        case_name = case_folder_item.get('name')
        if (cases is None and 'test' not in case_name) or (cases is not None and case_name in cases):
            print(f'Downloading {case_name}.')
            client.downloadFolderRecursive(case_folder_item.get('_id'), DOWNLOADS_FOLDER / case_name)

    print(f'Completed download in {datetime.now() - start} seconds.')


def upload_examples(cases, username=None, password=None):
    print(f'Uploading examples...')
    start = datetime.now()
    client = get_client(username, password)

    for case_folder in DOWNLOADS_FOLDER.glob('*'):
        case_name = case_folder.name
        if (cases is None and 'test' not in case_name) or (cases is not None and case_name in cases):
            case_folder_item = get_case_folder_item(client, case_name)
            image_path = case_folder / (f'{case_name}.svs' if case_name != 'test' else 'tcgaextract_rgb.tiff')
            if image_path.exists():
                parquet_path = case_folder / f'{case_name}.parquet'
                if not parquet_path.exists():
                    print('Generating parquet file of vector data...')
                    vector = get_case_vector(case_name=case_name)
                    vector.to_parquet(parquet_path)
                print(f'Uploading image and parquet file for {case_name}.')
                sync_file(client, case_folder_item, image_path)
                sync_file(client, case_folder_item, parquet_path)
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
        upload_examples(cases, username=username, password=password)
    elif command == 'download':
        download_examples(cases)


if __name__ == '__main__':
    main()
