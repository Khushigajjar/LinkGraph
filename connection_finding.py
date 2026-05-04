from graph import users, adjacency

def get_mutual_friends(user_id_a, user_id_b):
    if user_id_a not in users or user_id_b not in users:
        return []

    set_a = set(adjacency.get(user_id_a, []))
    set_b = set(adjacency.get(user_id_b, []))

    mutual_ids = set_a & set_b

    return [
        {
            "id":       uid,
            "name":     users[uid]["name"],
            "avatar":   users[uid]["avatar"],
            "headline": users[uid]["headline"]
        }
        for uid in mutual_ids
    ]


def jaccard_similarity(user_id_a, user_id_b):
    set_a = set(adjacency.get(user_id_a, []))
    set_b = set(adjacency.get(user_id_b, []))

    intersection = set_a & set_b
    union        = set_a | set_b

    if len(union) == 0:
        return 0.0

    return round(len(intersection) / len(union), 4)



def bfs_suggestions(user_id):
    if user_id not in users:
        return []

    direct  = set(adjacency.get(user_id, []))   
    visited = {user_id} | direct                 
    queue   = list(direct)                       
    suggestions = []

    while queue:
        current = queue.pop(0) 

        for neighbor in adjacency.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

                
                mutual       = get_mutual_friends(user_id, neighbor)
                jaccard_score = jaccard_similarity(user_id, neighbor)

                suggestions.append({
                    "id":             neighbor,
                    "name":           users[neighbor]["name"],
                    "avatar":         users[neighbor]["avatar"],
                    "headline":       users[neighbor]["headline"],
                    "company":        users[neighbor]["company"],
                    "skills":         users[neighbor]["skills"],
                    "mutual_friends": mutual,
                    "mutual_count":   len(mutual),
                    "jaccard_score":  jaccard_score
                })

    suggestions.sort(key=lambda x: x["jaccard_score"], reverse=True)

    return suggestions

def skill_based_suggestions(user_id):
    if user_id not in users:
        return []

    target_skills = set(users[user_id]["skills"])
    direct        = set(adjacency.get(user_id, []))
    suggestions   = []

    for uid, user in users.items():
        if uid == user_id or uid in direct:
            continue

        other_skills = set(user["skills"])

        shared = target_skills & other_skills

        
        all_skills = target_skills | other_skills

        
        skill_jaccard = round(len(shared) / len(all_skills), 4) if all_skills else 0

        if len(shared) > 0:   
            suggestions.append({
                "id":             uid,
                "name":           user["name"],
                "avatar":         user["avatar"],
                "headline":       user["headline"],
                "company":        user["company"],
                "shared_skills":  list(shared),
                "skill_overlap":  skill_jaccard
            })


    suggestions.sort(key=lambda x: x["skill_overlap"], reverse=True)
    return suggestions


def get_all_suggestions(user_id):
    network_based = bfs_suggestions(user_id)
    skill_based   = skill_based_suggestions(user_id)

    
    seen = set()
    combined = []

   
    for s in network_based:
        if s["id"] not in seen:
            seen.add(s["id"])
            combined.append({**s, "source": "network"})

    for s in skill_based:
        if s["id"] not in seen:
            seen.add(s["id"])
            combined.append({**s, "source": "skills"})

    return combined