from math import gcd
from functools import reduce


def make_adj_list(N_vid, N_requests, requests):
    """
    return a list of list where res[i] coresponds to the list of index of 
    the requests that asked for video i 
    """
    res = [[] for _ in range(N_vid)]

    for j in range(N_requests):
        vid_id, _, _ = requests[j]
        res[vid_id].append(j)

    return res


def knapsack_value(values, weights, W):
    INF = float('inf')
    n= len(values)
    if n == 0 or W == 0:
            return 0, set()
    opt=[[INF]*(sum(values)+1) for _ in range(n+1)]
    for i in range(n + 1):
        opt[i][0] = 0
    borne=0
    for i in range(1, n + 1):
        vi, wi = values[i-1], weights[i-1]
        borne_prev=borne
        borne+=vi
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

def knapsack_weight(values, weights, W):
    n = len(values)
    if n == 0 or W == 0:
        return 0, set()
    opt = [[0] * (W + 1) for _ in range(n + 1)]   

    for i in range(1, n + 1):
        vi, wi = values[i-1], weights[i-1]
        for w in range(W + 1):
            opt[i][w] = opt[i-1][w]                     
            if w >= wi:
                opt[i][w] = max(opt[i][w], vi + opt[i-1][w - wi])   

    bag = set()
    score = opt[n][W]
    w = W
    for i in range(n, 0, -1):
        if opt[i][w] != opt[i-1][w]:
            bag.add(i - 1)
            w -= weights[i-1]

    return score, bag

def multiknapsack(data,caches,caches_sizes):
    weight, gcd_weight = preprocess_weight_genius(data)
    values = preprocess_values_genius(data)
    for cache_id in range(data["N_cache"]):
        capacity = caches_sizes[cache_id] // gcd_weight
        if sum(values[cache_id])>capacity:
            print("knapsack weight")

            score, bag = knapsack_weight(values[cache_id], weight, capacity)
            caches[cache_id] = bag
        else:
            print("knapsack value")
            score, bag = knapsack_value(values[cache_id], weight, capacity)
            caches[cache_id] = bag

    
        
def useless_object(weights,values,capacity):
    n = len(values)
    res=set()
    for i in range(n):
        if weights[i]>capacity or values[i]==0:
            res.add(i)
    return res

    

def preprocess_weight_genius(data):
    weights=data["video_sizes"]
    gcd_weight=reduce(gcd, weights,0) or 1 
    if gcd_weight>1:
        weights=[w//gcd_weight for w in weights]

    return weights,gcd_weight


def preprocess_values_genius(data):
        values=[[0]*data["N_vid"] for _ in range(data["N_cache"])]
        for request in data["requests"]:
            vid_id, endpoint_id, num_request= request
            latency, linked_caches = data["endpoints"][endpoint_id]
            for cache_id, cache_latency in linked_caches:
                gain = latency - cache_latency
                if gain>0:
                    values[cache_id][vid_id]+=(gain*num_request)
        for cache_id in range(data["N_cache"]):
            gcd_value=reduce(gcd, values[cache_id],0) or 1
            if gcd_value>1:
                values[cache_id]=[v//gcd_value for v in values[cache_id]]

        return values



