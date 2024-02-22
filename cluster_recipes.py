import scipy.sparse
from scipy.sparse import dok_array, lil_array
from scipy.sparse import csr_matrix
import csv
from sklearn.cluster import KMeans
import numpy as np
import timeit
import time

# homegrown imports
from repurposing.sklearn_sparse.cluster_metrics import sparse_calinski_harabasz
from repurposing.sklearn_sparse.cluster_metrics import sparse_calinski_harabasz_alt
from repurposing.sklearn_sparse.cluster_metrics import sparse_davies_bouldin


def load_data(ifname):
    """
    Loads a csr matric from csv file
    with rows: rid, iid
    For recipe id, ingredient_id pairs
    
    Returns sparse matrix with 1 in each cell where 
        i=rid, and j=iid 
    """
    # load data from file
    pair_list = []
    max_rid = 0
    max_iid = 0
    with open(ifname, 'r') as ifile:
        reader = csv.reader(ifile)
        for line in reader:
            rid = int(line[0])
            iid = int(line[1])
            pair_list.append((rid,iid))
            rid = max(max_rid, rid)
            iid = max(max_iid, iid)
    lil_pam = lil_matrix((max_rid, max_iid), dtype=bool)
    for rid, iid in pair_list:
        lil_pam[rid, iid] = 1
    del pair_list
    csr_pam = csr_matrix(lil_pam)         
    return csr_pam        

def profile_clustering(sparse_data, labeler):
    # better way to do this with bitcounts
    cluster_counts = []
    for label_ in range(max(labeler.labels_)+1):
        count = np.sum(labeler.labels_==label_)
        #print(f"label {label_} has count {count}")
        cluster_counts.append(count)
        #print(f"row {row} has label {label}")
    res = {}
    res['cluster_counts'] = cluster_counts
    res['score'] = labeler.score(sparse_data)
    res['inertia_'] = labeler.inertia_
    labels = labeler.labels_
    centroids = labeler.cluster_centers_
    res['ch_score'] = sparse_calinski_harabasz(sparse_data, labels, centroids)
    res['db_score'] = sparse_davies_bouldin(sparse_data, labels, centroids)
    return res

def run_clustering(csr_pam):
    res_dict = {}
    param_dict = {}
    for K in list(range(3,10))+[12]:
        print(f"K = {K}")
        labeler = KMeans(n_clusters=K)
        labeler.fit(csr_pam) 
        param_dict[K] = labeler.get_params()
        res = profile_clustering(csr_pam, labeler)
        res_dict[K] = res
    return res_dict, param_dict
    
def save_dict(dict_, ofname):
    with open(ofname, 'wb') as pklfile:
        # dump information to that file
        pickle.dump(dict_, pklfile)

    
def main(ifname):
    csr_pam = load_data(ifname)
    timestr = time.strftime("%Y%m%d-%H%M%S")
    res_dict, param_dict = run_clustering(csr_pam)    
    save_dict(res_dict, f'cluster_recipes_results_{timestr}.pkl')
    save_dict(param_dict, f'cluster_recipes_params_{timestr}.pkl')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
                    description = 'Cluster recipes based on ingredietn sets')
    parser.add_argument('ifname')
    parser.add_argument('-c', '--count')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    main(args.ifname)
