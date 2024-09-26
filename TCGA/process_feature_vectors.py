import argparse
import getpass
import re
import json
import pandas
from pathlib import Path

from matplotlib import colormaps
from sklearn.preprocessing import normalize

from .annotations import upload_annotation, write_annotation
from .constants import (ANNOTATIONS_FOLDER, CLASS_PREFIX, COLUMN_NAMES,
                        DOWNLOADS_FOLDER, REDUCE_DIMS_RESULTS_FOLDER)
from .read_vectors import get_case_vector
from .reduce_dims import plot_results, tsne, umap
from .clustering import find_clusters, find_cluster_distinction_columns


def process_feature_vectors(
    cases, rois, upload, reduce_dims, reduce_dims_func, no_cache, plot, exclude_column_patterns, groupby, clusters, cluster_distinctions,
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
            vector = None
            groups = None
            all_results = {}

            # manage result files
            case_results_folder = REDUCE_DIMS_RESULTS_FOLDER / reduce_dims_func / case_name
            if not case_results_folder.exists():
                case_results_folder.mkdir(parents=True, exist_ok=True)
            group_records_file =  case_results_folder / 'all_groups.json'
            group_records = {}
            if group_records_file.exists():
                with open(group_records_file) as f:
                    try:
                        group_records = json.load(f)
                    except json.JSONDecodeError:
                        pass

            # avoid loading case vector if only using previous result files
            if not (upload or no_cache):
                group_names = group_records.get(groupby)
                if group_names is not None:
                    for group_name in group_names:
                        group_result_file = case_results_folder / f'{group_name}.csv'
                        if group_result_file.exists():
                            group_result = pandas.read_csv(group_result_file, index_col=0)
                            all_results[group_name] = group_result

            if not len(all_results):
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

                # record groups
                group_records[groupby] = list(groups.groups.keys())
                with open(group_records_file, 'w') as f:
                    json.dump(group_records, f)

                # evaluate groups
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
                        result_filepath = Path(REDUCE_DIMS_RESULTS_FOLDER, reduce_dims_func, case_name, f'{group_name}.csv')
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

            # find clusters
            cluster_results = None
            if reduce_dims and clusters:
                clusters_file = case_results_folder / 'clusters.json'
                cluster_results = find_clusters(all_results, clusters_file=clusters_file, use_cache=not no_cache)
                if cluster_distinctions:
                    find_cluster_distinction_columns(case_name, clusters_file, groups, print_results=True)

            # show result plot
            if reduce_dims and plot:
                plot_results(all_results, title=case_name, cluster_results=cluster_results)

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
    parser.add_argument(
        '--clusters', action='store_true',
        help='Find clusters among dim reduction results. Only used if --reduce-dims is specified.'
    )
    parser.add_argument(
        '--cluster-distinctions', action='store_true',
        help='Determine which columns are most statistically different between clusters. Only used if --reduce-dims and --clusters are specified.'
    )
    args = vars(parser.parse_args(raw_args))
    cases, rois, upload, reduce_dims, reduce_dims_func, no_cache, plot, exclude_column_patterns, groupby, clusters, cluster_distinctions = (
        args.get('cases'),
        args.get('rois'),
        args.get('upload'),
        args.get('reduce_dims'),
        args.get('reduce_dims_func'),
        args.get('no_cache'),
        args.get('plot'),
        args.get('exclude_column_patterns'),
        args.get('groupby'),
        args.get('clusters'),
        args.get('cluster_distinctions')
    )
    process_feature_vectors(
       cases, rois, upload, reduce_dims, reduce_dims_func, no_cache, plot, exclude_column_patterns, groupby, clusters, cluster_distinctions,
    )


if __name__ == '__main__':
    main()
