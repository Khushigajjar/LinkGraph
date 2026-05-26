import json
import mysql.connector
from datetime import datetime

with open("dataset.json", "r") as f:
    raw = json.load(f)

users     = { user["id"]: user for user in raw["users"] }
adjacency = { user["id"]: user["connections"] for user in raw["users"] }

def get_all_posts():
    # start with JSON posts
    all_posts = []
    for post in raw["posts"]:
        p = dict(post)
        p["timestamp"] = datetime.fromisoformat(p["timestamp"])
        p["tags"]      = p.get("tags", [])
        p["shares"]    = p.get("shares", 0)
        p["source"]    = "json"
        all_posts.append(p)

    # add MySQL posts on top
    try:
        conn   = mysql.connector.connect(
            host="localhost", user="root", password="", database="linkgraph"
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM posts ORDER BY timestamp DESC")
        db_posts = cursor.fetchall()
        cursor.close()
        conn.close()

        for post in db_posts:
            all_posts.append({
                "id":        post["id"] + 10000,  # avoid id clash with JSON posts
                "author_id": post["author_id"],
                "content":   post["content"],
                "likes":     post["likes"],
                "comments":  post["comments"],
                "shares":    post["shares"],
                "timestamp": post["timestamp"],
                "tags":      [],
                "source":    "db"
            })
    except Exception as e:
        print(f"DB posts error: {e}")

    return all_posts



posts = get_all_posts()


def enrich_posts(post_list):
    enriched = []
    for post in post_list:
        author = users.get(post["author_id"])
        if not author:
            continue
        enriched.append({
            **post,
            "author_name":     author["name"],
            "author_headline": author["headline"],
            "author_avatar":   author["avatar"]
        })
    return enriched