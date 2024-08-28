import pandas

from .constants import DOWNLOADS_FOLDER


def get_case_vector(case_name, rois=None):
    results = None
    case_folder = next(DOWNLOADS_FOLDER.glob(case_name))
    meta_vectors = case_folder / 'nucleiMeta'
    prop_vectors = case_folder / 'nucleiProps'
    meta_vector_files = list(meta_vectors.glob('*.csv'))
    prop_vector_files = list(prop_vectors.glob('*.csv'))
    num_regions = len(meta_vector_files) if rois is None else len(rois)
    print(f'\tReading features in {num_regions} region(s).')

    for meta_vector_file in meta_vector_files:
        roi_name = meta_vector_file.name.replace('.csv', '')
        if rois is None or roi_name in rois:
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
    print(f'\tFound {len(results)} features.')
    return results
