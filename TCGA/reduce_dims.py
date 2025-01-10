import argparse
import math
import os
import re
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import matplotlib
import matplotlib.pyplot as plt
import pandas
import umap as umap_lib
from sklearn import manifold
from sklearn.preprocessing import normalize

from .constants import PLOTS_FOLDER, DOWNLOADS_FOLDER, REDUCE_DIMS_RESULTS_FOLDER, COLUMN_NAMES
from .read_vectors import get_case_vector
from .client import get_client, get_case_folder_item, sync_file

# suppress warnings
warnings.simplefilter("ignore")

def umap(
    vector: pandas.DataFrame,
    result_filepath: Path,
    use_cache: bool=True,
    n_components: int=2,
    n_neighbors: int=15,
    init: str='random'
):
    if result_filepath.exists() and use_cache:
        return pandas.read_parquet(result_filepath)
    if not result_filepath.parent.exists():
        result_filepath.parent.mkdir(parents=True, exist_ok=True)

    print(f'\tEvaluating UMAP for {len(vector)} features... ', end='')
    start = datetime.now()
    # https://umap-learn.readthedocs.io/en/latest/parameters.html
    reducer = umap_lib.UMAP(
        n_components=n_components,
        n_neighbors=n_neighbors,
        init=init,
    )
    try:
        result = reducer.fit_transform(vector.to_numpy())
        df = pandas.DataFrame(
            result,
            index=vector.index,
            columns=['x', 'y']
        )
        df.to_parquet(result_filepath)
        print(f'Completed in {datetime.now() - start} seconds.')
        return df
    except Exception as e:
        print(f'Error: {str(e)}. Skipping UMAP evaluation.')


def tsne(
    vector: pandas.DataFrame,
    result_filepath: Path,
    use_cache: bool=True,
    perplexity: int=100,
    n_components: int=2,
    max_iterations: int=300,
    init: str='random'
):
    if result_filepath.exists() and use_cache:
        return pandas.read_parquet(result_filepath)
    if not result_filepath.parent.exists():
        result_filepath.parent.mkdir(parents=True, exist_ok=True)

    print(f'\tEvaluating TSNE for {len(vector)} features... ', end='')
    start = datetime.now()
    # https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html
    tsne = manifold.TSNE(
        perplexity=perplexity,
        n_components=n_components,
        max_iter=max_iterations,
        init=init,
    )
    try:
        result = tsne.fit_transform(vector.to_numpy())
        df = pandas.DataFrame(
            result,
            index=vector.index,
            columns=[['x', 'y', 'z'][i] for i in range(n_components)]
        )
        df.to_parquet(result_filepath)
        print(f'Completed in {datetime.now() - start} seconds.')
        return df
    except Exception as e:
        print(f'Error: {str(e)}. Skipping TSNE evaluation.')


# assumes n_components == 2
def plot_results(
    results: Dict[str, pandas.DataFrame],
    title='Dimensionality Reduction Results',
    cluster_results: Optional[Dict[str, list]] = None,
    show=True,
    save=True,
):
    result_items = list(results.items())
    subplots_width = round(math.sqrt(len(result_items)))
    subplots_height = math.ceil(len(result_items) / subplots_width)
    fig, subplots = plt.subplots(
        subplots_width,
        subplots_height,
        sharex=True,
        sharey=True,
    )
    fig.suptitle(title)

    i = 0
    for row in subplots:
        for ax in row:
            if i < len(result_items):
                result_title, result_data = result_items[i]
                x = result_data['x']
                y = result_data['y']
                c = cluster_results.get(result_title, None) if cluster_results is not None else None
                ax.scatter(x, y, c=c, s=2)
                ax.set_title(result_title)
                i += 1
    if not PLOTS_FOLDER.exists():
        os.mkdir(PLOTS_FOLDER)
    if save:
        plt.savefig(PLOTS_FOLDER / (title.replace(' ', '_') + '.png'))
    if show:
        plt.show()


def main(raw_args=None):
    parser = argparse.ArgumentParser(
        prog="ReduceDims",
        description="Process feature vectors and optionally upload resulting annotations",
    )
    parser.add_argument(
        '--cases', nargs='*',
        help='List of case names to process. If not specified, process all downloaded cases.'
    )
    parser.add_argument(
        '--reduce_dims_func', choices=['umap', 'tsne'], default='umap',
        help='Function to use for dimensionality reduction. Only used if --reduce-dims is specified. Default=umap.'
    )
    parser.add_argument(
        '--no-cache', action='store_true',
        help='Do not use cached results for dimensionality reduction. Only used if --reduce-dims is specified.'
    )
    parser.add_argument(
        '--exclude-column-patterns', nargs='*',
        help='List of regex patterns. Exclude matching column names from dimensionality reduction.'
    )
    parser.add_argument(
        '--plot', action='store_true',
        help='Display plots of dimensionality reduction results. Only used if --reduce-dims is specified.'
    )
    parser.add_argument(
        '--upload', action='store_true',
        help='Upload dimensionality reduction results to Girder.'
    )
    parser.add_argument(
        '--username', type=str, help='Girder username for upload'
    )
    parser.add_argument(
        '--password', type=str, help='Girder password for upload'
    )
    args = vars(parser.parse_args(raw_args))

    cases = args.get('cases')
    reduce_dims_func = args.get('reduce_dims_func')
    no_cache = args.get('no_cache')
    exclude_column_patterns = args.get('exclude_column_patterns')
    plot = args.get('plot')
    upload = args.get('upload')
    username = args.get('username')
    password = args.get('password')

    client = None
    if upload:
        client = get_client(username, password)

    all_results = {}
    for case in DOWNLOADS_FOLDER.glob('*'):
        case_name = case.name.split('.')[0]
        if cases is None or case_name in cases:
            print(f'Evaluating {case_name}.')
            case_results_folder = REDUCE_DIMS_RESULTS_FOLDER / reduce_dims_func / case_name
            if not case_results_folder.exists():
                case_results_folder.mkdir(parents=True, exist_ok=True)

            result_file = None
            result_filename = f'{case_name} {reduce_dims_func.upper()}*.parquet'
            result_files = list(case_results_folder.glob(result_filename))

            if len(result_files) and not no_cache:
                result_files.sort()
                result_file = result_files[0]
            else:
                # compute dimensionality reduction results
                result_file = case_results_folder / result_filename.replace('*', f' ({len(result_files)})')
                vector = get_case_vector(case_name)
                if exclude_column_patterns is not None:
                    vector = vector.drop([
                        c for c in COLUMN_NAMES if any(re.match(fr'{pattern}', c) for pattern in exclude_column_patterns)
                    ], axis=1, errors='ignore')
                vector = vector.drop([
                    c for c in vector.columns
                    if str(vector[c].dtype) != 'float64'
                ], axis=1).fillna(-1)
                normalize(vector, axis=1, norm='l1')

                if reduce_dims_func == 'umap':
                    umap(vector, result_file, use_cache=not no_cache)
                elif reduce_dims_func == 'tsne':
                    tsne(vector, result_file, use_cache=not no_cache)

            if result_file is not None and result_file.exists():
                all_results[case_name] = pandas.read_parquet(result_file)
                if upload:
                    print(f'Uploading {result_file.name} to Girder.')
                    case_folder_item = get_case_folder_item(client, case_name)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sync_file(
                        client,
                        case_folder_item,
                        result_file,
                        timestamp=timestamp,
                        exclude_column_patterns=exclude_column_patterns,
                    )

    if plot:
        plot_results(all_results)


if __name__ == '__main__':
    main()
