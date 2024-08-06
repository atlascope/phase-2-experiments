import numpy
import matplotlib.pyplot as plt
import matplotlib.cm as cm

from .scikit import get_tsne_result
from ..constants import (
    DOWNLOADS_FOLDER,
    COLUMN_NAMES,
    CLASSIF_PREFIX,
    COLORMAP,
    COLOR_LABEL_KEY,
    ROIS
)

PERPLEXITIES = [5, 30, 50, 100]
NUM_COMPONENTS = 2
MAX_ITERATIONS = 300


for case in DOWNLOADS_FOLDER.glob('*'):
    case_features = []
    case_name = case.name.split('.')[0]

    main_axes = None
    fig = plt.figure(figsize=(15, 15), layout='tight')
    fig.suptitle("TSNE Results")
    for i, perplexity in enumerate(PERPLEXITIES):
        result = get_tsne_result(
            case_name,
            ROIS,
            perplexity=perplexity,
            n_components=NUM_COMPONENTS,
            max_iterations=MAX_ITERATIONS,
            color_label_key=COLOR_LABEL_KEY,
        )
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
