from graph import users, posts, enrich_posts


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

    magnitude_a = sum(a ** 2 for a in vec_a) ** 0.5
    magnitude_b = sum(b ** 2 for b in vec_b) ** 0.5

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return round(dot_product / (magnitude_a * magnitude_b), 4)


def find_similar_users(user_id):
    vocab  = build_vocabulary()
    target = users[user_id]
    target_vec = skill_vector(target, vocab)

    similarities = []

    for uid, user in users.items():
        if uid == user_id:
            continue  

        other_vec  = skill_vector(user, vocab)
        score  = cosine_similarity(target_vec, other_vec)

        similarities.append({
            "user_id": uid,
            "name":  user["name"],
            "avatar":  user["avatar"],
            "headline":user["headline"],
            "similarity": score
        })

    
    for i in range(1, len(similarities)):
        key = similarities[i]
        j   = i - 1
        while j >= 0 and similarities[j]["similarity"] < key["similarity"]:
            similarities[j + 1] = similarities[j]
            j -= 1
        similarities[j + 1] = key

    return similarities

def collaborative_filter(user_id, top_n=3):
    similar_users = find_similar_users(user_id)

   
    relevant = [u for u in similar_users if u["similarity"] > 0.3]

   
    top_similar = relevant[:top_n]
    top_ids     = {u["user_id"] for u in top_similar}

    recommended = []
    for post in posts:
        if post["author_id"] in top_ids:
            recommended.append(post)

    return enrich_posts(recommended)

def engagement_score(post):
    return (post["likes"] * 1) + (post["comments"] * 3) + (post["shares"] * 5)


def find_trending(post_list):
    if len(post_list) == 1:
        return post_list[0]
    
    mid = len(post_list) // 2
    left = find_trending(post_list[:mid])
    right = find_trending(post_list[mid:])

   
    if engagement_score(left) >= engagement_score(right):
        return left
    return right


def get_trending_posts(top_n=3):
   
    remaining = list(posts)
    trending = []

    for _ in range(min(top_n, len(remaining))):
        winner = find_trending(remaining)
        trending.append(winner)
        remaining.remove(winner)

    return enrich_posts(trending)

def get_recommendations(user_id):
    personalised = collaborative_filter(user_id)
    trending     = get_trending_posts()

    seen = set()
    combined = []

    for post in personalised + trending:
        if post["id"] not in seen:
            seen.add(post["id"])
            combined.append({
                **post,
                "timestamp": post["timestamp"].strftime("%B %d, %Y")
            })

    return combined