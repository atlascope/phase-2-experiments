import json
from pathlib import Path


DOWNLOADS_FOLDER = Path(__file__).parent / 'downloads'
ANNOTATIONS_FOLDER = Path(__file__).parent / 'annotations'
REDUCE_DIMS_RESULTS_FOLDER = Path(__file__).parent / 'reduce_dims_results'
COLUMN_NAMES_FILE = Path(__file__).parent / 'column_names.json'
CLASS_PREFIX = 'Unconstrained.ClassifProbab.'

with open(COLUMN_NAMES_FILE) as f:
    COLUMN_NAMES = json.load(f)

with open('conf.json') as f:
    CONF = json.load(f)
