import numpy as np
import scipy.sparse

def generate_csr_matrix(N=10, D=30,density=0.1, fragile=True, col_density=None):
    """
    Generates a sparse csr binary matrix of size NxD with approximately
    density*N*D non-zero elements.
    
    If col_density is specified then only round(col_density*D) columns
    will contain non-zero elements.
    """
    K = 20
    lil_data = scipy.sparse.lil_array((N,D), dtype=int)
    expected_cols = density*D
    per_row_avg = round(expected_cols)
    if col_density is None:
        col_choice = D
        num_cols_chosen = D
    elif col_density >= density:
        col_choice = np.random.choice(D, size=round(col_density*D), replace=False)
        num_cols_chosen = col_choice.size
    else:
        raise ValueError(f"col_density ({col_density}) cannot be less than density ({density})")
    condensed_density = expected_cols/num_cols_chosen
    for i in range(N):
        try:
            #non_zeros = np.random.poisson(per_row_avg-1)+1
            non_zeros = np.random.binomial(num_cols_chosen, condensed_density)
        except:
            if fragile:
                raise
            else:
                non_zeros = 1
        js = np.random.choice(col_choice, size=non_zeros, replace=False)
        lil_data[i,js] = 1
    return scipy.sparse.csr_matrix(lil_data.tocsr())

def generate_sparse_cluster_data(
        Ns, D=30, density=0.1, col_density=None, fragile=True,
        randomise_rows=True):
    """
    Synthetically generates simple binary data from different clusters
    Ns - a list/array of numbers of a given cluster one per cluster
        len(Ns) is number of clusters
    D - number of columns in resulting matrix
    col_density - is the number of non-zero columns in each cluster.
     
    """
    sub_matrices = []
    Ntot = np.sum(Ns)
    cluster_ids = np.zeros(Ntot)
    min_index = 0
    for i, N in enumerate(Ns):
        max_index = min_index+N
        cluster_ids[min_index:max_index] = i
        min_index = max_index
        sub_matrices.append(generate_csr_matrix(
            N=N, D=D, density=density, fragile=fragile, col_density=col_density))
    data = scipy.sparse.vstack(sub_matrices)
    if randomise_rows:
        reorder = np.arange(Ntot)
        np.random.shuffle(reorder)
        print(f"reorder = {reorder}")
        data = data[reorder,:]
        cluster_ids = cluster_ids[reorder]
    return data, cluster_ids
    
