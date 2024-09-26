import json
import numpy
import scipy.stats as stats

from datetime import datetime
from sklearn import cluster
from sklearn.metrics import silhouette_score

from .constants import COLUMN_NAMES, CLASS_PREFIX
from .read_vectors import get_case_vector


MAX_CLUSTERS = 5
RANDOM_STATE = 0
SIGNIFICANCE_LEVEL = 0.05
N_CORRELATION_COLS = 5


def get_optimal_clusters(data, group_name, clusters_file=None, use_cache=False):
    cached = {}
    if use_cache and clusters_file is not None and clusters_file.exists():
        with open(clusters_file) as f:
            try:
                cached = json.load(f)
                if cached.get(group_name) is not None:
                    return cached.get(group_name)
            except json.JSONDecodeError:
                pass
    start = datetime.now()
    optimal_clusters = None
    max_silhouette_score = -1
    # Try different n_clusters and return result with highest silhouette score
    for n in range(2, MAX_CLUSTERS):
        spectral = cluster.SpectralClustering(
            n_clusters=n,
            eigen_solver='arpack',
            affinity='nearest_neighbors',
            random_state=RANDOM_STATE,
        )
        spectral.fit(data)
        labels = spectral.labels_
        score = silhouette_score(data, labels)
        if score > max_silhouette_score:
            max_silhouette_score = score
            optimal_clusters = labels
    seconds = (datetime.now() - start).total_seconds()
    print(f'Got optimal clusters for {len(data)} {group_name} features in {seconds} seconds.')
    cached[group_name] = optimal_clusters.tolist()
    with open(clusters_file, 'w') as f:
        json.dump(cached, f)
    return cached[group_name]


def find_clusters(all_results, clusters_file=None, use_cache=False):
    cluster_results = {}
    for group_name, result in all_results.items():
        data = result.to_numpy()
        cluster_results[group_name] = get_optimal_clusters(
            data,
            group_name,
            clusters_file=clusters_file,
            use_cache=use_cache
        )
    return cluster_results


def find_cluster_distinction_columns(case_name, clusters_file, groups=None, print_results=False):
    distinction_columns = {}
    clusters = None
    with open(clusters_file) as f:
        clusters = json.load(f)

    if groups is None:
        vector = get_case_vector(case_name)
        class_cols = [c for c in COLUMN_NAMES if CLASS_PREFIX in c]
        classes = [c.replace(CLASS_PREFIX, '') for c in vector[class_cols].idxmax(axis=1)]
        vector = vector.assign(classification=classes)
        groups = vector.groupby('classification')

    for group_name, group in groups:
        start = datetime.now()
        labels = clusters.get(group_name)
        columns = [c for c, d in group.dtypes.to_dict().items() if d == numpy.float64]
        column_f_stats = {}
        if labels is not None:
            group = group.assign(cluster=labels)
            cluster_groups = group.groupby('cluster')
            for column_name in columns:
                column_per_cluster = [
                    cluster[column_name]
                    for cluster_id, cluster in cluster_groups
                ]
                f_stat, p_val = stats.f_oneway(*column_per_cluster)
                if p_val < SIGNIFICANCE_LEVEL:
                    column_f_stats[column_name] = float(f_stat)
            group_distinction_cols = dict(sorted(
                column_f_stats.items(),
                key=lambda item: item[1],
                reverse=True
            )[:N_CORRELATION_COLS])
            distinction_columns[group_name] = group_distinction_cols

            if print_results:
                seconds = (datetime.now() - start).total_seconds()
                print(f'Found cluster distinction columns for {group_name} in {seconds} seconds.')
                for col_name, f_val in group_distinction_cols.items():
                    print(f'\t{col_name}: {f_val}')
    return distinction_columns
