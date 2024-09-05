import argparse
import getpass
import re
from pathlib import Path

from matplotlib import colormaps
from sklearn.preprocessing import normalize

from .annotations import upload_annotation, write_annotation
from .constants import (ANNOTATIONS_FOLDER, CLASS_PREFIX, COLUMN_NAMES,
                        DOWNLOADS_FOLDER, REDUCE_DIMS_RESULTS_FOLDER)
from .read_vectors import get_case_vector
from .reduce_dims import plot_results, tsne, umap


def process_feature_vectors(
    cases, rois, upload, reduce_dims, reduce_dims_func, no_cache, plot, exclude_column_patterns, groupby
):
    username = None
    password = None
    if upload:
        print('Specified upload=True; will overwrite existing annotations on selected cases. Specify Girder credentials below.')
        username = input('Girder Username: ')
        password = getpass.getpass('Girder Password: ')

    for case in DOWNLOADS_FOLDER.glob('*'):
        case_name = case.name.split('.')[0]
        if cases is None or case_name in cases:
            print(f'Evaluating {case_name}.')
            vector = get_case_vector(case_name, rois=rois)

            # create groups
            groups = {'all': vector}.items()
            if groupby == 'roi':
                groups = vector.groupby('roiname')
            if groupby == 'class':
                class_cols = [c for c in COLUMN_NAMES if CLASS_PREFIX in c]
                classes = [c.replace(CLASS_PREFIX, '') for c in vector[class_cols].idxmax(axis=1)]
                vector = vector.assign(classification=classes)
                groups = vector.groupby('classification')

            # evaluate groups
            all_results = {}
            for group_name, group in groups:
                print(f'\tEvaluating group "{group_name}".')
                group_copy = group.copy()

                # remove any excluded columns
                if exclude_column_patterns is not None:
                    group_copy = group_copy.drop([
                        c for c in COLUMN_NAMES if any(re.match(fr'{pattern}', c) for pattern in exclude_column_patterns)
                    ], axis=1, errors='ignore')

                # clean and normalize data
                group_copy = group_copy.drop([
                    c for c in group_copy.columns
                    if str(group_copy[c].dtype) != 'float64'
                ], axis=1).fillna(-1)
                normalize(group_copy, axis=1, norm='l1')

                # get dimensionality reduction results
                result = None
                if reduce_dims:
                    result_filepath = Path(REDUCE_DIMS_RESULTS_FOLDER, reduce_dims_func, case_name, f'{group_name}.json')
                    if reduce_dims_func == 'umap':
                        result = umap(group_copy, result_filepath, use_cache=not no_cache)
                    elif reduce_dims_func == 'tsne':
                        result = tsne(group_copy, result_filepath, use_cache=not no_cache)

                if result is not None:
                    all_results[group_name] = result

                annotation_filepath = Path(ANNOTATIONS_FOLDER, case_name, f'{group_name}.json')
                write_annotation(annotation_filepath, group, result)

                if upload:
                    upload_annotation(case_name, annotation_filepath, username, password)

            # show result plot
            if reduce_dims and plot:
                plot_results(all_results, title=case_name)

    print('Done.')

def main(raw_args=None):
    parser = argparse.ArgumentParser(
        prog="FeatureVectorProcess",
        description="Process feature vectors and optionally upload resulting annotations",
    )
    parser.add_argument(
        '--cases', nargs='*',
        help='List of case names to process. If not specified, process all downloaded cases.'
    )
    parser.add_argument(
        '--rois', nargs='*',
        help='List of ROI names to process. If not specified, process all ROIs.'
    )
    parser.add_argument(
        '--upload', action='store_true',
        help='Write annotations and upload to target_server specified in conf.json. Will overwrite previous annotations on items.'
    )
    parser.add_argument(
        '--reduce-dims', action='store_true',
        help='Reduce dimensionality of feature vectors and include results in annotation.'
    )
    parser.add_argument(
        '--reduce-dims-func', choices=['umap', 'tsne'], default='umap',
        help='Function to use for dimensionality reduction. Only used if --reduce-dims is specified. Default=umap.'
    )
    parser.add_argument(
        '--no-cache', action='store_true',
        help='Do not use cached results for dimensionality reduction. Only used if --reduce-dims is specified.'
    )
    parser.add_argument(
        '--plot', action='store_true',
        help='Display plots of dimensionality reduction results. Only used if --reduce-dims is specified.'
    )
    parser.add_argument(
        '--exclude-column-patterns', nargs='*',
        help='List of regex patterns. Exclude matching column names from dimensionality reduction.'
    )
    parser.add_argument(
        '--groupby', choices=['roi', 'class'],
        help='Process feature vectors in multiple groups, separated by this attribute. If not specified, process all feature vectors in one group.'
    )
    args = vars(parser.parse_args(raw_args))
    cases, rois, upload, reduce_dims, reduce_dims_func, no_cache, plot, exclude_column_patterns, groupby = (
        args.get('cases'),
        args.get('rois'),
        args.get('upload'),
        args.get('reduce_dims'),
        args.get('reduce_dims_func'),
        args.get('no_cache'),
        args.get('plot'),
        args.get('exclude_column_patterns'),
        args.get('groupby'),
    )
    process_feature_vectors(
       cases, rois, upload, reduce_dims, reduce_dims_func, no_cache, plot, exclude_column_patterns, groupby
    )


if __name__ == '__main__':
    main()
