def preprocess(data):
    """
    Preprocess the data to create two lists:
    - endpoint_video: a list where each index corresponds to an endpoint and contains a list of video IDs 
    requested by that endpoint.
    - cacheData: a list where each index corresponds to a cache and contains a list of tuples 
    (endpoint_id, gain) sorted by gain in descending order.
    """

    endpoint_video = [[] for _ in range(data["N_endpoint"])]
    for request in data["requests"]:
        vid_id, endpoint_id, num_requests = request
        endpoint_video[endpoint_id].append(vid_id)

    
    cacheData=[[] for _ in range(data["N_cache"])]
    for endpoint_id in range (data["N_endpoint"]):
        latency,linked_caches=data["endpoints"][endpoint_id]
        for cache_id, cache_latency in linked_caches:
            gain=latency-cache_latency
            cacheData[cache_id].append((endpoint_id, gain))
    for cache_id in range (data["N_cache"]):
        cacheData[cache_id].sort(key=lambda x: x[1], reverse=True)
    
    
    return endpoint_video, cacheData

def greedy3(data,caches,caches_sizes):
    requests = data["requests"]
    N_requests = data["N_requests"]
    N_caches = data["N_cache"]
    videoSizes = data["video_sizes"]
    endpointData = data["endpoints"]
    #boucle sur les caches
    endpoint_video, cacheData=preprocess(data)
    for cache_id in range(N_caches):
        
        for endpoint_id, gain in cacheData[cache_id]:
            for vid_id in endpoint_video[endpoint_id]:
                if videoSizes[vid_id]<=caches_sizes[cache_id] and vid_id not in caches[cache_id]:
                    caches[cache_id].append(vid_id)
                    caches_sizes[cache_id]-=videoSizes[vid_id]
                    break
    return caches
          



        
        
        

