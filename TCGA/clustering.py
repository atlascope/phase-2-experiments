import json

from datetime import datetime
from sklearn import cluster
from sklearn.metrics import silhouette_score


MAX_CLUSTERS = 5
RANDOM_STATE = 0


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
