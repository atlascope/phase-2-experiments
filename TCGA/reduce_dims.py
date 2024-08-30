import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict

import matplotlib
import matplotlib.pyplot as plt
import pandas
import umap as umap_lib
from sklearn import manifold

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
        return pandas.read_csv(result_filepath, index_col=0)
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
        df.to_csv(result_filepath)
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
        return pandas.read_csv(result_filepath, index_col=0)
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
        df.to_csv(result_filepath)
        print(f'Completed in {datetime.now() - start} seconds.')
        return df
    except Exception as e:
        print(f'Error: {str(e)}. Skipping TSNE evaluation.')


# assumes n_components == 2
def plot_results(
    results: Dict[str, pandas.DataFrame],
):
    result_items = list(results.items())
    fig, subplots = plt.subplots(len(result_items), sharex=True, sharey=True)
    fig.suptitle('Dimensionality Reduction Results')

    i = 0
    for ax in subplots:
        result_title, result_data = result_items[i]
        x = result_data['x']
        y = result_data['y']
        ax.scatter(x, y, s=2)
        ax.set_title(result_title)
        i += 1
    plt.show()
