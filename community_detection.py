from graph import users, adjacency

def find_connected_components():
    visited    = set()
    components = []   

    for user_id in users:
        if user_id in visited:
            continue  

        component = []
        stack     = [user_id]

        while stack:
            current = stack.pop()   

            if current in visited:
                continue

            visited.add(current)
            component.append(current)

            for neighbor in adjacency.get(current, []):
                if neighbor not in visited:
                    stack.append(neighbor)

        components.append(component)

    result = []
    for component in components:
        result.append([
            {
                "id":       uid,
                "name":     users[uid]["name"],
                "avatar":   users[uid]["avatar"],
                "headline": users[uid]["headline"],
                "company":  users[uid]["company"],
                "skills":   users[uid]["skills"]
            }
            for uid in component
        ])

    return result

def build_vocabulary():
    vocab = set()
    for user in users.values():
        for skill in user["skills"]:
            vocab.add(skill)
    return sorted(list(vocab))


def skill_vector(user, vocab):
    return [1 if skill in user["skills"] else 0 for skill in vocab]


def cosine_similarity(vec_a, vec_b):
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = sum(a ** 2 for a in vec_a) ** 0.5
    mag_b = sum(b ** 2 for b in vec_b) ** 0.5
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return round(dot_product / (mag_a * mag_b), 4)


def find_skill_clusters(threshold=0.4):
    vocab    = build_vocabulary()
    assigned = set()    
    clusters = []

    for uid, user in users.items():
        if uid in assigned:
            continue

        
        cluster   = [uid]
        assigned.add(uid)
        vec_a     = skill_vector(user, vocab)

        for other_id, other_user in users.items():
            if other_id in assigned:
                continue

            vec_b = skill_vector(other_user, vocab)
            score = cosine_similarity(vec_a, vec_b)

            if score >= threshold:
                cluster.append(other_id)
                assigned.add(other_id)

        clusters.append(cluster)

    result = []
    for cluster in clusters:
        result.append([
            {
                "id":       uid,
                "name":     users[uid]["name"],
                "avatar":   users[uid]["avatar"],
                "headline": users[uid]["headline"],
                "company":  users[uid]["company"],
                "skills":   users[uid]["skills"],
            }
            for uid in cluster
        ])

    return result

def find_influence_hubs():
    user_ids = sorted(users.keys())
    n        = len(user_ids)

    # Map user_id → matrix index
    id_to_index = {uid: i for i, uid in enumerate(user_ids)}

    matrix = [[0] * n for _ in range(n)]

    for uid in user_ids:
        i = id_to_index[uid]
        for neighbor in adjacency.get(uid, []):
            if neighbor in id_to_index:
                j = id_to_index[neighbor]
                matrix[i][j] = 1 

   
    scores = []
    for uid in user_ids:
        i             = id_to_index[uid]
        degree        = sum(matrix[i])  
        second_degree = 0

        
        for j in range(n):
            if matrix[i][j] == 1:
                second_degree += sum(matrix[j])

        scores.append({
            "id":             uid,
            "name":           users[uid]["name"],
            "avatar":         users[uid]["avatar"],
            "headline":       users[uid]["headline"],
            "company":        users[uid]["company"],
            "direct_connections":  degree,
            "network_reach":  degree + second_degree
        })

    scores.sort(key=lambda x: x["network_reach"], reverse=True)
    return scores

def get_communities():
    return {
        "connected_components": find_connected_components(),
        "skill_clusters":       find_skill_clusters(),
        "influence_hubs":       find_influence_hubs()
    }