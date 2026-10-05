def knapsack(values, weights, capacity):
    n = len(values)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        w, v = weights[i - 1], values[i - 1]
        for c in range(capacity + 1):
            dp[i][c] = dp[i - 1][c]
            if w <= c and dp[i - 1][c - w] + v > dp[i][c]:
                dp[i][c] = dp[i - 1][c - w] + v

    alloc, c = set(), capacity
    for i in range(n, 0, -1):
        if dp[i][c] != dp[i - 1][c]:
            alloc.add(i - 1)
            c -= weights[i - 1]

    return dp[n][capacity], alloc

def preprocess_values(data):
    values=[[0]*data["N_vid"] for _ in range(data["N_cache"])]
    for request in data["requests"]:
        vid_id, endpoint_id, num_requests = request
        latency, linked_caches = data["endpoints"][endpoint_id]
        for cache_id, cache_latency in linked_caches:
            gain = latency - cache_latency
            values[cache_id][vid_id]+=(gain * num_requests)
    return values



def multi_knapsack(Data,caches,caches_sizes):
    weights=Data["video_sizes"]
    values=preprocess_values(Data)
    for cache_id in range(Data["N_cache"]):
        capacity=caches_sizes[cache_id]
        scores,alloc=knapsack(values[cache_id],weights,capacity)
        caches[cache_id]=alloc
        caches_sizes[cache_id]-=sum(weights[i] for i in alloc)