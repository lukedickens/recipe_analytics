# This is a hack to make the library in the parent folder available for imoprts
# A better solution is by np8 here:
# https://stackoverflow.com/questions/714063/importing-modules-from-parent-folder
import sys
import os
import inspect

thisdir = sys.path[0]
print(f"thisdir = {thisdir}")
parentdir = os.path.dirname(thisdir)
#print(f"parentdir = {parentdir}")
if not parentdir in sys.path:
    print("Adding parent directory to python path")
    sys.path.insert(1, parentdir)
else:
    print("Skipping adding parent direct to path (there already)")

print(f"sys.path =\n{sys.path}")

import scipy.sparse
#from scipy.sparse import dok_array, lil_array
#from scipy.sparse import csr_matrix, csr_array
import numpy as np
import timeit
import sklearn.cluster
import sklearn.metrics

from repurposing.sklearn_sparse.cluster_metrics import sparse_calinski_harabasz
from repurposing.sklearn_sparse.cluster_metrics import sparse_calinski_harabasz_alt
from repurposing.sklearn_sparse.cluster_metrics import sparse_davies_bouldin
from repurposing.sklearn_sparse.cluster_metrics import sparse_kmedoids_e_step
from repurposing.sklearn_sparse.cluster_metrics import sparse_kmedoids_m_step
from repurposing.sklearn_sparse.cluster_metrics import sparse_kmedoids_m_step_alt
from repurposing.sklearn_sparse.cluster_metrics import sparse_kmedoids

from repurposing.sklearn_sparse.mem_utils import get_nparray_memory_usage
from repurposing.sklearn_sparse.mem_utils import get_csr_memory_usage

from repurposing.sklearn_sparse.synthetic_data import generate_csr_matrix
from repurposing.sklearn_sparse.synthetic_data import generate_sparse_cluster_data

print(f"creating data")
num_cluster_seq = [ 3, 4, 5, 6, 7 , 8 , 9 , 10]
num_rows_seq = [50, 100, 150, 200, 250]
num_cols_seq = [50, 100, 150, 200, 250]
results = {}
for num_clusters in num_cluster_seq:
    Ns = np.zeros(dtype=int)
    for num_rows in num_rows_seq:
        # set the number of rows per cluster as balanced
        Ns[:] = num_rows // num_clusters
        Ns[:num_rows % num_clusters] += 1 
        for D in num_cols_seq:
            for density in [0.0001, 0.0002, 0.0005, 0.001, 0.002]:
                for col_density in [0.01 0.02, 0.05, 0.1]:
                    data, gt_cluster_ids = generate_sparse_cluster_data(
                        Ns, D=D, density=density, col_density=col_density)
                    print(f"creating model")
                    params = dict(
                        n_clusters=num_clusters, init='k-means++', max_iter=100,
                        batch_size=1024,
                        verbose=0, compute_labels=True, random_state=None, tol=0.0,
                        max_no_improvement=10, init_size=None, n_init=3,
                        reassignment_ratio=0.01)
                        model = sklearn.cluster.MiniBatchKMeans(**params)
                        start = timeit.default_timer()
                        model.fit(data)
                        stop = timeit.default_timer()
                        fit_time = stop - start
                        print(f"fit_time =  {fit_time}") 

                        adj_rand_score = sklearn.metrics.adjusted_rand_score(
                            gt_cluster_ids, model.labels_)
                        print(f"adj_rand_score = {adj_rand_score}")

