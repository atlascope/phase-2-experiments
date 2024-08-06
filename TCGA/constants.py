import json
from pathlib import Path
from matplotlib import colormaps


DOWNLOADS_FOLDER = Path(__file__).parent / 'downloads'
ANNOTATIONS_FOLDER = Path(__file__).parent / 'annotations'
TSNE_RESULTS_FOLDER = Path(__file__).parent / 'TSNE' / 'results'

COLUMN_NAMES = Path(__file__).parent / 'column_names.json'
CLASSIF_PREFIX = 'Unconstrained.ClassifProbab.'
COLORMAP = colormaps['Set1']

INCLUDE_TSNE = True
TSNE_PERPLEXITY = 100
TSNE_NUM_COMPONENTS = 2
ROIS = [
    "TCGA-3C-AALI-01Z-00-DX1_roi-2_left-15953_top-51923_right-18001_bottom-53971",
    "TCGA-3C-AALI-01Z-00-DX1_roi-3_left-15953_top-53971_right-18001_bottom-56019",
    "TCGA-3C-AALI-01Z-00-DX1_roi-4_left-15953_top-56019_right-18001_bottom-58067",
]

OVERWRITE = True

with open(COLUMN_NAMES) as f:
    column_names = json.load(f)
    classif_columns = [c for c in column_names if c.startswith(CLASSIF_PREFIX)]
    COLOR_LABEL_KEY = {c: i for i, c in enumerate(classif_columns)}


with open('conf.json') as f:
    CONF = json.load(f)
