import os
import argparse
import numpy
import pandas
import girder_client
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, select
from .models import ImageItem, FeatureVector
from .services import create_db_and_tables, engine


def populate(cases, username, password):
    if username is None:
        username = input('Girder Username: ')
    if password is None:
        password = getpass.getpass('Girder Password: ')

    girder_server = os.environ.get('GIRDER_SERVER')
    example_server = os.environ.get('EXAMPLE_SERVER')
    example_folder_id = os.environ.get('EXAMPLE_FOLDER_ID')
    example_path = os.environ.get('EXAMPLE_PATH')

    # Download examples
    start = datetime.now()
    client = girder_client.GirderClient(apiUrl=example_server)
    for case_folder in client.listFolder(example_folder_id):
        case_name = case_folder.get('name')
        case_path = Path(example_path, case_name)
        if not case_path.exists():
            if (cases is None and 'test' not in case_name) or (cases is not None and case_name in cases):
                print(f'Downloading {case_name}.')
                client.downloadFolderRecursive(case_folder.get('_id'), case_path)
        else:
            print(f'{case_path} already exists. Skipping download.')
    print(f'Completed example downloads in {(datetime.now() - start).total_seconds()} seconds.')

    # Prepare local Girder
    start = datetime.now()
    client = girder_client.GirderClient(apiUrl=girder_server)
    client.authenticate(username, password)
    collection = list(client.listCollection())
    if len(collection) == 0:
        collection = client.createCollection('TCGA', public=True)
    else:
        collection = collection[0]
    target_folder = client.createFolder(
        collection.get('_id'),
        'Examples',
        parentType='collection',
        public=True,
        reuseExisting=True,
    )
    target_folder_id = target_folder.get('_id')

    # Upload examples to local Girder
    for case_folder in Path(example_path).glob('*'):
        case_name = case_folder.name.split('.')[0]
        if (cases is None and 'test' not in case_name) or (cases is not None and case_name in cases):
            for child in case_folder.glob('*'):
                if child.is_file():
                    print(f'Uploading image {child.name}.')
                    with open(child) as f:
                        item = client.createItem(
                            target_folder_id,
                            case_name,
                            reuseExisting=True,
                        )
                        item_id = item.get('_id')
                        client.addMetadataToItem(item_id, {
                            'project': 'Atlascope'
                        })
                        file_id, current = client.isFileCurrent(item_id, child.name, str(child))
                        if not current:
                            file_obj = client.uploadFileToItem(item_id, str(child))

    # create large images for all items in folder
    client.put(f'/large_image/folder/{target_folder_id}/tiles?recurse=true')
    print(f'Completed image uploads in {(datetime.now() - start).total_seconds()} seconds.')

    # Record ImageItems and FeatureVectors in Atlascope
    start = datetime.now()
    create_db_and_tables()
    with Session(engine) as session:
        existing_image_items = select(ImageItem).where(ImageItem.apiURL == girder_server)
        for case_folder in Path(example_path).glob('*'):
            case_name = case_folder.name.split('.')[0]
            if (cases is None and 'test' not in case_name) or (cases is not None and case_name in cases):
                matches = client.listItem(target_folder_id, name=case_name)
                for match in matches:
                    image_item = session.exec(existing_image_items.where(ImageItem.girderId == match.get('_id'))).first()
                    if not image_item:
                        image_item = ImageItem(name=case_name, apiURL=girder_server, girderId=match.get('_id'))
                        session.add(image_item)
                        session.commit()
                        session.refresh(image_item)
                        print(f'Created ImageItem {image_item.id}.')
                    else:
                        print(f'ImageItem {image_item.id} already exists. Skipping.')

                print('Reading feature vectors...')
                existing_vectors = select(FeatureVector).where(FeatureVector.imageItemId == image_item.id)
                meta_vectors = case_folder / 'nucleiMeta'
                prop_vectors = case_folder / 'nucleiProps'
                meta_vector_files = list(meta_vectors.glob('*.csv'))
                prop_vector_files = list(prop_vectors.glob('*.csv'))
                for meta_vector_file in meta_vector_files:
                    roiname = meta_vector_file.name.replace('.csv', '')
                    prop_vector_file = next((
                        f for f in prop_vector_files
                        if f.name == meta_vector_file.name
                    ), None)
                    if prop_vector_file:
                        meta = pandas.read_csv(
                            str(meta_vector_file),
                            usecols=lambda x: 'Unnamed' not in x
                        ).reset_index(drop=True)
                        props = pandas.read_csv(
                            str(prop_vector_file),
                            usecols=lambda x: 'Unnamed' not in x
                        ).reset_index(drop=True)
                        intersection_cols = list(meta.columns.intersection(props.columns))
                        props = props.drop(intersection_cols, axis=1)
                        data = pandas.concat([meta, props], axis=1).fillna(-1)

                        # Vector Implementation
                        # data = data.select_dtypes(include='number')
                        # for index, row in data.iterrows():
                        #     vector = session.exec(
                        #         existing_vectors.where(FeatureVector.roiname == roiname).where(FeatureVector.index == index)
                        #     ).first()
                        #     if not vector:
                        #         vector = FeatureVector(
                        #             index=index,
                        #             imageItemId=image_item.id,
                        #             roiname=roiname,
                        #             labels=list(data.columns),
                        #             features=row.to_numpy().tolist(),
                        #         )
                        #         session.add(vector)
                        #         session.commit()

                        # JSON implementation
                        vector = session.exec(
                            existing_vectors.where(FeatureVector.roiname == roiname)
                        ).first()
                        if not vector:
                            vector = FeatureVector(
                                imageItemId=image_item.id,
                                roiname=roiname,
                                labels=list(data.columns),
                                features=data.to_numpy().tolist(),
                            )
                            session.add(vector)
                            session.commit()

                existing_vectors = session.exec(existing_vectors).all()
                print(f'{len(existing_vectors)} FeatureVectors recorded for {case_name}.')

    print(f'Completed Atlascope records in {(datetime.now() - start).total_seconds()} seconds.')


def main(raw_args=None):
    parser = argparse.ArgumentParser(
        prog="Populate",
        description="Transfer data from example server to target server.",
    )
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

    populate(cases, username, password)


if __name__ == '__main__':
    main()
