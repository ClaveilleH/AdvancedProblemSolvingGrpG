from math import gcd
from functools import reduce

# taille maximale d'une dimension de table de programmation dynamique :
# au-delà, on considère que la résolution exacte est trop coûteuse
LIMIT = 10000
INF = float('inf')




def knapsack_value(values, weights, maxCapacity):
    """
    Sac à dos exact par programmation dynamique indexée sur la valeur.
    opt[i][V] = poids minimal pour atteindre une valeur d'au moins V
    avec les i premiers objets.
    Complexité en O(n * somme des valeurs) : intéressant quand la somme
    des valeurs est plus petite que la capacité.
    Renvoie (valeur optimale, ensemble des indices des objets choisis).
    """
    n = len(values)
    if n == 0 or maxCapacity == 0: # pas d'objets ou sac vide : pas de valeur
            return 0, set()
    
    opt = [ [INF] * (sum(values) + 1) for _ in range(n+1) ]
    # atteindre une valeur 0 ne coûte aucun poids
    for i in range(n + 1):
        opt[i][0] = 0

    # borne = somme des valeurs des i premiers objets,
    # soit la plus grande valeur atteignable à l'étape i
    borne = 0
    for i in range(1, n + 1):
        item_value, item_weight = values[i-1], weights[i-1]
        borne_prev = borne
        borne += item_value

        for value in range(1, borne+1):
            if value > borne_prev:
                # valeur inatteignable sans l'objet i : on est obligé de le prendre
                opt[i][value] = item_weight + opt[i-1][max(0, value - item_value)]
            else:
                # le meilleur entre ne pas prendre l'objet i et le prendre
                opt[i][value] = min(opt[i-1][value], item_weight + opt[i-1][max(0, value - item_value)])

    bag = set()
    # la valeur optimale est la plus grande valeur dont le poids minimal tient dans le sac
    score = max(value for value in range(borne + 1) if opt[n][value] <= maxCapacity)
    
    # reconstruction de la solution en remontant la table
    value = score
    for i in range(n, 0, -1):
        # si le poids change entre i-1 et i, c'est que l'objet i a été pris
        if opt[i][value] != opt[i-1][value]:
            bag.add(i - 1)
            value = max(0, value - values[i-1])

    return score,bag

def knapsack_weight(values, weights, maxCapacity):
    """
    Sac à dos exact par programmation dynamique indexée sur le poids.
    opt[i][w] = valeur maximale atteignable avec les i premiers objets
    et une capacité w.
    Complexité en O(n * W) : intéressant quand la capacité est plus petite
    que la somme des valeurs.
    Renvoie (valeur optimale, ensemble des indices des objets choisis).
    """
    n = len(values)
    if n == 0 or maxCapacity == 0:
        return 0, set()
    opt = [[0] * (maxCapacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        item_value, item_weight = values[i-1], weights[i-1]

        for capa in range(maxCapacity + 1):
            # par défaut, on ne prend pas l'objet i
            opt[i][capa] = opt[i-1][capa]
            # s'il rentre, on regarde si le prendre fait mieux
            if capa >= item_weight:
                opt[i][capa] = max(opt[i][capa], item_value + opt[i-1][capa - item_weight])

    bag = set()
    score = opt[n][maxCapacity]
    # reconstruction de la solution en remontant la table
    capa = maxCapacity
    for i in range(n, 0, -1):
        # si la valeur change entre i-1 et i, c'est que l'objet i a été pris
        if opt[i][capa] != opt[i-1][capa]:
            bag.add(i - 1)
            capa -= weights[i-1]

    return score, bag

def knapsack_goulton(values, weights, maxCapacity):
    """
    Sac à dos approché par algorithme glouton : on prend les objets par
    ratio valeur/poids décroissant tant qu'ils rentrent.
    Sert de solution de repli quand les deux tables de programmation
    dynamique seraient trop grandes.
    Renvoie (valeur obtenue, ensemble des indices des objets choisis).
    """
    # trop d'objets : on abandonne et on renvoie un sac vide
    if len(values) > LIMIT:
        return 0,set()
    
    # indices des objets triés du plus rentable au moins rentable
    order = sorted(range(len(values)), key=lambda i: values[i] / weights[i], reverse=True)
    bag = set()
    total_weight = 0
    total_value = 0
    for i in order: # indices triés
        # on ajoute l'objet s'il reste assez de place
        if total_weight + weights[i] <= maxCapacity:
            bag.add(i)
            total_weight += weights[i]
            total_value += values[i]


    return total_value, bag

def multiknapsack(data, caches, caches_sizes):
    """
    Remplit chaque cache indépendamment des autres en résolvant un sac à dos :
    les objets sont les vidéos, le poids est leur taille et la valeur est le
    gain de latence qu'elles apportent dans ce cache.
    Les caches ne se concertent pas : une même vidéo peut être placée
    dans plusieurs caches voisins.
    Modifie caches en place.
    """
    weight, gcd_weight = preprocess_weight_genius(data)
    values, gcd_values = preprocess_values_genius(data)
    for cache_id in range(data["N_cache"]):
        # les poids ont été divisés par leur pgcd, on fait pareil pour la capacité
        capacity = caches_sizes[cache_id] // gcd_weight
        sumvalue = sum(values[cache_id])

        # les deux tables seraient trop grandes : on arrête tout
        if sumvalue > LIMIT and capacity > LIMIT:
            return 0, set()

        # on choisit la programmation dynamique dont la table est la plus petite
        elif sumvalue>capacity:
            score, bag = knapsack_weight(values[cache_id], weight, capacity)
            caches[cache_id] = bag
        else:
            score, bag = knapsack_value(values[cache_id], weight, capacity)
            caches[cache_id] = bag

def multiknapsack_bg(data, caches, caches_sizes):
    """
    Version améliorée de multiknapsack : les caches sont remplis un par un,
    du plus prometteur au moins prometteur, et après chaque cache rempli on
    diminue la valeur des vidéos placées dans les autres caches reliés aux
    mêmes endpoints, pour éviter de stocker plusieurs fois la même vidéo
    sans gain supplémentaire.
    Modifie caches en place.
    """
    endpoints = data["endpoints"]
    requests = data["requests"]
    weight, gcd_weight = preprocess_weight_genius(data)
    values, gcd_values= preprocess_values_genius(data)
    # adj_list[vid_id] = identifiants des requêtes qui portent sur cette vidéo
    adj_list = data["adj_list"]
    # caches qu'il reste à remplir
    remaining = set(range(data["N_cache"]))
    
    while remaining:
        # on prend le cache dont le gain total potentiel est le plus grand
        # (on remultiplie par le pgcd pour comparer les caches à la même échelle)
        cache_id = max(remaining,key=lambda c: sum(values[c]) * gcd_values[c])
        remaining.discard(cache_id)
        capacity = caches_sizes[cache_id] // gcd_weight
        # on ne garde que les vidéos utiles : valeur non nulle et qui rentrent dans le cache
        objects = [ i for i in range(data["N_vid"]) if values[cache_id][i] > 0 and weight[i] <= capacity ]
        sub_values = [values[cache_id][i] for i in objects]
        sub_weight = [weight[i] for i in objects]
        sumsubvalues = sum(sub_values)
        # les deux tables seraient trop grandes : on se rabat sur le glouton
        if sumsubvalues > LIMIT and capacity > LIMIT:
            score,bag = knapsack_goulton(sub_values,sub_weight,capacity)

        # sinon on choisit la programmation dynamique dont la table est la plus petite
        elif sumsubvalues > capacity:
            score, bag = knapsack_weight(sub_values, sub_weight, capacity)

        else:
            score, bag = knapsack_value(sub_values, sub_weight, capacity)

        # le sac contient des indices dans la sous-liste : on revient aux identifiants de vidéos
        bag = {objects[i] for i in bag}
        caches[cache_id] = bag

        # mise à jour des valeurs des autres caches pour chaque vidéo qu'on vient de placer
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
                        # on retire la perte (ramenée à l'échelle du pgcd de cache2), sans passer sous 0
                        values[cache_id2][vid_id] = max(
                            0,
                            values[cache_id2][vid_id] - (perte * num_requests) // gcd_values[cache_id2]
                        )


def useless_object(weights,values,capacity):
    """
    Renvoie l'ensemble des indices des objets inutiles : ceux qui sont
    trop lourds pour le sac ou qui n'ont aucune valeur.
    """
    n = len(values)
    res = set()
    for i in range(n):
        if weights[i]>capacity or values[i]==0:
            res.add(i)
    return res


def preprocess_weight_genius(data):
    """
    Divise les tailles des vidéos par leur pgcd pour réduire la taille de la
    table de programmation dynamique sans changer la solution.
    Renvoie (poids réduits, pgcd) ; les capacités des caches doivent être
    divisées par le même pgcd.
    """
    weights = data["video_sizes"]
    # "or 1" évite un pgcd nul si la liste est vide ou ne contient que des 0
    gcd_weight = reduce(gcd, weights, 0) or 1
    if gcd_weight > 1:
        weights = [ w // gcd_weight for w in weights ]

    return weights,gcd_weight


def preprocess_values_genius(data):
    """
    Calcule la valeur de chaque vidéo dans chaque cache :
    values[cache_id][vid_id] = latence totale économisée (gain par requête
    multiplié par le nombre de requêtes) si la vidéo est dans ce cache
    plutôt que servie depuis le datacenter.
    Les valeurs de chaque cache sont ensuite divisées par leur pgcd.
    Renvoie (valeurs réduites, liste des pgcd par cache).
    """
    gcd_values = []
    values = [ [0]*data["N_vid"] for _ in range(data["N_cache"]) ]
    
    for request in data["requests"]:
        vid_id, endpoint_id, num_request = request
        latency, linked_caches = data["endpoints"][endpoint_id]
        for cache_id, cache_latency in linked_caches:
            # gain de latence par rapport au datacenter
            gain = latency - cache_latency
            # on ignore les caches plus lents que le datacenter
            if gain > 0:
                values[cache_id][vid_id]+=(gain*num_request)
    # réduction des valeurs de chaque cache par leur pgcd
    for cache_id in range(data["N_cache"]):
        gcd_value = reduce(gcd, values[cache_id],0) or 1
        if gcd_value > 1:
            values[cache_id] = [ v // gcd_value for v in values[cache_id] ]
        gcd_values.append(gcd_value)

    return values, gcd_values



