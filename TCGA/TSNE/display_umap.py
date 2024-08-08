import numpy
import matplotlib.pyplot as plt
import matplotlib.cm as cm

from .umap import get_umap_result
from ..constants import (
    DOWNLOADS_FOLDER,
    COLUMN_NAMES,
    CLASSIF_PREFIX,
    COLORMAP,
    COLOR_LABEL_KEY,
    ROIS
)


for case in DOWNLOADS_FOLDER.glob('*'):
    case_features = []
    case_name = case.name.split('.')[0]

    fig = plt.figure(figsize=(15, 15), layout='tight')
    fig.suptitle("UMAP Results")
    result = get_umap_result(
        case_name,
        ROIS,
        color_label_key=COLOR_LABEL_KEY,
    )
    if result is not None:
        ax = plt.axes()
        ax.scatter(
            result['x'],
            result['y'],
            c=result['c'],
            s=2,
            cmap=COLORMAP
        )

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
