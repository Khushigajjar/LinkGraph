from datetime import datetime
from graph import enrich_posts

# Professional feed score:
# engagement + network boost + shared-skill boost - recency penalty


def _normalise(value):
    return value.strip().lower()


def engagement_score(post):
    likes = post["likes"]
    comments = post["comments"]
    shares = post["shares"]
    return (likes * 1) + (comments * 3) + (shares * 5)


def professional_relevance_score(post, user_id=None):
    from graph import adjacency, users

    base_score = engagement_score(post)
    connected_ids = set(adjacency.get(user_id, [])) if user_id else set()
    current_user = users.get(user_id)

    tag_set = {_normalise(tag) for tag in post.get("tags", [])}
    skill_set = {_normalise(skill) for skill in current_user.get("skills", [])} if current_user else set()
    shared_interests = sorted(tag_set & skill_set)

    network_boost = 40 if post["author_id"] in connected_ids else 0
    skill_boost = 25 * len(shared_interests)

    now = datetime.now()
    age_hours = max((now - post["timestamp"]).total_seconds() / 3600, 0)
    recency_penalty = min(age_hours * 0.8, 120)

    score = base_score + network_boost + skill_boost - recency_penalty
    reasons = []
    if network_boost:
        reasons.append("author is in your network")
    if shared_interests:
        reasons.append("matches " + ", ".join(shared_interests[:3]))
    if not reasons:
        reasons.append("strong professional engagement")

    return {
        "score": round(score, 2),
        "match_reason": "; ".join(reasons),
        "shared_interests": shared_interests,
        "score_breakdown": {
            "engagement": base_score,
            "network_boost": network_boost,
            "skill_boost": skill_boost,
            "recency_penalty": round(recency_penalty, 2)
        }
    }


comparison_count = 0


def post_score(post):
    return post.get("score", engagement_score(post))


def merge_sort(post_list):
    if len(post_list) <= 1:
        return post_list
    mid = len(post_list) // 2
    left = merge_sort(post_list[:mid])
    right = merge_sort(post_list[mid:])
    return merge(left, right)


def merge(left, right):
    global comparison_count
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        comparison_count += 1
        if post_score(left[i]) >= post_score(right[j]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


class StoryNode:
    def __init__(self, post):
        self.post = post
        self.next = None
        self.prev = None


class StoryList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.current = None

    def add_story(self, post):
        node = StoryNode(post)

        if self.head is None:
            self.head = node
            self.tail = node
            self.current = node
        else:
            node.prev = self.tail
            self.tail.next = node
            self.tail = node

    def get_current(self):
        if self.current:
            return self.current.post
        return None

    def go_next(self):
        if self.current and self.current.next:
            self.current = self.current.next
            return self.current.post
        return None

    def go_prev(self):
        if self.current and self.current.prev:
            self.current = self.current.prev
            return self.current.post
        return None


def get_ranked_feed(user_id=None, post_list=None):
    global comparison_count
    comparison_count = 0

    from graph import posts as default_posts

    source_posts = post_list if post_list is not None else default_posts

    scored_posts = []
    for post in source_posts:
        relevance = professional_relevance_score(post, user_id)
        scored_posts.append({**post, **relevance})

    import time
    start = time.time()
    sorted_posts = merge_sort(scored_posts)
    elapsed = round((time.time() - start) * 1000, 2)

    return enrich_posts(sorted_posts), comparison_count, elapsed
