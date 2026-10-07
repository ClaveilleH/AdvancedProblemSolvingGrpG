#    greedy(N_vid, N_endpoint, N_request, N_cache, caches_sizes, video_sizes, endpoints, requests, caches)
def greedy(data, caches, caches_sizes):
    # tri des requêtes par nombre de requêtes décroissant
    requests = data["requests"]
    N_requests = data["N_requests"]
    N_caches = data["N_cache"]
    videoSizes = data["video_sizes"]
    endpointData = data["endpoints"]

    sorted_requests = sorted(requests,key=lambda x: x[2],reverse=True)
    res=[set() for _ in range(N_caches)]

    for request_id in range(N_requests):
        vid_id, endpoint_id, num_requests = sorted_requests[request_id]
        latency, linked_caches = endpointData[endpoint_id]
        fastest_latency = latency
        fastest_cache = None

        for lc in linked_caches :
            cacheid, cache_latency = lc

            if cache_latency < fastest_latency and caches_sizes[cacheid] >= videoSizes[vid_id]:
                fastest_latency = cache_latency
                fastest_cache = cacheid

        if fastest_cache != None and vid_id not in res[fastest_cache]:
            res[fastest_cache].add(vid_id)
            caches_sizes[fastest_cache] -= videoSizes[vid_id]

    #modifie la liste pour que ca soit compatible avec le reste du code
    # caches = [list(res[i]) for i in range(N_caches)] 
    for i in range(N_caches):
        caches[i] = list(res[i])

    return res
