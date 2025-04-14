import pandas as pd
import umap
import json

import numpy as np
import plotly.express as px
from sklearn.preprocessing import normalize
from datetime import datetime
from pathlib import Path


# from https://umap-learn.readthedocs.io/en/latest/api.html
DEFAULT_UMAP_KWARGS = dict(
    n_neighbors=15,
    n_components=2,
    metric='euclidean',
    metric_kwds=None,
    output_metric='euclidean',
    output_metric_kwds=None,
    n_epochs=None,
    learning_rate=1.0,
    init='spectral',
    min_dist=0.1,
    spread=1.0,
    low_memory=True,
    n_jobs=-1,
    set_op_mix_ratio=1.0,
    local_connectivity=1.0,
    repulsion_strength=1.0,
    negative_sample_rate=5,
    transform_queue_size=4.0,
    a=None,
    b=None,
    random_state=None,
    angular_rp_forest=False,
    target_n_neighbors=-1,
    target_metric='categorical',
    target_metric_kwds=None,
    target_weight=0.5,
    transform_seed=42,
    transform_mode='embedding',
    force_approximation_algorithm=False,
    verbose=False,
    tqdm_kwds=None,
    unique=False,
    densmap=False,
    dens_lambda=2.0,
    dens_frac=0.3,
    dens_var_shift=0.1,
    output_dens=False,
    disconnection_distance=None,
    precomputed_knn=[None, None, None]
)


class UMAPManager():
    def __init__(self, data_path=None, result_path=None, **kwargs):
        self._data_path = Path(data_path)
        self._result_path = Path(result_path)
        self._result_path.mkdir(exist_ok=True, parents=True)
        self._data = None
        self._umap_kwargs = DEFAULT_UMAP_KWARGS
        self._exclude_columns = []
        if data_path is not None:
            self.read_data(data_path)

    @property
    def umap_kwargs(self):
        return self._umap_kwargs

    @umap_kwargs.setter
    def umap_kwargs(self, kwarg_set):
        self._umap_kwargs.update({
            k: v for k, v in kwarg_set.items() if k in DEFAULT_UMAP_KWARGS.keys()
        })

    @property
    def exclude_columns(self):
        return self._exclude_columns

    @exclude_columns.setter
    def exclude_columns(self, cols):
        if not isinstance(cols, list):
            raise ValueError('exclude_columns must be a list.')
        self._exclude_columns = cols

    @property
    def data(self):
        data = self._data
        # drop excluded / non-numeric columns
        data = data.drop([
            c for c in data.columns
            if c in self.exclude_columns or
            str(data[c].dtype) != 'float64'
        ], axis=1).fillna(-1)
        # normalize
        normalize(data, axis=1, norm='l1')
        return data

    @property
    def columns(self):
        return self._data.columns

    def reset(self):
        self._umap_kwargs = DEFAULT_UMAP_KWARGS
        self._exclude_columns = []

    def read_data(self, data_path):
        print('Reading HIPS data.')
        meta_vector_files = list((data_path / 'nucleiMeta').glob('*.csv'))
        prop_vector_files = list((data_path / 'nucleiProps').glob('*.csv'))
        for meta_vector_file in meta_vector_files:
            prop_vector_file = next((
                f for f in prop_vector_files
                if f.name == meta_vector_file.name
            ), None)
            if prop_vector_file:
                meta = pd.read_csv(
                    str(meta_vector_file),
                    usecols=lambda x: 'Unnamed' not in x
                ).reset_index(drop=True)
                props = pd.read_csv(
                    str(prop_vector_file),
                    usecols=lambda x: 'Unnamed' not in x
                ).reset_index(drop=True)
                intersection_cols = list(meta.columns.intersection(props.columns))
                props = props.drop(intersection_cols, axis=1)
                vector = pd.concat([meta, props], axis=1)
                if self._data is None:
                    self._data = vector
                else:
                    self._data = pd.concat([self._data, vector])
        if self._data is not None:
            print(f'Found {len(self._data)} features.')
        else:
            print('Found no HIPS data.')

    def find_existing_result(self):
        for existing_result_file in self._result_path.glob('*.json'):
            with open(existing_result_file) as f:
                existing_result = json.load(f)
                if (
                    existing_result.get('umap_kwargs') == self._umap_kwargs and
                    existing_result.get('input_data') == self.data.to_numpy().tolist()
                ):
                    return np.array(existing_result.get('output_data'))

    def reduce_dims(self, plot=False, **kwargs):
        exclude_columns = kwargs.pop('exclude_columns', None)
        if exclude_columns is not None:
            self.exclude_columns = exclude_columns
        self.umap_kwargs = kwargs
        output_data = self.find_existing_result()
        if output_data is None:
            filename = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f") + '.json'
            result_filepath = self._result_path / filename
            fit = umap.UMAP(**self._umap_kwargs)
            input_data = self.data.to_numpy()
            output_data = fit.fit_transform(input_data)
            with open(result_filepath, 'w') as f:
                json.dump(dict(
                    umap_kwargs=self._umap_kwargs,
                    input_data=input_data.tolist(),
                    output_data=output_data.tolist(),
                ), f)
        if plot:
            data = pd.DataFrame(output_data, columns=['x', 'y'])
            px.scatter(data, x='x', y='y', color=data.index).show()
        return output_data

    def compare_reductions(self, **reductions):
        data = None
        max_x = max_y = 0
        min_x = min_y = 9999
        for name, kwarg_set in reductions.items():
            output = self.reduce_dims(plot=False, **kwarg_set)
            mxx = np.max(output[:, 0])
            if max_x < mxx:
                max_x = mxx
            mnx = np.min(output[:, 0])
            if min_x > mnx:
                min_x = mnx
            mxy = np.max(output[:, 1])
            if max_y < mxy:
                max_y = mxy
            mny = np.min(output[:, 1])
            if min_y > mny:
                min_y = mny
            current = pd.DataFrame(output, columns=['x', 'y'])
            current['set'] = name
            if data is None:
                data = current
            else:
                data = pd.concat([data, current])

        if data is not None:
            px.scatter(
                data,
                x='x', y='y',
                range_x=[min_x, max_x],
                range_y=[min_y, max_y],
                animation_frame='set',
                animation_group=data.index,
                color=data.index,
            ).show()
