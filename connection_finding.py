from graph import users, adjacency

# ──────────────────────────────────────────────────────────
# ALGORITHM 1: Mutual Friends (Set Intersection)
#
# Given two users, find who they BOTH know.
#
# We treat each user's connections as a SET.
# Set intersection gives us the overlap instantly.
#
# Example:
#   Khushi's connections = {2, 3}      (Rahul, Zijie)
#   Clara's connections  = {4, 5}
#   Rahul's connections  = {1, 4}
#
#   Khushi vs Rahul → {2,3} ∩ {1,4} = {} → no mutuals
#   Khushi vs Clara → {2,3} ∩ {4,5} = {} → no mutuals
#   Rahul  vs Alice → {1,4} ∩ {2,6} = {} → no mutuals
#
# Why sets and not lists?
#   List intersection = O(n²) — check every pair
#   Set intersection  = O(min(n,m)) — hash lookup
# ──────────────────────────────────────────────────────────

def get_mutual_friends(user_id_a, user_id_b):
    if user_id_a not in users or user_id_b not in users:
        return []

    # Convert connection lists to sets for O(1) lookup
    set_a = set(adjacency.get(user_id_a, []))
    set_b = set(adjacency.get(user_id_b, []))

    # Intersection = users both are connected to
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


# ──────────────────────────────────────────────────────────
# ALGORITHM 2: Jaccard Similarity
#
# Measures HOW SIMILAR two users' networks are.
# Not just "do they share friends" but "what fraction
# of their combined network do they share?"
#
# Formula:
#   jaccard = |A ∩ B| / |A ∪ B|
#
#   |A ∩ B| = number of mutual friends
#   |A ∪ B| = total unique friends across both users
#
# Example:
#   Khushi connections = {2, 3}
#   Bob    connections = {3, 6}
#   Intersection = {3}       → 1 mutual
#   Union        = {2, 3, 6} → 3 total
#   Jaccard      = 1/3 = 0.33
#
# Result between 0 (no overlap) and 1 (identical networks)
# Higher Jaccard → stronger suggestion to connect
# ──────────────────────────────────────────────────────────

def jaccard_similarity(user_id_a, user_id_b):
    set_a = set(adjacency.get(user_id_a, []))
    set_b = set(adjacency.get(user_id_b, []))

    intersection = set_a & set_b
    union        = set_a | set_b

    # Edge case: both users have zero connections
    if len(union) == 0:
        return 0.0

    return round(len(intersection) / len(union), 4)


# ──────────────────────────────────────────────────────────
# ALGORITHM 3: BFS Friend Suggestion
#
# Finds people the user should connect with by exploring
# the network in expanding "waves":
#   Wave 1 = direct connections       (skip — already connected)
#   Wave 2 = connections of connections (suggest these)
#
# BFS guarantees we find the CLOSEST strangers first
# (2nd degree before 3rd degree) — exactly what LinkedIn does.
#
# Data structure: a queue (FIFO)
#   - We process users level by level
#   - First in, first explored
#   - This is what makes it BFS not DFS
# ──────────────────────────────────────────────────────────

def bfs_suggestions(user_id):
    if user_id not in users:
        return []

    direct  = set(adjacency.get(user_id, []))   # degree-1: already connected
    visited = {user_id} | direct                 # don't revisit these
    queue   = list(direct)                       # start exploring from direct connections
    suggestions = []

    while queue:
        current = queue.pop(0)   # FIFO — take from front (BFS)

        for neighbor in adjacency.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

                # This neighbor is reachable but not directly connected
                # → they are a 2nd degree connection → suggest them
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

    # Sort by jaccard score — strongest network overlap first
    suggestions.sort(key=lambda x: x["jaccard_score"], reverse=True)

    return suggestions


# ──────────────────────────────────────────────────────────
# ALGORITHM 4: Skill-based connection suggestions
#
# BFS finds people close in the GRAPH.
# This finds people close in SKILLS —
# even if they are far away in the connection graph.
#
# Steps:
#   1. Build skill sets for the target user
#   2. For every user NOT already connected:
#      compute skill overlap using set intersection
#   3. Sort by overlap count descending
#
# Real LinkedIn use: "People who also know Python"
# ──────────────────────────────────────────────────────────

def skill_based_suggestions(user_id):
    if user_id not in users:
        return []

    target_skills = set(users[user_id]["skills"])
    direct        = set(adjacency.get(user_id, []))
    suggestions   = []

    for uid, user in users.items():
        # Skip self and already-connected users
        if uid == user_id or uid in direct:
            continue

        other_skills = set(user["skills"])

        # Set intersection — shared skills
        shared = target_skills & other_skills

        # Set union — all unique skills combined
        all_skills = target_skills | other_skills

        # Jaccard on skills (not connections)
        skill_jaccard = round(len(shared) / len(all_skills), 4) if all_skills else 0

        if len(shared) > 0:   # only suggest if at least 1 shared skill
            suggestions.append({
                "id":             uid,
                "name":           user["name"],
                "avatar":         user["avatar"],
                "headline":       user["headline"],
                "company":        user["company"],
                "shared_skills":  list(shared),
                "skill_overlap":  skill_jaccard
            })

    # Sort by skill overlap descending
    suggestions.sort(key=lambda x: x["skill_overlap"], reverse=True)
    return suggestions


# ──────────────────────────────────────────────────────────
# MAIN FUNCTIONS: what app.py will call
# ──────────────────────────────────────────────────────────

def get_all_suggestions(user_id):
    network_based = bfs_suggestions(user_id)
    skill_based   = skill_based_suggestions(user_id)

    # Deduplicate — a user could appear in both lists
    seen     = set()
    combined = []

    # Network-based suggestions come first
    for s in network_based:
        if s["id"] not in seen:
            seen.add(s["id"])
            combined.append({**s, "source": "network"})

    # Then skill-based suggestions
    for s in skill_based:
        if s["id"] not in seen:
            seen.add(s["id"])
            combined.append({**s, "source": "skills"})

    return combined