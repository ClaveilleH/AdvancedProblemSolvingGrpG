from math import gcd
from functools import reduce
LIMIT = 10000




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

def multiknapsack(data,caches,caches_sizes):
    weight, gcd_weight = preprocess_weight_genius(data)
    values,gcd_values = preprocess_values_genius(data)
    for cache_id in range(data["N_cache"]):
        capacity = caches_sizes[cache_id] // gcd_weight
        sumvalue=sum(values[cache_id])
        
        if sumvalue>LIMIT and capacity>LIMIT:
            return 0,set()
        
        elif sumvalue>capacity:

            score, bag = knapsack_weight(values[cache_id], weight, capacity)
            caches[cache_id] = bag
        else:
            score, bag = knapsack_value(values[cache_id], weight, capacity)
            caches[cache_id] = bag

def multiknapsack_bg(data,caches,caches_sizes):
    endpoints = data["endpoints"]
    requests = data["requests"]
    weight,gcd_weight = preprocess_weight_genius(data)
    values,gcd_values= preprocess_values_genius(data)
    adj_list = data["adj_list"]
    remaining=set(range(data["N_cache"]))
    while remaining:
        cache_id=max(remaining,key=lambda c: sum(values[c])*gcd_values[c])
        remaining.discard(cache_id)
        capacity = caches_sizes[cache_id] // gcd_weight
        objects=[i for i in range(data["N_vid"]) if values[cache_id][i]>0 and weight[i]<=capacity]
        sub_values=[values[cache_id][i] for i in objects]
        sub_weight=[weight[i] for i in objects]
        sumsubvalues=sum(sub_values)
        if sumsubvalues>LIMIT and capacity>LIMIT:
            score,bag=knapsack_goulton(sub_values,sub_weight,capacity)
            
        elif sumsubvalues > capacity:
            score, bag = knapsack_weight(sub_values, sub_weight, capacity)
           
        else:
            score, bag = knapsack_value(sub_values, sub_weight, capacity)

        bag={objects[i] for i in bag}
        caches[cache_id]=bag
           
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
      

        return values



