from graph import users, adjacency


def top_cluster_skills(cluster, limit=3):
    counts = {}
    for uid in cluster:
        for skill in users[uid]["skills"]:
            counts[skill] = counts.get(skill, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [skill for skill, _ in ranked[:limit]]

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


COMMUNITY_DEFINITIONS = [
    ("AI Strategy Community", ["AI Strategy", "Machine Learning", "Recommendation Systems"]),
    ("Data Analytics Community", ["Data Analytics", "People Analytics", "Data Science", "Business Analytics"]),
    ("Product Management Community", ["Product Management", "Product Strategy", "Stakeholder Management"]),
    ("Backend Engineering Community", ["Python", "Flask", "Graph Algorithms", "API Design"]),
    ("Design and UX Community", ["Product Design", "UX Research", "Design Systems", "User Interviews"]),
    ("Professional Growth Community", ["Employer Branding", "Community Building", "Networking", "Learning Programs"])
]


def find_skill_clusters(threshold=0.4):
    clusters = []

    for community_name, focus_skills in COMMUNITY_DEFINITIONS:
        focus = set(focus_skills)
        cluster = [
            uid for uid, user in users.items()
            if focus & set(user["skills"])
        ]

        if len(cluster) >= 2:
            clusters.append((community_name, focus_skills, cluster))

    result = []
    for community_name, focus, cluster in clusters:
        result.append([
            {
                "id":       uid,
                "name":     users[uid]["name"],
                "avatar":   users[uid]["avatar"],
                "headline": users[uid]["headline"],
                "company":  users[uid]["company"],
                "skills":   users[uid]["skills"],
                "cluster_focus": focus,
                "community_name": community_name,
                "cluster_summary": "Members share " + ", ".join(focus[:3])
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
            "network_reach":  degree + second_degree,
            "hub_reason":     "High second-degree reach across the professional graph"
        })

    scores.sort(key=lambda x: x["network_reach"], reverse=True)
    return scores

def get_communities():
    return {
        "connected_components": find_connected_components(),
        "skill_clusters":       find_skill_clusters(),
        "influence_hubs":       find_influence_hubs()
    }
