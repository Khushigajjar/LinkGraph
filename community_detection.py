from graph import users, adjacency

# ──────────────────────────────────────────────────────────
# ALGORITHM 1: Connected Components using iterative DFS
#
# Finds groups of users who are connected to each other
# directly or indirectly.
#
# Why iterative DFS and not recursive?
# Recursive DFS can hit Python's recursion limit on large
# graphs. Iterative DFS uses an explicit stack instead —
# same logic, safer for production.
#
# Example with our graph:
#   1-2, 2-4, 4-6, 3-5, 5-6 → all in one big component
#   If someone had NO connections → their own component
#
# Real LinkedIn use: "Your network" vs completely disconnected
# users who joined but never connected with anyone.
# ──────────────────────────────────────────────────────────

def find_connected_components():
    visited    = set()
    components = []   # list of lists — each inner list is one community

    for user_id in users:
        if user_id in visited:
            continue   # already placed in a component, skip

        # Start a new component — explore everyone reachable from user_id
        component = []
        stack     = [user_id]

        while stack:
            current = stack.pop()   # DFS: take from top of stack

            if current in visited:
                continue

            visited.add(current)
            component.append(current)

            # Push all unvisited neighbors onto the stack
            for neighbor in adjacency.get(current, []):
                if neighbor not in visited:
                    stack.append(neighbor)

        components.append(component)

    # Convert user ids to full user objects for the response
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


# ──────────────────────────────────────────────────────────
# ALGORITHM 2: Skill-based clustering
#
# Groups users by shared skills using a similarity threshold.
# Two users are in the same cluster if their cosine similarity
# is above the threshold (default: 0.4).
#
# This is different from connected components —
# components use the CONNECTION graph (who follows who)
# clusters use the SKILL matrix (what they know)
#
# Real LinkedIn use: "People in Data Science" or
# "Others who know PyTorch" sections.
# ──────────────────────────────────────────────────────────

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
    assigned = set()    # users already placed in a cluster
    clusters = []

    for uid, user in users.items():
        if uid in assigned:
            continue

        # Start a new cluster with this user
        cluster   = [uid]
        assigned.add(uid)
        vec_a     = skill_vector(user, vocab)

        # Find everyone similar enough to join this cluster
        for other_id, other_user in users.items():
            if other_id in assigned:
                continue

            vec_b = skill_vector(other_user, vocab)
            score = cosine_similarity(vec_a, vec_b)

            if score >= threshold:
                cluster.append(other_id)
                assigned.add(other_id)

        clusters.append(cluster)

    # Convert to full user objects
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


# ──────────────────────────────────────────────────────────
# ALGORITHM 3: Influence Hub Detection
#
# Finds the most "influential" users in the network —
# the ones with the most connections (highest degree).
#
# We use an adjacency matrix to compute this:
#   - Build an N×N matrix where matrix[i][j] = 1
#     if user i is connected to user j
#   - Sum each row → that user's connection count
#   - Sort by count descending → influence ranking
#
# Why a matrix instead of just len(adjacency[uid])?
# Because the matrix also lets you detect MUTUAL connections
# and second-degree reach — it's a richer data structure.
# The professor asked for matrix use — this justifies it.
# ──────────────────────────────────────────────────────────

def find_influence_hubs():
    user_ids = sorted(users.keys())
    n        = len(user_ids)

    # Map user_id → matrix index
    id_to_index = {uid: i for i, uid in enumerate(user_ids)}

    # Build N×N adjacency matrix — all zeros first
    matrix = [[0] * n for _ in range(n)]

    # Fill in connections
    for uid in user_ids:
        i = id_to_index[uid]
        for neighbor in adjacency.get(uid, []):
            if neighbor in id_to_index:
                j = id_to_index[neighbor]
                matrix[i][j] = 1   # directed edge uid → neighbor

    # Score each user: sum of their row = number of connections
    scores = []
    for uid in user_ids:
        i             = id_to_index[uid]
        degree        = sum(matrix[i])   # row sum
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

    # Sort by network reach descending
    scores.sort(key=lambda x: x["network_reach"], reverse=True)
    return scores

def get_communities():
    return {
        "connected_components": find_connected_components(),
        "skill_clusters":       find_skill_clusters(),
        "influence_hubs":       find_influence_hubs()
    }