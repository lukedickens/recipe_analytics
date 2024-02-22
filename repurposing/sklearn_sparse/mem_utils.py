"""
Utilities to investigate the memory footprint of arrays
"""

def get_nparray_memory_usage(array):
    BYTES_TO_MB_DIV = 0.000001
    return array.nbytes*BYTES_TO_MB_DIV

def get_csr_memory_usage(X_csr):
    BYTES_TO_MB_DIV = 0.000001
    mem = get_nparray_memory_usage(X_csr.data) \
        + get_nparray_memory_usage(X_csr.indptr) \
        + get_nparray_memory_usage(X_csr.indices)
    return mem
