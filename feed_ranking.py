from datetime import datetime, timezone
from turtle import right
from graph import posts, enrich_posts

# Formula:
#   score = (likes × 1) + (comments × 3) + (shares × 5) - age_penalty


def engagement_score(post):
    likes    = post["likes"]
    comments = post["comments"]
    shares   = post["shares"]

    now = datetime.now()
    age_hours = (now - post["timestamp"]).total_seconds() / 3600

    age_penalty = age_hours * 2

    score = (likes * 1) + (comments * 3) + (shares * 5) - age_penalty

    return round(score, 2)



def merge_sort(post_list):
    if len(post_list) <= 1:
        return post_list

    mid = len(post_list) // 2
    left  = merge_sort(post_list[:mid])  
    right = merge_sort(post_list[mid:])  


    return merge(left, right)


def merge(left, right):
    result = []
    i = 0 
    j = 0 

    
    while i < len(left) and j < len(right):
        score_left  = left[i]["score"]
        score_right = right[j]["score"]

        if score_left >= score_right:
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
        self.head    = None   
        self.tail    = None   
        self.current = None   

    def add_story(self, post):
        node = StoryNode(post)

        if self.head is None:
            self.head    = node
            self.tail    = node
            self.current = node
        else:
            
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
        return None  
    def go_prev(self):
        if self.current and self.current.prev:
            self.current = self.current.prev
            return self.current.post
        return None  


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