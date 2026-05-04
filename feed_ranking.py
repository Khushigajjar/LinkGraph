from datetime import datetime, timezone
from turtle import right
from graph import posts, enrich_posts

# Formula:
#   score = (likes × 1) + (comments × 3) + (shares × 5) - age_penalty


def engagement_score(post):
    likes    = post["likes"]
    comments = post["comments"]
    shares   = post["shares"]

    # How many hours ago was this posted?
    now = datetime.now()
    age_hours = (now - post["timestamp"]).total_seconds() / 3600

    # Recency penalty: lose 2 points for every hour old
    # A post from 10 hours ago loses 20 points
    # A post from 5 days ago loses 240 points
    age_penalty = age_hours * 2

    score = (likes * 1) + (comments * 3) + (shares * 5) - age_penalty

    return round(score, 2)

# Merge Sort
# Sorts posts by their engagement score — highest first.

# Time complexity: O(n log n) — much better than bubble sort O(n²)


def merge_sort(post_list):
    # Base case: a list of 0 or 1 items is already sorted
    if len(post_list) <= 1:
        return post_list

    # Step 1: Split down the middle
    mid = len(post_list) // 2
    left  = merge_sort(post_list[:mid])   # sort left half recursively
    right = merge_sort(post_list[mid:])   # sort right half recursively

    # Step 2: Merge the two sorted halves
    return merge(left, right)


def merge(left, right):
    result = []
    i = 0  # pointer for left list
    j = 0  # pointer for right list

    # Compare scores from both halves, take the higher one first
    while i < len(left) and j < len(right):
        score_left  = left[i]["score"]
        score_right = right[j]["score"]

        if score_left >= score_right:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    # One list ran out — append whatever remains from the other
    result.extend(left[i:])
    result.extend(right[j:])

    return result

class StoryNode:
    def __init__(self, post):
        self.post = post
        self.next = None      # points to next story
        self.prev = None      # points to previous story


class StoryList:
    def __init__(self):
        self.head    = None   # first story
        self.tail    = None   # last story
        self.current = None   # currently viewed story

    def add_story(self, post):
        node = StoryNode(post)

        if self.head is None:
            # First story added
            self.head    = node
            self.tail    = node
            self.current = node
        else:
            # Append to end
            node.prev    = self.tail
            self.tail.next = node
            self.tail    = node

    def get_current(self):
        if self.current:
            return self.current.post
        return None

    def go_next(self):
        if self.current and self.current.next:
            self.current = self.current.next
            return self.current.post
        return None   # already at last story

    def go_prev(self):
        if self.current and self.current.prev:
            self.current = self.current.prev
            return self.current.post
        return None   # already at first story


def get_ranked_feed(user_id=None):
    from graph import adjacency
    connected_ids = set(adjacency.get(user_id, [])) if user_id else set()

    scored_posts = []
    for post in posts:
        base_score = engagement_score(post)
        if post["author_id"] in connected_ids:
            base_score *= 1.4
        scored_posts.append({
            **post,
            "score": round(base_score, 2)
        })
    return enrich_posts(merge_sort(scored_posts))