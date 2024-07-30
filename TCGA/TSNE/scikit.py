import pandas
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
from sklearn import manifold

from ..read_vectors import get_case_vector


DOWNLOADS_FOLDER = Path(__file__).parent.parent / 'downloads'
PERPLEXITIES = [5, 30, 50, 100]
N_COMPONENTS = 3


for case in DOWNLOADS_FOLDER.glob('*'):
    case_features = []
    case_name = case.name.split('.')[0]

    print(f'{case_name}')
    (fig, subplots) = plt.subplots(1, 4, figsize=(15, len(PERPLEXITIES)))
    vector = get_case_vector(case_name)

    # whole vectors take 40-70 minutes; test with just one ROI
    # comment the following two lines to compute whole image:
    target_roi = vector['roiname'].mode()[0]
    vector = vector[vector['roiname'] == target_roi]

    # remove any columns that cannot be cast to float
    vector.drop(
        [c for c in vector.columns if str(vector[c].dtype) != 'float64'],
        axis=1,
        inplace=True
    )
    vector.fillna(-1, inplace=True)

    for i, perplexity in enumerate(PERPLEXITIES):
        print(f'\tEvaluating TSNE with perplexity={perplexity} for {len(vector)} features...')
        start = datetime.now()
        ax = subplots[i]

        tsne = manifold.TSNE(
            n_components=N_COMPONENTS,
            init="random",
            random_state=0,
            perplexity=perplexity,
            max_iter=300,
        )
        result = tsne.fit_transform(vector.to_numpy())
        print(f'\tCompleted TSNE evaluation  in {datetime.now() - start} seconds.')

        ax.set_title(f"Perplexity={perplexity}")
        ax.scatter(
            result[:, 0],
            result[:, 1],
            c=(result[:, 2] if N_COMPONENTS == 3 else 'g'),
        )

plt.show()
