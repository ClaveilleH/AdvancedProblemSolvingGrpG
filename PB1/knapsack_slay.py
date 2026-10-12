from math import gcd
from functools import reduce
LIMIT = 100000000



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

def knapsack_goulton(values, weights, W):
    
    order = sorted(range(len(values)), key=lambda i: values[i] / weights[i], reverse=True)
    bag = set()
    total_weight = 0
    total_value = 0
    for i in order:
        if total_weight + weights[i] <= W:
            bag.add(i)
            total_weight += weights[i]
            total_value += values[i]
    return total_value, bag


def multiknapsack_bg(data,caches,caches_sizes):



    endpoints = data["endpoints"]
    requests = data["requests"]
    weight = data["video_sizes"]
    caches_endpoints = data["caches_endpoints"]



   
    best = {}   # (endpoint_id, vid_id) -> meilleure latence actuelle



    values= preprocess_values_genius(data)
    adj_list = data["adj_list"]
    remaining=set(range(data["N_cache"]))
    while remaining:
        cache_id=max(remaining,key=lambda c: sum(values[c])/sum(weight)     )
        remaining.discard(cache_id)
       
        capacity = caches_sizes[cache_id] 
        objects=[i for i in range(data["N_vid"]) if values[cache_id][i]>0 and weight[i]<=capacity]
        

        sub_values=[values[cache_id][i] for i in objects]
        sub_weight=[weight[i] for i in objects]

        gcd_values = reduce(gcd, sub_values,0) or 1
        sub_values_reduced = [v // gcd_values for v in sub_values]
        gcd_weights = reduce(gcd, sub_weight,0) or 1
        sub_weight_reduced = [w // gcd_weights for w in sub_weight]
        capacity_reduced = capacity // gcd_weights



        sumsubvalues=sum(sub_values_reduced)
        n=len(objects)


        if sumsubvalues*n>LIMIT and capacity_reduced*n>LIMIT:
            score,bag=knapsack_goulton(sub_values_reduced,sub_weight_reduced,capacity_reduced)
            
        elif sumsubvalues > capacity_reduced:
            score, bag = knapsack_weight(sub_values_reduced, sub_weight_reduced, capacity_reduced)
           
        else:
            score, bag = knapsack_value(sub_values_reduced, sub_weight_reduced, capacity_reduced)

        bag={objects[i] for i in bag}
        caches[cache_id]=bag


        for vid_id in bag:
                for request_id in adj_list[vid_id]:
                    _, endpoint_id, num_requests = requests[request_id]
                    endpoint_latency, linked_caches = endpoints[endpoint_id]

                    # latence de cet endpoint vers le cache qu'on vient de remplir
                    cache_latency = caches_endpoints[cache_id].get(endpoint_id)
                    if cache_latency is None:        # endpoint non relié à ce cache
                        continue

                    key = (endpoint_id, vid_id)
                    old = best.get(key, endpoint_latency)   # meilleure latence avant ce cache
                    new = min(old, cache_latency)           # meilleure latence après
                    if new == old:                          # ce cache n'améliore rien
                        continue
                    best[key] = new

                    for cache_id2, latency2 in linked_caches:
                        if cache_id2 in remaining:          # seulement les caches pas encore remplis
                            # gain marginal de cache2 avant, moins gain marginal après
                            perte = max(0, old - latency2) - max(0, new - latency2)
                            if perte > 0:
                                values[cache_id2][vid_id] -= perte * num_requests

        
        


  

def preprocess_values_genius(data):
        values=[[0]*data["N_vid"] for _ in range(data["N_cache"])]
        for request in data["requests"]:
            vid_id, endpoint_id, num_request= request
            latency, linked_caches = data["endpoints"][endpoint_id]
            for cache_id, cache_latency in linked_caches:
                gain = latency - cache_latency
                if gain>0:
                    values[cache_id][vid_id]+=(gain*num_request)
       

        return values


