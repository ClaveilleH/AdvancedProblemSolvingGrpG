import random 

def WriteInstance():
    """
        Crée un fichier Txt contenant une instance 
    """
    NbVideos = 5
    NbEndpoints = 2
    NbRequests = 4
    NbCaches = 3
    CapacityCache = 100 
    # SizeVideo = [50,50,80,30,110]
    SizeVideo = GenerateSizeVideo(NbVideos)
    # Endpoints = [(1000,[(0,100),(2,200),(1,300)]),
    #              (500,[])]
    Endpoints = GenerateEndpoints(NbEndpoints,NbCaches)
    # Requests = [(3,0,1500),(0,1,1000),(4,0,500),(1,0,1000)]
    Requests = GenerateRequests(NbRequests,NbVideos,NbEndpoints)

    with open("Mon_instance.txt","w") as fichier:
        fichier.write(f"{NbVideos} {NbEndpoints} {NbRequests} {NbCaches} {CapacityCache}\n")
        for size in SizeVideo:
            fichier.write(f"{size} ")
        fichier.write("\n")
        for endpoint in Endpoints:
            LatencyEndpoint = endpoint[0]
            NbCachesEndpoint = len(endpoint[1])
            fichier.write(f"{LatencyEndpoint} {NbCachesEndpoint}\n")
            for cache in endpoint[1]:
                fichier.write(f"{cache[0]} {cache[1]}\n")
        for request in Requests:
            fichier.write(f"{request[0]} {request[1]} {request[2]}\n")

def GenerateSizeVideo(NbVideo):
    """
        Genere une liste de taille pour les videos
    """
    return [random.randint(0,100) for _ in range(NbVideo)]

def GenerateEndpoints(NbEndpoints,NbCaches):
    """
        Genere pour chaque endpoint sa latence, et choisi sa liste de chaches associer et leurs latences
    """
    Endpoints = []
    for _ in range(NbEndpoints):
        Endpoint = ()
        # On choisi aleatoirement une latence pour le endpoint
        LantenceEndpoint = random.randint(500,1000)
        Caches = []
        # On choisi aleatoirement le nombre de cache associer au endpoint
        NbCachesEndpoint = random.randint(0,NbCaches) 
        # On creer une liste contenant les Id des caches associer au endpoint
        ListCaches = random.sample(range(0,NbCaches), NbCachesEndpoint)

        for indice in range(NbCachesEndpoint):
            IdCache = ListCaches[indice]
            # On creer le tupple contenant l'id du cache et sa latence choisi aleatoirement qui sera toujour inférieur à la latence du endpoint
            Caches.append((IdCache,random.randint(1,LantenceEndpoint)))
        Endpoint = (LantenceEndpoint, Caches)
        Endpoints.append(Endpoint)
    return Endpoints

def GenerateRequests (NbRequests,NbVideos,NbEndpoints):
    """
        Genere une liste de requete
    """
    Requests = []
    for _ in range(NbRequests):
        # On choisi aleatoirement une video
        IdVideo = random.randint(0,NbVideos-1)
        # On choisi aleatoirement un endpoint
        IdEndpoint = random.randint(0,NbEndpoints-1)
        # on choisi aleatoirement un nombre de video a envoyer
        NbVideoSend = random.randint(1,10000)
        Requests.append((IdVideo,IdEndpoint,NbVideoSend))
    return Requests

def main():
    WriteInstance()


if __name__ == "__main__":  
    main()