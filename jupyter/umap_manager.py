import io
import json
from datetime import datetime
from pathlib import Path

import ipywidgets
import large_image
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import umap
from IPython.display import display
from PIL import Image
from sklearn.preprocessing import normalize

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
        self._data = self._raw_data = None
        self._image_path = self._image = None
        self._sample_size = None
        self._exclude_columns = []
        self._class_filters = None
        self._compute_density = True
        self._umap_kwargs = DEFAULT_UMAP_KWARGS
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
    def class_filters(self):
        return self._class_filters

    @class_filters.setter
    def class_filters(self, classes):
        if not isinstance(classes, list):
            raise ValueError('class_filters must be a list.')
        self._class_filters = classes

    @property
    def sample_size(self):
        return self._sample_size

    @sample_size.setter
    def sample_size(self, n):
        if not isinstance(n, int):
            raise ValueError('sample_size must be an integer.')
        self._sample_size = n

    @property
    def compute_density(self):
        return self._compute_density

    @compute_density.setter
    def compute_density(self, enable):
        if not isinstance(enable, bool):
            raise ValueError('compute_density must be a boolean.')
        self._compute_density = enable

    @property
    def data(self):
        if self._data is not None:
            return self._data
        else:
            data = self._raw_data
            # apply class filter
            if self.class_filters is not None:
                data = data[data['Classif.StandardClass'].isin(self._class_filters)]
            # sample full data
            if self.sample_size is not None:
                data = data.sample(self.sample_size)
            # compute density column
            if self.compute_density:
                idx = data.index
                data =  self.compute_density_column(data.reset_index())
                data.index = idx
            # drop excluded / non-numeric columns
            data = data.drop([
                c for c in data.columns
                if c in self.exclude_columns or
                str(data[c].dtype) != 'float64'
            ], axis=1).fillna(-1)
            self._data = data
            return data

    @property
    def normalized_data(self):
        return normalize(self.data, axis=1, norm='l1')

    @property
    def columns(self):
        return self._raw_data.columns

    @property
    def image(self):
        return self._image

    def reset(self):
        self._umap_kwargs = DEFAULT_UMAP_KWARGS
        self._exclude_columns = []
        self._sample_size = None

    def read_data(self, data_path):
        print('Reading HIPS data.')
        self._image_path = next(data_path.glob('*.svs'))
        if self._image_path:
            self._image = large_image.open(self._image_path)
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
                if self._raw_data is None:
                    self._raw_data = vector
                else:
                    self._raw_data = pd.concat([self._raw_data, vector])
        if self._raw_data is not None:
            print(f'Found {len(self._raw_data)} features.')
        else:
            print('Found no HIPS data.')

    def find_existing_result(self):
        for existing_result_file in self._result_path.glob('*.json'):
            with open(existing_result_file) as f:
                existing_result = json.load(f)
                if (
                    existing_result.get('umap_kwargs') == self._umap_kwargs and
                    existing_result.get('input_data') == self.normalized_data.tolist()
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
            input_data = self.normalized_data
            output_data = fit.fit_transform(input_data)
            with open(result_filepath, 'w') as f:
                json.dump(dict(
                    umap_kwargs=self._umap_kwargs,
                    input_data=input_data.tolist(),
                    output_data=output_data.tolist(),
                ), f)
        if plot:
            data = pd.DataFrame(output_data, columns=['x', 'y'])
            scatter = go.Scatter(
                x=data['x'],
                y=data['y'],
                mode='markers',
                marker=dict(color=data.index)
            )
            figure = go.FigureWidget(data=[scatter])
            cell_view = ipywidgets.VBox()

            def selection_callback(trace, points, selector):
                thumbnails = self.show_cell_thumbnails(trace.selectedpoints)
                cell_view.children = [
                    thumbnails
                ]

            figure.data[0].on_selection(selection_callback)
            display(figure)
            display(cell_view)
        else:
            return output_data

    def get_cell_thumbnails(self, cell_indexes=None):
        thumbnails = []
        if cell_indexes is None:
            cell_indexes = list(self.data.index)
        for i, index in enumerate(cell_indexes):
            cell = self._raw_data.iloc[index]
            scale_multiplier = 2
            margin = 10
            region = dict(
                left=max(int(cell['Identifier.Xmin']) * scale_multiplier - margin, 0),
                right=int(cell['Identifier.Xmax']) * scale_multiplier + margin,
                top=max(int(cell['Identifier.Ymin']) * scale_multiplier - margin, 0),
                bottom=int(cell['Identifier.Ymax']) * scale_multiplier + margin,
            )
            if len(self._raw_data['roiname'].unique()) > 1:
                roi_split = cell['roiname'].split('_')[2:]
                roi_region = {s.split('-')[0]: int(s.split('-')[1]) for s in roi_split}
                region['left'] += roi_region['left']
                region['right'] += roi_region['left']
                region['top'] += roi_region['top']
                region['bottom'] += roi_region['top']
            thumbnail, _ = self.image.getRegion(region=region, format='numpy')
            thumbnails.append(thumbnail)
        return thumbnails

    def show_cell_thumbnails(self, cell_indexes=None):
        thumbnails = self.get_cell_thumbnails(cell_indexes)
        children = []
        for thumbnail in thumbnails:
            f = io.BytesIO()
            im = Image.fromarray(thumbnail, 'RGB')
            im.save(f, 'png')
            children.append(ipywidgets.Image(value=f.getvalue(), format='png'))
        return ipywidgets.GridBox(children, layout=ipywidgets.Layout(grid_template_columns="repeat(10, 100px)"))

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

    def compute_density_column(self, data, n=5):
        from scipy.spatial.distance import cdist

        def absolute_location(cell):
            roi_split = cell['roiname'].split('_')[2:]
            roi_region = {s.split('-')[0]: int(s.split('-')[1]) for s in roi_split}
            scale_multiplier = 2
            cell['x'] = cell['Identifier.CentroidX'] * scale_multiplier + roi_region['left']
            cell['y'] = cell['Identifier.CentroidX'] * scale_multiplier + roi_region['top']
            return cell

        def nearest_n_density(distances):
            # exclude distance of 0 (distance to self)
            nearest_idx = np.argpartition(distances[distances > 0], n)
            nearest_distances = distances[nearest_idx[:n]]
            density = n / np.sum(nearest_distances)
            return density

        print('Computing density column.')
        locations = data.apply(absolute_location, axis=1)[['x', 'y']]
        distances = pd.DataFrame(
            cdist(locations, locations, metric='euclidean')
        )
        data['density'] = distances.apply(nearest_n_density, axis=1)
        return data
