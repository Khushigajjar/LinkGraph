import json
from datetime import datetime
from db import get_connection

with open("dataset.json", "r") as f:
    raw = json.load(f)

users = {user["id"]: user for user in raw["users"]}
adjacency = {user["id"]: user["connections"] for user in raw["users"]}
session_posts = []


def _json_posts():
    all_posts = []
    for post in raw["posts"]:
        p = dict(post)
        p["timestamp"] = datetime.fromisoformat(p["timestamp"])
        p["tags"] = p.get("tags", [])
        p["shares"] = p.get("shares", 0)
        p["source"] = "json"
        all_posts.append(p)
    return all_posts


def _mysql_posts():
    conn = get_connection()
    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM posts ORDER BY timestamp DESC")
    db_posts = cursor.fetchall()
    cursor.close()
    conn.close()

    posts_from_db = []
    for post in db_posts:
        posts_from_db.append({
            "id": post["id"] + 10000,
            "author_id": post["author_id"],
            "content": post["content"],
            "likes": post.get("likes", 0),
            "comments": post.get("comments", 0),
            "shares": post.get("shares", 0),
            "timestamp": post["timestamp"],
            "tags": ["Career Update"],
            "source": "db"
        })
    return posts_from_db


def add_session_post(author_id, content):
    existing_ids = [post["id"] for post in _json_posts()] + [post["id"] for post in session_posts]
    post_id = (max(existing_ids) if existing_ids else 100) + 1
    post = {
        "id": post_id,
        "author_id": author_id,
        "content": content,
        "likes": 0,
        "comments": 0,
        "shares": 0,
        "timestamp": datetime.now(),
        "tags": ["Career Update"],
        "source": "session"
    }
    session_posts.insert(0, post)
    return post


def get_all_posts():
    return session_posts + _json_posts() + _mysql_posts()


posts = get_all_posts()


def enrich_posts(post_list):
    enriched = []
    for post in post_list:
        author = users.get(post["author_id"])
        if not author:
            continue
        enriched.append({
            **post,
            "author_name": author["name"],
            "author_headline": author["headline"],
            "author_avatar": author["avatar"]
        })
    return enriched
