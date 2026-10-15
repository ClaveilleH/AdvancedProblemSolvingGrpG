import sys
import algos.knapsack_slay as K
from utils import read_input_file, make_adj_list, compute_score
N_vid, N_e, N_r, N_c, S, sizes, eps, ce, reqs = read_input_file(sys.argv[1])
data = dict(N_vid=N_vid, N_endpoint=N_e, N_request=N_r, N_requests=N_r, N_cache=N_c, S_cache=S, cache_size=S,
            video_sizes=sizes, endpoints=eps, caches_endpoints=ce, requests=reqs, adj_list=make_adj_list(N_vid, N_r, reqs))
for label, limit in [("knapsack (DP exacte, PGCD)", K.LIMIT), ("tri par valeur + glouton", 0)]:
    K.LIMIT = limit
    caches = [[] for _ in range(N_c)]; cs = [S] * N_c
    K.multiknapsack_bg(data, caches, cs)
    print(f"  {label:30s} {compute_score(caches, eps, reqs)}")
