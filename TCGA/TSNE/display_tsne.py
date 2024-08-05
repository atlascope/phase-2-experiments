import json
import numpy
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.cm as cm

from .scikit import get_tsne_result as get_scikit_tsne_result


DOWNLOADS_FOLDER = Path(__file__).parent.parent / 'downloads'
COLUMN_NAMES = Path(__file__).parent.parent / 'column_names.json'
CLASSIF_PREFIX = 'Unconstrained.ClassifProbab.'
COLORMAP = 'Set1'

LIBRARY = 'scikit'
PERPLEXITIES = [5, 30, 50, 100]
NUM_COMPONENTS = 2
MAX_ITERATIONS = 300
NUM_ROIS = 3

with open(COLUMN_NAMES) as f:
    column_names = json.load(f)
    classif_columns = [c for c in column_names if c.startswith(CLASSIF_PREFIX)]
    COLOR_LABEL_KEY = {c: i for i, c in enumerate(classif_columns)}

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
            if LIBRARY == 'scikit':
                result = get_scikit_tsne_result(
                    case_name,
                    roiname,
                    perplexity=perplexity,
                    n_components=NUM_COMPONENTS,
                    max_iterations=MAX_ITERATIONS,
                    color_label_key=COLOR_LABEL_KEY,
                )
            else:
                raise ValueError(f'Unknown library "{LIBRARY}". Options are ["scikit"].')

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
