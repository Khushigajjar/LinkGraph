import json
from datetime import datetime
with open("dataset.json", "r") as f:
    raw = json.load(f)


users = { user["id"]: user for user in raw["users"] }


adjacency = { user["id"]: user["connections"] for user in raw["users"] }

posts = []
for post in raw["posts"]:
    post["timestamp"] = datetime.fromisoformat(post["timestamp"])
    posts.append(post)

def enrich_posts(post_list):
    enriched = []
    for post in post_list:
        author = users[post["author_id"]]
        enriched.append({
            **post,
            "author_name": author["name"],
            "author_headline": author["headline"],
            "author_avatar": author["avatar"]
        })
    return enriched