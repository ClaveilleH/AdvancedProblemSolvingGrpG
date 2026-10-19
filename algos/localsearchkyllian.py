def calculgainmarignal(data,cache,video,solution):
    requests = data["requests"]
    caches_endpoints = data["caches_endpoints"]
    adj_list = data["adj_list"]

    total_gain = 0

    for request_id in adj_list[video]:
        _, endpoint_id, num_requests = requests[request_id]
        data_center_latency, linked_caches = data["endpoints"][endpoint_id]
        # On verifie que le endpoint est relier au cache 
        latence_cache = caches_endpoints[cache].get(endpoint_id)
        if latence_cache is None:
            continue
        # On cherche les caches en dehors du cache en argument qui sont relier au endpoint_id et qui contienne la vidéo (on garde la latence minimum)
        latence_autre = data_center_latency
        for cache_id, cache_latency in linked_caches:
            if cache_id != cache and video in solution[cache_id]:
                latence_autre = min(latence_autre, cache_latency)

        # On calcule le gain donc la (latence_autre - latence_cache) * nombre de fois que la video est demander dans endpoint_id
        # Si latence autre est mieux on met gain = 0 
        total_gain += max(0,latence_autre-latence_cache)*num_requests

    return total_gain

def ajout(data,solution,list_capacity_left):
    video_sizes = data["video_sizes"]
    for cache_id, cache in enumerate(solution):
        for video_id, size in enumerate(video_sizes):
            if (list_capacity_left[cache_id] >= size) and (video_id not in cache ):
                if calculgainmarignal(data,cache_id,video_id,solution) > 0:
                    solution[cache_id].add(video_id)
                    list_capacity_left[cache_id] -= size
    return solution

def retrait(data,solution,list_capacity_left):
    video_sizes = data["video_sizes"]
    for cache_id, cache in enumerate(solution):
        for video_id in list(cache):
            if calculgainmarignal(data,cache_id,video_id,solution) == 0:
                cache.remove(video_id)
                list_capacity_left[cache_id] += video_sizes[video_id]
    return solution

def echange(data,solution,list_capacity_left):
    video_sizes = data["video_sizes"]
    for cache_id,cache in enumerate(solution):
        for video_id_now in list(cache):
            gain_now = calculgainmarignal(data,cache_id,video_id_now,solution)
            for video_id, size in enumerate(video_sizes):

                if video_id in cache :
                    continue

                if list_capacity_left[cache_id] + video_sizes[video_id_now] < size:
                    continue

                if gain_now < calculgainmarignal(data,cache_id,video_id,solution):
                    cache.remove(video_id_now)
                    cache.add(video_id)
                    list_capacity_left[cache_id] = list_capacity_left[cache_id] + video_sizes[video_id_now] - size
                    break
    return solution 
    
def calculcapacitysolution(data,solution):
    cache_capacity = data["S_cache"]
    video_sizes = data["video_sizes"]
    list_capacity = []
    for cache in solution:
        capacity = 0
        for video_id in cache:
            capacity += video_sizes[video_id]
        list_capacity.append(cache_capacity-capacity)
    return list_capacity            
        
import time

def ma_recherche_locale(data, caches, sizes, time_limit=120, max_tours=70):
    debut = time.time()
    place = calculcapacitysolution(data, caches)     

    for _ in range(max_tours):
        if time.time() - debut > time_limit:
            break
        avant = [frozenset(cache) for cache in caches]      

        retrait(data, caches, place)                
        ajout(data, caches, place)                   
        echange(data, caches, place)   

        if [frozenset(cache) for cache in caches] == avant:  
            break

    for cache in range(len(caches)):
        sizes[cache] = place[cache]