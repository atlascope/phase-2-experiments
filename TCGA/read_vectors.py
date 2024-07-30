import girder_client
import json
import math
import pandas
from pathlib import Path
from datetime import datetime


DOWNLOADS_FOLDER = Path(__file__).parent / 'downloads'


def get_case_vector(case_name):
    results = None
    case_folder = next(DOWNLOADS_FOLDER.glob(case_name))
    meta_vectors = case_folder / 'nucleiMeta'
    prop_vectors = case_folder / 'nucleiProps'
    meta_vector_files = list(meta_vectors.glob('*.csv'))
    prop_vector_files = list(prop_vectors.glob('*.csv'))
    print(f'\tReading features in {len(meta_vector_files)} regions.')

    for meta_vector_file in meta_vector_files:
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
            # print(intersection_cols)
            props = props.drop(intersection_cols, axis=1)
            vector = pandas.concat([meta, props], axis=1)
            if results is None:
                results = vector
            else:
                results = pandas.concat([results, vector])
        else:
            print('No prop file for', meta_vector_file.name)
    return results
