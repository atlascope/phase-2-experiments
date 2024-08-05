import pandas
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from sklearn import manifold

from ..read_vectors import get_case_vector


RESULTS_FOLDER = Path(__file__).parent / 'results'


def get_tsne_result(
    case_name,
    roiname,
    n_components=2,
    perplexity=100,
    max_iterations=300,
    color_label_key=None
):
    filepath = RESULTS_FOLDER / 'scikit' / case_name / f'{n_components}_components' / f'perplexity_{perplexity}' / roiname
    if filepath.exists():
        return pandas.read_csv(filepath, index_col=0)
    else:
        if not filepath.parent.exists():
            filepath.parent.mkdir(parents=True, exist_ok=True)

        vector = get_case_vector(case_name, rois=[roiname])
        # remove any columns that cannot be cast to float
        vector.drop(
            [c for c in vector.columns if str(vector[c].dtype) != 'float64'],
            axis=1,
            inplace=True
        )
        vector.fillna(-1, inplace=True)
        if color_label_key is not None:
            colors = [color_label_key[c] for c in vector[color_label_key.keys()].idxmax(axis=1)]
        else:
            colors = []
        print(f'\tEvaluating TSNE with perplexity={perplexity} for {len(vector)} features...')
        start = datetime.now()
        tsne = manifold.TSNE(
            n_components=n_components,
            perplexity=perplexity,
            init="random",
            random_state=0,
            max_iter=max_iterations,
        )
        try:
            result = tsne.fit_transform(vector.to_numpy())
            df = pandas.DataFrame(
                result,
                columns=[['x', 'y', 'z'][i] for i in range(n_components)]
            )
            df = df.assign(c=colors)
            df.to_csv(filepath)
            print(f'\tCompleted TSNE evaluation in {datetime.now() - start} seconds.')
            return df
        except Exception as e:
            print('\tSkipping TSNE Evaluation:', str(e))
