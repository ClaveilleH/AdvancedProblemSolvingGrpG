from math import gcd
from functools import reduce
LIMIT = 1000




def knapsack_value(values, weights, W):
    if sum(values)> LIMIT:
        return 0,set()
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
    if W > LIMIT:
        return  0,set()
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
    values,gcd_values = preprocess_values_genius(data)
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

def multiknapsack_bg(data,caches,caches_sizes):
    endpoints = data["endpoints"]
    requests = data["requests"]
    weight,gcd_weight = preprocess_weight_genius(data)
    values,gcd_values= preprocess_values_genius(data)
    adj_list = data["adj_list"]
    order_treatment=sorted(range(data["N_cache"]), key=lambda x: sum(values[x]), reverse=True)
    for cache_id in order_treatment:
        capacity = caches_sizes[cache_id] // gcd_weight
        if sum(values[cache_id])>capacity:
            score, bag = knapsack_weight(values[cache_id], weight, capacity)
            caches[cache_id] = bag
        else:
            score, bag = knapsack_value(values[cache_id], weight, capacity)
            caches[cache_id] = bag

        for vid_id in bag:
            for request_id in adj_list[vid_id]:
                _, endpoint_id, num_requests = requests[request_id]
                endpoint_latency, linked_caches = endpoints[endpoint_id]

                # latence entre cet endpoint et le cache qu'on vient de remplir
                cache_latency = dict(linked_caches).get(cache_id)
                if cache_latency is None:      # endpoint non relié à ce cache : rien à mettre à jour
                    continue

                for cache_id2, latency2 in linked_caches:
                    if cache_id2 == cache_id:
                        continue
                    # gain qu'avait cache2 pour cette requête, moins le gain qui lui reste
                    # maintenant que cache_id sert déjà la vidéo
                    perte = max(0, endpoint_latency - latency2) - max(0, cache_latency - latency2)
                    if perte > 0:
                        values[cache_id2][vid_id] = max(
                            0,
                            values[cache_id2][vid_id] - (perte * num_requests) // gcd_values[cache_id2]
                        )


        
        
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
        gcd_values=[]
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
            gcd_values.append(gcd_value)

        return values,gcd_values



