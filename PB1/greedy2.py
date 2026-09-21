def preprocess_requests(N_vid, N_endpoint, N_requests, N_caches, requests, endpointData):
    """
    On cherche a faire une liste de videos triée par nombre de requêtes
    et pour chaque video une liste de caches accessible triée par nombre de fois accessible selon les endpoints qui la demandent
    """
    videos_list = set()
    video_request_count = [0] * N_vid
    video_endpoint = [[] for _ in range(N_vid)]
    for video_id, endpoint_id, num_requests in requests:
        videos_list.add(video_id)
        video_request_count[video_id] += num_requests
        video_endpoint[video_id].append(endpoint_id)

    # print(f"Nombre de videos non utilisées : {N_vid - len(videos_list)}")
    

    # videos_caches = [{} for _ in range(N_vid)]
    videos_caches = [[] for _ in range(N_vid)]
    caches_list = set()
    #lister les caches pour chaque video
    for video_id in list(videos_list):
        caches_accessible = []
        for endpoint_id in video_endpoint[video_id]:
            _, linked_caches = endpointData[endpoint_id]
            for cache_id, _ in linked_caches:
                caches_accessible.append(cache_id)
        dico = {}
        for cache_id in caches_accessible:
            caches_list.add(cache_id)
            if cache_id not in dico:
                dico[cache_id] = 1
            else:
                dico[cache_id] += 1
        # videos_caches[video_id] = dico
        videos_caches[video_id] = list(dico.items())
        videos_caches[video_id].sort(key=lambda x: x[1], reverse=True)  # Sort by number of requests descending

    # print(videos_caches[1])
    # print(f"Nombre de caches non utilisés : {N_caches - len(caches_list)}")

    video_list_sorted = sorted(list(videos_list), key=lambda x: video_request_count[x], reverse=True)
    print(f"---> {N_vid - len(video_list_sorted)} videos unused, {N_caches - len(caches_list)} caches unlinked")
    return video_list_sorted, videos_caches, caches_list


def greedy2(data, caches, caches_sizes):
    """
    Idée : on tr
    """
    videoSizes = data["video_sizes"]
    N_vid = data["N_vid"]
    N_endpoint = data["N_endpoint"]
    N_requests = data["N_requests"]
    N_caches = data["N_cache"]
    requests = data["requests"]
    endpointData = data["endpoints"]
    
    smallest_video_size = min(videoSizes)
    video_list_sorted, videos_caches, caches_list = preprocess_requests(N_vid, N_endpoint, N_requests, N_caches, requests, endpointData)

    i = 0
    while i < len(video_list_sorted) and caches_list:
        video_id = video_list_sorted[i]
        j = 0
        while j < len(videos_caches[video_id]) and caches_list: # caches_list pas nécessaire
            cache_id, _ = videos_caches[video_id][j]
            if cache_id in caches_list and videoSizes[video_id] <= caches_sizes[cache_id]:
                caches[cache_id].append(video_id)
                caches_sizes[cache_id] -= videoSizes[video_id]
                if caches_sizes[cache_id] < smallest_video_size:
                    caches_list.remove(cache_id)
                break  # Move to the next video after placing it in a cache
            j += 1
        i += 1
