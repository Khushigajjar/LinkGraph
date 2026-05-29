from graph import users, adjacency


def get_mutual_friends(user_id_a, user_id_b):
    if user_id_a not in users or user_id_b not in users:
        return []

    set_a = set(adjacency.get(user_id_a, []))
    set_b = set(adjacency.get(user_id_b, []))
    mutual_ids = set_a & set_b

    return [
        {
            "id": uid,
            "name": users[uid]["name"],
            "avatar": users[uid]["avatar"],
            "headline": users[uid]["headline"]
        }
        for uid in mutual_ids
    ]


def shared_skills(user_id_a, user_id_b):
    if user_id_a not in users or user_id_b not in users:
        return []
    return sorted(set(users[user_id_a]["skills"]) & set(users[user_id_b]["skills"]))


def jaccard_similarity(user_id_a, user_id_b):
    set_a = set(adjacency.get(user_id_a, []))
    set_b = set(adjacency.get(user_id_b, []))

    intersection = set_a & set_b
    union = set_a | set_b

    if len(union) == 0:
        return 0.0

    return round(len(intersection) / len(union), 4)


def network_reason(mutual, skills, degree):
    parts = []
    if mutual:
        names = ", ".join(person["name"] for person in mutual[:2])
        extra = len(mutual) - 2
        if extra > 0:
            names += f" and {extra} more"
        parts.append(f"Shared connections: {names}")
    else:
        suffix = "nd" if degree == 2 else "rd"
        parts.append(f"{degree}{suffix}-degree professional connection")

    if skills:
        parts.append("shared skills: " + ", ".join(skills[:3]))

    return "; ".join(parts)


def bfs_suggestions(user_id):
    if user_id not in users:
        return []

    direct = set(adjacency.get(user_id, []))
    visited = {user_id} | direct
    queue = [(neighbor, 1) for neighbor in direct]
    suggestions = []

    while queue:
        current, depth = queue.pop(0)

        for neighbor in adjacency.get(current, []):
            if neighbor in visited:
                continue

            visited.add(neighbor)

            if depth <= 2:
                jaccard_score = jaccard_similarity(user_id, neighbor)
                mutual = get_mutual_friends(user_id, neighbor)
                skills = shared_skills(user_id, neighbor)
                degree = depth + 1

                suggestions.append({
                    "id": neighbor,
                    "name": users[neighbor]["name"],
                    "avatar": users[neighbor]["avatar"],
                    "headline": users[neighbor]["headline"],
                    "company": users[neighbor]["company"],
                    "skills": users[neighbor]["skills"],
                    "shared_skills": skills,
                    "mutual_friends": mutual,
                    "mutual_count": len(mutual),
                    "jaccard_score": jaccard_score,
                    "degree": degree,
                    "recommendation_reason": network_reason(mutual, skills, degree)
                })

                if depth < 2:
                    queue.append((neighbor, depth + 1))

    suggestions.sort(
        key=lambda x: (x["mutual_count"], x["jaccard_score"], len(x["shared_skills"])),
        reverse=True
    )
    return suggestions


def skill_based_suggestions(user_id):
    if user_id not in users:
        return []

    target_skills = set(users[user_id]["skills"])
    direct = set(adjacency.get(user_id, []))
    suggestions = []

    for uid, user in users.items():
        if uid == user_id or uid in direct:
            continue

        shared = sorted(target_skills & set(user["skills"]))
        all_skills = target_skills | set(user["skills"])
        skill_jaccard = round(len(shared) / len(all_skills), 4) if all_skills else 0

        if shared:
            suggestions.append({
                "id": uid,
                "name": user["name"],
                "avatar": user["avatar"],
                "headline": user["headline"],
                "company": user["company"],
                "skills": user["skills"],
                "shared_skills": shared,
                "skill_overlap": skill_jaccard,
                "recommendation_reason": "Shared skills: " + ", ".join(shared[:3])
            })

    suggestions.sort(key=lambda x: x["skill_overlap"], reverse=True)
    return suggestions


def get_all_suggestions(user_id):
    network_based = bfs_suggestions(user_id)
    skill_based = skill_based_suggestions(user_id)
    combined = []

    for suggestion in network_based:
        combined.append({**suggestion, "source": "network"})

    seen_in_skills = set()
    for suggestion in skill_based:
        if suggestion["id"] not in seen_in_skills:
            seen_in_skills.add(suggestion["id"])
            combined.append({**suggestion, "source": "skills"})

    return combined
