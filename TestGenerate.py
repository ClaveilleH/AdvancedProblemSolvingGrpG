import random 
import os

OUTPUT_DIR_PATH = "instances/generated"

def write_instance(file_path):
    """
        Crée un fichier Txt contenant une instance 
    """
    nbVideos = 5
    nbEndpoints = 2
    nbRequests = 4
    nbCaches = 3
    capacityCache = 100

    # SizeVideo = [50,50,80,30,110]
    sizeVideo = generate_size_video(nbVideos)
    # Endpoints = [(1000,[(0,100),(2,200),(1,300)]),
    #              (500,[])]
    endpoints = generate_edpoints(nbEndpoints,nbCaches)
    # Requests = [(3,0,1500),(0,1,1000),(4,0,500),(1,0,1000)]
    requests = generate_requests(nbRequests,nbVideos,nbEndpoints)

    with open(file_path,"w") as fichier:
        fichier.write(f"{nbVideos} {nbEndpoints} {nbRequests} {nbCaches} {capacityCache}\n")
        for size in sizeVideo:
            fichier.write(f"{size} ")
        fichier.write("\n")
        for endpoint in endpoints:
            latencyEndpoint = endpoint[0]
            nbCachesEndpoint = len(endpoint[1])
            fichier.write(f"{latencyEndpoint} {nbCachesEndpoint}\n")
            for cache in endpoint[1]:
                fichier.write(f"{cache[0]} {cache[1]}\n")
        for request in requests:
            fichier.write(f"{request[0]} {request[1]} {request[2]}\n")

def generate_size_video(nbVideo):
    """
        Genere une liste de taille pour les videos
    """
    return [random.randint(0,100) for _ in range(nbVideo)]

def generate_edpoints(nbEndpoints, nbCaches):
    """
        Genere pour chaque endpoint sa latence, et choisi sa liste de chaches associer et leurs latences
    """
    endpoints = []
    for _ in range(nbEndpoints):
        endpoint = ()
        # On choisi aleatoirement une latence pour le endpoint
        lantenceEndpoint = random.randint(500,1000)
        caches = []
        # On choisi aleatoirement le nombre de cache associer au endpoint
        nbCachesEndpoint = random.randint(0,nbCaches) 
        # On creer une liste contenant les Id des caches associer au endpoint
        listCaches = random.sample(range(0,nbCaches), nbCachesEndpoint)

        for indice in range(nbCachesEndpoint):
            idCache = listCaches[indice]
            # On creer le tupple contenant l'id du cache et sa latence choisi aleatoirement qui sera toujour inférieur à la latence du endpoint
            caches.append((idCache,random.randint(1,lantenceEndpoint)))
        endpoint = (lantenceEndpoint, caches)
        endpoints.append(endpoint)

    return endpoints

def generate_requests (nbRequests, nbVideos, nbEndpoints):
    """
        Genere une liste de requete
    """
    requests = []
    for _ in range(nbRequests):
        # On choisi aleatoirement une video
        idVideo = random.randint(0,nbVideos-1)
        # On choisi aleatoirement un endpoint
        idEndpoint = random.randint(0,nbEndpoints-1)
        # on choisi aleatoirement un nombre de video a envoyer
        nbVideoSend = random.randint(1,10000)
        requests.append((idVideo,idEndpoint,nbVideoSend))

    return requests

def main():
    if not os.path.exists(OUTPUT_DIR_PATH):
        os.makedirs(OUTPUT_DIR_PATH)
    write_instance(f"{OUTPUT_DIR_PATH}/mon_instance.txt")


if __name__ == "__main__":  
    main()