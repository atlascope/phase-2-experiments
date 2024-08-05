import json
import pandas
import numpy
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from sklearn import manifold

from ..read_vectors import get_case_vector


DOWNLOADS_FOLDER = Path(__file__).parent.parent / 'downloads'
RESULTS_FOLDER = Path(__file__).parent / 'results'
COLUMN_NAMES = Path(__file__).parent.parent / 'column_names.json'
CLASSIF_PREFIX = 'Unconstrained.ClassifProbab.'
COLORMAP = 'Set1'

PERPLEXITIES = [5, 30, 50, 100]
NUM_COMPONENTS = 2
MAX_ITERATIONS = 300
NUM_ROIS = 3

with open(COLUMN_NAMES) as f:
    column_names = json.load(f)
    classif_columns = [c for c in column_names if c.startswith(CLASSIF_PREFIX)]
    COLOR_LABEL_KEY = {c: i for i, c in enumerate(classif_columns)}


def get_tsne_result(case_name, roiname, n_components=2, perplexity=100):
    filepath = RESULTS_FOLDER / 'scikit' / case_name / f'{n_components}_components' / f'perplexity_{perplexity}' / roiname
    if filepath.exists():
        return pandas.read_csv(filepath)
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
        colors = [COLOR_LABEL_KEY[c] for c in vector[COLOR_LABEL_KEY.keys()].idxmax(axis=1)]
        print(f'\tEvaluating TSNE with perplexity={perplexity} for {len(vector)} features...')
        start = datetime.now()
        tsne = manifold.TSNE(
            n_components=n_components,
            perplexity=perplexity,
            init="random",
            random_state=0,
            max_iter=MAX_ITERATIONS,
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


for case in DOWNLOADS_FOLDER.glob('*'):
    case_features = []
    case_name = case.name.split('.')[0]

    for roi_csv in list((case / 'nucleiMeta').glob('*.csv'))[:NUM_ROIS]:
        roiname = roi_csv.name.replace('.csv', '')
        print(roiname)
        main_axes = None
        fig = plt.figure(figsize=(15, 15), layout='tight')
        fig.suptitle(roiname)
        for i, perplexity in enumerate(PERPLEXITIES):
            result = get_tsne_result(case_name, roiname, NUM_COMPONENTS, perplexity)
            if result is not None:
                components = [result[['x', 'y', 'z'][i]] for i in range(NUM_COMPONENTS)]
                ax = fig.add_subplot(
                    1,
                    len(PERPLEXITIES),
                    i + 1,
                    sharex=main_axes,
                    sharey=main_axes,
                    title=f"Perplexity={perplexity}",
                    projection='3d' if NUM_COMPONENTS == 3 else None,
                )
                ax.scatter(
                    *components,
                    c=result['c'],
                    s=2,
                    cmap=COLORMAP
                )
                if main_axes is None:
                    main_axes = ax

        cbar = fig.colorbar(
            cm.ScalarMappable(cmap=COLORMAP),
            ax=ax,
            label='Classification',
        )
        yticks = numpy.linspace(*cbar.ax.get_ylim(), len(COLOR_LABEL_KEY) + 1)[:-1]
        yticks += (yticks[1] - yticks[0]) / 2
        cbar.set_ticks(
            yticks,
            labels=[c.replace(CLASSIF_PREFIX, '') for c in COLOR_LABEL_KEY.keys()],
        )
        cbar.ax.tick_params(length=0)
        plt.show()
