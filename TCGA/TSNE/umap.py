import pandas
from datetime import datetime
from sklearn.preprocessing import normalize
import umap

from ..read_vectors import get_case_vector
from ..constants import TSNE_RESULTS_FOLDER, TSNE_EXCLUDE_COLUMNS


def get_umap_result(
    case_name,
    rois,
    color_label_key=None,
    vector=None
):
    filename = 'all.csv'
    if rois is not None:
        filename = '&'.join(rois) + '.csv'
    filepath = TSNE_RESULTS_FOLDER / 'umap' / case_name / filename
    if filepath.exists():
        return pandas.read_csv(filepath, index_col=0)
    else:
        if not filepath.parent.exists():
            filepath.parent.mkdir(parents=True, exist_ok=True)

        if vector is None:
            vector = get_case_vector(case_name, rois=rois)
        if color_label_key is not None:
            colors = [color_label_key[c] for c in vector[color_label_key.keys()].idxmax(axis=1)]
        else:
            colors = None

        # remove any columns that cannot be cast to float
        vector.drop(
            [
                c for c in vector.columns
                if str(vector[c].dtype) != 'float64' or c in TSNE_EXCLUDE_COLUMNS
            ],
            axis=1,
            inplace=True
        )
        vector.fillna(-1, inplace=True)
        normalize(vector, axis=1, norm='l1')

        print(f'\tEvaluating UMAP for {len(vector)} features...')
        start = datetime.now()
        reducer = umap.UMAP()
        try:
            result = reducer.fit_transform(vector.to_numpy())
            df = pandas.DataFrame(
                result,
                columns=['x', 'y']
            )
            if colors is not None:
                df = df.assign(c=colors)
            df.to_csv(filepath)
            print(f'\tCompleted TSNE evaluation in {datetime.now() - start} seconds.')
            return df
        except Exception as e:
            print('\tSkipping TSNE Evaluation:', str(e))
