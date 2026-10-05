LIMIT = 10000000

def knapsack_crespelle(values, weights, W):
    INF = float('inf')
    n= len(values)
    
    opt=[[INF]*(sum(values)+1) for _ in range(n+1)]
    for i in range(n + 1):
        opt[i][0] = 0
    
    for i in range(1, n + 1):
        vi, wi = values[i-1], weights[i-1]
        borne= sum(values[:i])
        borne_prev= sum(values[:i-1])

        for V in range(1,borne+1):
            if V>borne_prev:
                opt[i][V]=wi+opt[i-1][max(0, V - vi)]
            else:
                opt[i][V] = min(opt[i-1][V], wi + opt[i-1][max(0, V - vi)])

    bag=set()
    score = max(V for V in range(borne + 1) if opt[n][V] <= W)
    V=score
    for i in range(n, 0, -1):
        if opt[i][V] != opt[i-1][V]:            
            bag.add(i - 1)                     
            V = max(0, V - values[i-1])

    return score,bag 

def preprocess_values(data):
    values=[[0]*data["N_vid"] for _ in range(data["N_cache"])]
    Vmax=0
    for request in data["requests"]:
        vid_id, endpoint_id, num_request= request
        latency, linked_caches = data["endpoints"][endpoint_id]
        for cache_id, cache_latency in linked_caches:
            gain = latency - cache_latency
            values[cache_id][vid_id]+=(gain*num_request)
            Vmax = max(Vmax, values[cache_id][vid_id])
    return values,Vmax



def preprocess_values_nul(data):
    values=[[0]*data["N_vid"] for _ in range(data["N_cache"])]
    Vmax=0
    for request in data["requests"]:
        vid_id, endpoint_id, _= request
        latency, linked_caches = data["endpoints"][endpoint_id]
        for cache_id, cache_latency in linked_caches:
            gain = latency - cache_latency
            values[cache_id][vid_id]+=(gain)
            Vmax = max(Vmax, values[cache_id][vid_id])
    return values,Vmax


def multi_knapsack(data,caches,caches_sizes):
    weights=data["video_sizes"]
    values,Vmax=preprocess_values(data)
    if Vmax>LIMIT:
        print(f"greater value bigger than limit : {LIMIT} the exact algo is too long ")
        return multi_knapsack_nul(data,caches,caches_sizes)
    for cache_id in range(data["N_cache"]):
        capacity=caches_sizes[cache_id]
        scores,bag=knapsack_crespelle(values[cache_id],weights,capacity)
        caches[cache_id]=bag
        caches_sizes[cache_id]-=sum(weights[i] for i in bag)


def multi_knapsack_nul(data,caches,caches_sizes):
    weights=data["video_sizes"]
    values,Vmax=preprocess_values_nul(data)
    if Vmax>LIMIT:
        print(f"greater value bigger than limit : {LIMIT} the exact algo is too long ")
        return multi_knapsack_nul(data,caches,caches_sizes)
    for cache_id in range(data["N_cache"]):
        capacity=caches_sizes[cache_id]
        scores,bag=knapsack_crespelle(values[cache_id],weights,capacity)
        caches[cache_id]=bag
        caches_sizes[cache_id]-=sum(weights[i] for i in bag)