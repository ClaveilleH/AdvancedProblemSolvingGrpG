import random
from utils import calculate_video_latency, compute_cost
#! ATTENTION : supprimer l'utilisation de compute_cost dans local_search

    # random_tabu_search(data, caches, caches_sizes, nb_forbiden_moves, iteration , nbCaches, nbVideos)

def random_tabu_search(data, caches, caches_sizes, nb_forbidden_moves, iteration=10, nb_caches=None, nb_videos=None):
    N_vid = data["N_vid"]
    N_endpoint = data["N_endpoint"]
    N_requests = data["N_requests"]
    N_caches = data["N_cache"]
    video_sizes = data["video_sizes"]
    endpoint_data = data["endpoints"]
    requests = data["requests"]
    adj_list = data["adj_list"]
    if nb_caches is None or nb_caches > N_caches:
        nb_caches = N_caches
    if nb_videos is None or nb_videos > N_vid:
        nb_videos = N_vid
    if nb_forbidden_moves <= 0:
        nb_forbidden_moves = 1
    forbidden_moves = [None] * nb_forbidden_moves
    best_caches = [c.copy() for c in caches]
    current_total_delta = 0
    best_total_delta = 0

    for iter_step in range(iteration):
        best_delta = float('inf')
        best_move = None

        for cache_id in random.sample(range(N_caches), nb_caches):
            cache = caches[cache_id]
            for video_id in random.sample(range(N_vid), nb_videos):
                current_vid_latency = calculate_video_latency(  adj_list, caches, video_id, N_vid, N_endpoint, N_requests, N_caches, caches_sizes, video_sizes, endpoint_data, requests)     

                if video_id in cache and (cache_id, video_id, 1) not in forbidden_moves:
                    cache.remove(video_id)
                    new_video_latency = calculate_video_latency(     adj_list, caches, video_id, N_vid, N_endpoint, N_requests, N_caches, caches_sizes, video_sizes, endpoint_data, requests  )
                    current_delta = new_video_latency - current_vid_latency
                    move = (cache_id, video_id, 0)
                    cache.add(video_id) 

                elif (video_id not in cache   and caches_sizes[cache_id] >= video_sizes[video_id]      and (cache_id, video_id, 0) not in forbidden_moves):
                    cache.add(video_id)
                    new_video_latency = calculate_video_latency( adj_list, caches, video_id, N_vid, N_endpoint, N_requests, N_caches, caches_sizes, video_sizes, endpoint_data, requests   )
                    current_delta = new_video_latency - current_vid_latency
                    move = (cache_id, video_id, 1)
                    cache.remove(video_id)  

                else:
                    continue

                if current_delta < best_delta:
                    best_delta = current_delta
                    best_move = move

        if best_move is None:
            break

        move_cache_id, move_video_id, action = best_move
        if action == 0:
            caches[move_cache_id].remove(move_video_id)
            caches_sizes[move_cache_id] += video_sizes[move_video_id]
        else:
            caches[move_cache_id].add(move_video_id)
            caches_sizes[move_cache_id] -= video_sizes[move_video_id]

        forbidden_moves[iter_step % nb_forbidden_moves] = (  move_cache_id, move_video_id, (action + 1) % 2      )
        current_total_delta += best_delta

        if current_total_delta < best_total_delta:
            best_total_delta = current_total_delta
            best_caches = [c.copy() for c in caches]

    return best_caches                


def sort_vid(N_vid, N_requests, requests, videoSizes):
    count=[0]*N_vid
    for i in range(N_requests):
        video_id, endpoint_id, num_requests = requests[i]
        count[video_id]+=num_requests
    weights=[(count[i]*videoSizes[i] ,i)for i in range(N_vid)]
    weights.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in weights]

def sorted_tabu_search(data, caches, caches_sizes, nb_forbidden_moves, iteration=10, nb_caches=None, nb_videos=None):
    N_vid = data["N_vid"]
    N_endpoint = data["N_endpoint"]
    N_requests = data["N_requests"]
    N_caches = data["N_cache"]
    video_sizes = data["video_sizes"]
    endpoint_data = data["endpoints"]
    requests = data["requests"]
    adj_list = data["adj_list"]
    
    if nb_caches is None or nb_caches > N_caches:
        nb_caches = N_caches
    if nb_videos is None or nb_videos > N_vid:
        nb_videos = N_vid
    if nb_forbidden_moves <= 0:
        nb_forbidden_moves = 1
    sorted_vid= sort_vid(N_vid, N_requests, requests, video_sizes)
    forbidden_moves = [None] * nb_forbidden_moves
    best_caches = [c.copy() for c in caches]
    current_total_delta = 0
    best_total_delta = 0

    for iter_step in range(iteration):
        best_delta = float('inf')
        best_move = None

        for cache_id in range((nb_caches)):
            cache = caches[cache_id]
            for i in (range(nb_videos)):
                video_id=sorted_vid[i]
                current_vid_latency = calculate_video_latency(  adj_list, caches, video_id, N_vid, N_endpoint, N_requests, N_caches, caches_sizes, video_sizes, endpoint_data, requests)     

                if video_id in cache and (cache_id, video_id, 1) not in forbidden_moves:
                    cache.remove(video_id)
                    new_video_latency = calculate_video_latency(     adj_list, caches, video_id, N_vid, N_endpoint, N_requests, N_caches, caches_sizes, video_sizes, endpoint_data, requests  )
                    current_delta = new_video_latency - current_vid_latency
                    move = (cache_id, video_id, 0)
                    cache.add(video_id) 

                elif (video_id not in cache   and caches_sizes[cache_id] >= video_sizes[video_id]      and (cache_id, video_id, 0) not in forbidden_moves):
                    cache.add(video_id)
                    new_video_latency = calculate_video_latency( adj_list, caches, video_id, N_vid, N_endpoint, N_requests, N_caches, caches_sizes, video_sizes, endpoint_data, requests   )
                    current_delta = new_video_latency - current_vid_latency
                    move = (cache_id, video_id, 1)
                    cache.remove(video_id)  

                else:
                    continue

                if current_delta < best_delta:
                    best_delta = current_delta
                    best_move = move

        if best_move is None:
            break

        move_cache_id, move_video_id, action = best_move
        if action == 0:
            caches[move_cache_id].remove(move_video_id)
            caches_sizes[move_cache_id] += video_sizes[move_video_id]
        else:
            caches[move_cache_id].add(move_video_id)
            caches_sizes[move_cache_id] -= video_sizes[move_video_id]

        forbidden_moves[iter_step % nb_forbidden_moves] = (  move_cache_id, move_video_id, (action + 1) % 2      )
        current_total_delta += best_delta

        if current_total_delta < best_total_delta:
            best_total_delta = current_total_delta
            best_caches = [c.copy() for c in caches]

    return best_caches    

# ######################################## LOCAL SEARCH ########################################

def local_search(data, caches, caches_sizes, iteration=10, previous_moves=None, nbCaches=None, nbVideos=None, supp = False):
    N_vid = data["N_vid"]
    N_endpoint = data["N_endpoint"]
    N_requests = data["N_requests"]
    N_caches = data["N_cache"]
    videoSizes = data["video_sizes"]
    endpointData = data["endpoints"]
    requests = data["requests"]
    adj_list = data["adj_list"]

    if iteration == 0:
        return caches, caches_sizes
    if nbCaches is None or nbCaches > N_caches:
        nbCaches = N_caches
    if nbVideos is None or nbVideos > N_vid:
        nbVideos = N_vid
    if iteration == 0:
        return caches, caches_sizes

    # print(f"previous_moves={previous_moves}")

    # print(f"Testing local search iteration {iteration} with {nbCaches}/{N_caches} caches and {nbVideos}/{N_vid} videos")
    # base_cost = compute_cost(caches, endpointData, requests)
    neighbors = []  # (cost, caches, caches_sizes, move)
    cost = compute_cost(caches, endpointData, requests)
    # ajouts
    for cache_id in range(nbCaches):
        cache = caches[cache_id]
        for video in range(nbVideos):
            # print(f"Checking video {videoId} for cache {cache_id}")
            if video in cache:
                continue
            if videoSizes[video] <= caches_sizes[caches.index(cache)]:
                previous_cost = calculate_video_latency(adj_list, caches, video, N_vid, N_endpoint, N_requests, N_caches, caches_sizes, videoSizes, endpointData, requests)
                caches[cache_id].append(video)
                new_cost = calculate_video_latency(adj_list, caches, video, N_vid, N_endpoint, N_requests, N_caches, caches_sizes, videoSizes, endpointData, requests)
                delta = new_cost - previous_cost

                caches[cache_id].remove(video)
                move = (1, cache_id, video) # 1 for addition, 0 for removal
                neighbors.append((video, cost + delta, caches, caches_sizes, move))

    # suppression
    if supp:
        for cache_id in range(nbCaches):
            cache = caches[cache_id]
            for video in cache[:nbVideos]:  # Only consider the first nbVideos videos in the cache for removal
                previous_cost = calculate_video_latency(adj_list, caches, video, N_vid, N_endpoint, N_requests, N_caches, caches_sizes, videoSizes, endpointData, requests)
                caches[cache_id].remove(video)
                new_cost = calculate_video_latency(adj_list, caches, video, N_vid, N_endpoint, N_requests, N_caches, caches_sizes, videoSizes, endpointData, requests)
                delta = new_cost - previous_cost
                # cost = compute_cost(caches, endpointData, requests)
                caches[cache_id].append(video)
                move = (0, cache_id, video) # 1 for addition, 0 for removal
                neighbors.append((video, cost + delta, caches, caches_sizes, move))

    neighbors.sort(key=lambda x: x[1])
    if neighbors is None or len(neighbors) == 0:
        print(f"No neighbors found at iteration {iteration}, current state: previous_moves={previous_moves}, nVideos={nbVideos}, nCaches={nbCaches}, supp={supp}")
        return caches, caches_sizes
    best_neighbor = neighbors[0] if neighbors else (float('inf'), caches, caches_sizes, None)
    # print(f"Best neighbor: {best_neighbor} with cost {best_neighbor[1]}")
    #on applique le mouvement du meilleur voisin
    if best_neighbor[4][0] == 1:
        caches[best_neighbor[4][1]].append(best_neighbor[4][2])
    else:
        # print(f"Supression")
        caches[best_neighbor[4][1]].remove(best_neighbor[4][2])
    # caches[best_neighbor[4][1]].append(best_neighbor[4][2])

    caches_sizes[best_neighbor[4][0]] -= videoSizes[best_neighbor[4][1]]
    
#          local_search(N_vid, N_endpoint, N_request, N_cache, adj_list, video_sizes, caches_sizes, caches, endpoints, requests, iteration=10, previous_moves=None, nbCaches=50, nbVideos=100, supp=True)
    # return local_search(N_vid, N_endpoint, N_requests, N_caches, adj_list, videoSizes, caches_sizes, caches, endpointData, requests, iteration-1, best_neighbor[4], nbCaches, nbVideos, supp)
    return local_search(data, caches, caches_sizes, iteration-1, best_neighbor[4], nbCaches, nbVideos, supp)
                

    # for videos 
                
def preprocess_data(N_vid, N_endpoint, N_requests, N_caches, caches_sizes, videoSizes, caches, endpointData, requests):
    """
    Preprocess the data to sort the videos by size and number of requests.
    """
    video_request_count = [0] * N_vid
    video_endpoint_data = [0] * N_vid  # To store the endpoint data for each video
    for video_id, endpoint_id, num_requests in requests:
        video_request_count[video_id] += num_requests


    # Create a list of videos with their sizes and request counts
    videos_info = [(video_id, videoSizes[video_id], video_request_count[video_id], ) for video_id in range(N_vid)]
    

    # Sort videos by request count (descending) and then by size (ascending)
    videos_info.sort(key=lambda x: (-x[2], x[1]))

    video_sizes_sorted = [video[1] for video in videos_info]
    return video_sizes_sorted, videos_info

