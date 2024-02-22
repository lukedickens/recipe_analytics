import numpy as np

def sparse_calinski_harabasz(
        sparse_data, labels, centroids):
    """
    Calculates calinski_harabasz score but for scipy.sparse.csr matrices
    
    Based on definitions from:
    
    https://fr-m-wikipedia-org.translate.goog/wiki/Indice_de_Calinski-Harabasz?_x_tr_sl=fr&_x_tr_tl=en&_x_tr_hl=en&_x_tr_pto=sc
    
    and
    
    https://www.geeksforgeeks.org/calinski-harabasz-index-cluster-validity-indices-set-3/
    """
    mean = sparse_data.mean(axis=0)
    separation = calinski_harabasz_separation(
            labels, centroids, mean)
    cohesion = sparse_calinski_harabasz_cohesion(
        sparse_data, labels, centroids)
    return separation/cohesion

def sparse_calinski_harabasz_alt(
        sparse_data, labels, centroids):
    mean = sparse_data.mean(axis=0)
    separation = calinski_harabasz_separation(
            labels, centroids, mean)
    cohesion = sparse_calinski_harabasz_cohesion_alt(
        sparse_data, labels, centroids)
    return separation/cohesion

def calinski_harabasz_separation(
        labels, centroids, mean):
    K = centroids.shape[0]
    separation = 0.
    squarednorms = np.linalg.norm(centroids - mean, axis=1)**2
    cluster_counts = np.bincount(labels)
    for k, kth_squarednorm in enumerate(squarednorms):
        #n_k = np.sum(labels==k)
        n_k = cluster_counts[k]
        separation += (n_k * kth_squarednorm)
    separation /= K-1
    return separation

def sparse_calinski_harabasz_cohesion_alt(
        sparse_data, labels, centroids):
    cohesion = 0.
    N = sparse_data.shape[0]
    K = centroids.shape[0]
    for n, data_n in enumerate(sparse_data):
        k = labels[n]
        centroid = centroids[k,:]
        cohesion += np.linalg.norm(data_n-centroid)**2
    cohesion /= N-K
    return cohesion

def sparse_calinski_harabasz_cohesion(
        sparse_data, labels, centroids):
    cohesion = 0.
    N = sparse_data.shape[0]
    K = centroids.shape[0]
    for k in range(K):
        centroid = centroids[k,:]
        W_k = 0.
        for data_k_i in sparse_data[labels==k,:]:
            W_k += np.linalg.norm(data_k_i -centroid)**2
        cohesion += W_k
    cohesion /= N-K
    return cohesion



def sparse_davies_bouldin_S_is(
        sparse_data, labels, centroids, p=2, q=2):
    print(f"labels.shape ={labels.shape}")
    print(f"sparse_data.shape ={sparse_data.shape}")
    K = centroids.shape[0]
    cluster_counts = np.bincount(labels)
    S_is = np.zeros(cluster_counts.shape)
    for k, (count, centroid) in enumerate(zip(cluster_counts, centroids)):
        S_i = 0.
        datapoint_D_istances = np.empty(count)
        for data_k_i in sparse_data[labels==k,:]:
            S_i += np.linalg.norm(data_k_i -centroid, p)**q
        S_i /= count
        S_i = S_i**(1/q)
        S_is[k] = S_i
    return S_is
    
def davies_bouldin_M_ijs(centroids, p=2):
    K = centroids.shape[0]
    M_ijs = np.zeros((K,K))
    for i, centroid_i in enumerate(centroids):
        M_ijs[i,:] = np.linalg.norm(centroids - centroid_i, p, axis=1)
    return M_ijs

def sparse_davies_bouldin_D_is(S_is, M_ijs, K):
    np.seterr(divide='ignore')
    R_ijs = (S_is.reshape((K,1))+S_is.reshape((1,K)))/M_ijs
    np.seterr(divide='warn')
    min_ = np.min(R_ijs)
    for k in range(K):
        R_ijs[k,k] = min_
    return np.max(R_ijs, axis=0)
    
def sparse_davies_bouldin(
        sparse_data, labels, centroids, p=2, q=2):
    """
    Davies Bouldin clustering metric supporting sparse csr_matrix arrays
    Definitionfrom:
    https://en.wikipedia.org/wiki/Davies%E2%80%93Bouldin_index
    
    """
    K = centroids.shape[0]
    S_is = sparse_davies_bouldin_S_is(
            sparse_data, labels, centroids, p, q)
    M_ijs = davies_bouldin_M_ijs(centroids, p)
    D_is = sparse_davies_bouldin_D_is(S_is, M_ijs, K)
    return np.sum(D_is)/K    

def sparse_kmedoids(sparse_data, K, initial_medoids=None, threshold=1, iterations=10):
    """
    Finds K clusters in data using the K-medoids algorithm

    parameters
    ----------
    sparse_data - (NxD) data matrix (sparse array-like)
    K - integer number of clusters to find
    initial_medoids (optional) - K vector of initial medoids, , each is a
        data-point id 0..(N-1)
    threshold (optional) - the threshold magnitude for termination
    iterations (optional) - the maximum number of iterations

    returns
    -------
    medoids - (K) vector of medoids, each is a data-point id 0..(N-1)
    cluster_assignments - a vector of N integers 0..(K-1), one per data-point,
        assigning that data-point to a cluster
    """
    N,D = sparse_data.shape
    if initial_medoids is None:
        medoids = np.random.choice(N, K, replace=False)
    else:
        medoids = initial_medoids
    # initially change must be larger than threshold for algorithm to run 
    # at least one iteration
    change = 2*threshold
    total_loss = np.inf
    iteration = 1
    while change > threshold:
        cluster_assignments = sparse_kmedoids_e_step(sparse_data, medoids)
        medoids, new_total_loss = sparse_kmedoids_m_step(
            sparse_data, K, cluster_assignments)
        change = total_loss - new_total_loss
        total_loss = new_total_loss
        if not iterations is None and iteration >= iterations:
            break
        iteration += 1
    #
    return medoids, cluster_assignments

def sparse_kmedoids_e_step(sparse_data, medoids, metric=None):
    """
    The E step for the K-medoids algorithm

    parameters
    ----------
    sparse_data - (NxD) data matrix (sparse array-like)
    medoids - K vector of medoids, each is a data-point id 0..(N-1)

    returns
    -------
    cluster_assignments - a vector of N integers 0..(K-1), one per data-point,
        assigning that data-point to a cluster
    """
    N, D = sparse_data.shape
    K = medoids.size
    if metric is None:
        metric = lambda x,y: np.sqrt((x-y).power(2).sum(axis=1))
    # medoids references rows of the data matrix
    centers = sparse_data[medoids, :]
    # two lines below don't work as we cannot reshape sparse matrix.
    #distances_to_medoids = metric(sparse_data.reshape((N,1,D)), medoids.reshape(1,K,D))
    #cluster_assignments = np.argmin(distances_to_medoids, axis=1)
    cluster_assignments = np.empty(N, dtype=int)
    for n, x_n in enumerate(sparse_data):
        # I don't know why this works but it tiles the matrix
        # see the following URL for the source:
        # https://stackoverflow.com/questions/25335095/repeat-a-scipy-csr-sparse-matrix-along-axis-0
        x_n_tiled = x_n[np.zeros(K),:]
        distances_to_medoids = metric(x_n_tiled, centers)
        cluster_assignments[n] = np.argmin(distances_to_medoids)
    return cluster_assignments

def sparse_kmedoids_m_step(sparse_data, K, cluster_assignments, metric=None):
    """
    The M step for the K-medoids algorithm

    parameters
    ----------
    datamtx - (NxD) data matrix (array-like)
    K - number of clusters
    cluster_assignments - a vector of N integers 0..(K-1), one per data-point,
        assigning that data-point to a cluster

    returns
    -------
    centres - (KxD) matrix of updated cluster centres
    total_loss - the new total loss of the clustering
    """
    if metric is None:
        metric = lambda x,y: np.sqrt((x-y).power(2).sum(axis=1))
    N, D = sparse_data.shape
    medoids = np.empty(K, dtype=int)
    total_loss = 0.
    for k in range(K):
        cluster_ids = np.where(cluster_assignments == k)[0]
        cluster_k_data = sparse_data[cluster_ids, :]
        N_k = cluster_ids.size
        summed_cluster_distances = np.empty(N_k)
        for i in range(N_k):
            cluster_member_i = sparse_data[cluster_ids[i], :]
            # I don't know why this works but it tiles the row to a matrix
            # see the following URL for the source:
            # https://stackoverflow.com/questions/25335095/repeat-a-scipy-csr-sparse-matrix-along-axis-0
            cluster_member_i_tiled = cluster_member_i[np.zeros(N_k),:]
            summed_cluster_distances[i] = np.sum(metric(cluster_k_data, cluster_member_i_tiled))
        # find cluster position of the most central member
        i_star = np.argmin(summed_cluster_distances)
        # convert to cluster id
        medoids[k] = cluster_ids[i_star]
        # add to total loss
        total_loss += summed_cluster_distances[i_star]
    return medoids, total_loss

def sparse_kmedoids_m_step_alt(sparse_data, K, cluster_assignments, metric=None):
    """
    The M step for the K-medoids algorithm

    parameters
    ----------
    datamtx - (NxD) data matrix (array-like)
    K - number of clusters
    cluster_assignments - a vector of N integers 0..(K-1), one per data-point,
        assigning that data-point to a cluster

    returns
    -------
    centres - (KxD) matrix of updated cluster centres
    total_loss - the new total loss of the clustering
    """
    if metric is None:
        metric = lambda x,y: np.sqrt((x-y).power(2).sum(axis=1))
    N, D = sparse_data.shape
    medoids = np.empty(K, dtype=int)
    total_loss = 0.
    for k in range(K):
        cluster_ids = np.where(cluster_assignments == k)[0]
        cluster_k_data = sparse_data[cluster_ids, :]
        cluster_mean = cluster_k_data.mean(axis=0)
        N_k = cluster_ids.size
        distances = np.linalg.norm(cluster_k_data - cluster_mean.reshape((1,D)), axis=1)
        # find cluster position of the member closest to the mean
        i_star = np.argmin(distances)
        # convert to cluster id
        medoids[k] = cluster_ids[i_star]
        # add to total loss
        total_loss += distances[i_star]
    return medoids, total_loss

def sparse_kmeans_m_step_alt(sparse_data, K, cluster_centres, metric=None):
    """
    The M step for the K-medoids algorithm

    parameters
    ----------
    datamtx - (NxD) data matrix (array-like)
    K - number of clusters
    cluster_assignments - a vector of N integers 0..(K-1), one per data-point,
        assigning that data-point to a cluster

    returns
    -------
    centres - (KxD) matrix of updated cluster centres
    total_loss - the new total loss of the clustering
    """
    if metric is None:
        metric = lambda x,y: np.sqrt((x-y).power(2).sum(axis=1))
    N, D = sparse_data.shape
    medoids = np.empty(K, dtype=int)
    total_loss = 0.
    for k in range(K):
        cluster_ids = np.where(cluster_assignments == k)[0]
        cluster_k_data = sparse_data[cluster_ids, :]
        cluster_mean = cluster_k_data.mean(axis=0)
        N_k = cluster_ids.size
        distances = np.linalg.norm(cluster_k_data - cluster_mean.reshape((1,D)), axis=1)
        # find cluster position of the member closest to the mean
        i_star = np.argmin(distances)
        # convert to cluster id
        medoids[k] = cluster_ids[i_star]
        # add to total loss
        total_loss += distances[i_star]
    return medoids, total_loss

