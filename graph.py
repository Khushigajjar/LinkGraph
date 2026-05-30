import json
from datetime import datetime
from db import get_connection

with open("dataset.json", "r") as f:
    raw = json.load(f)

users = {user["id"]: user for user in raw["users"]}
adjacency = {user["id"]: user["connections"] for user in raw["users"]}
session_posts = []

DB_POST_OFFSET = 10000


def _safe_int(value, default=0):
    if value is None:
        return default
    return int(value)


def _persist_json():
    with open("dataset.json", "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2)


def ensure_engagement_tables():
    conn = get_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()
        cursor.execute(""" CREATE TABLE IF NOT EXISTS post_comments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            post_id INT NOT NULL,
            user_id INT NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) """)
        cursor.execute(""" CREATE TABLE IF NOT EXISTS post_likes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            post_id INT NOT NULL,
            user_id INT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_like (post_id, user_id)
        ) """)
        cursor.execute(""" CREATE TABLE IF NOT EXISTS post_engagement (
            post_id INT PRIMARY KEY,
            likes INT DEFAULT 0,
            comments INT DEFAULT 0
        ) """)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"engagement tables error: {e}")


def _load_engagement_overrides():
    overrides = {}
    conn = get_connection()
    if conn is None:
        return overrides

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT post_id, likes, comments FROM post_engagement")
        for row in cursor.fetchall():
            overrides[row["post_id"]] = row
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"post_engagement read error: {e}")

    return overrides


def user_liked_post(post_id, user_id):
    if not user_id:
        return False

    conn = get_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM post_likes WHERE post_id = %s AND user_id = %s LIMIT 1",
            (post_id, user_id),
        )
        liked = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return liked
    except Exception as e:
        print(f"post_likes read error: {e}")
        return False


def _json_posts():
    engagement = _load_engagement_overrides()
    all_posts = []

    for post in raw["posts"]:
        p = dict(post)
        p["timestamp"] = datetime.fromisoformat(p["timestamp"])
        p["tags"] = p.get("tags", [])
        p["shares"] = _safe_int(p.get("shares"))
        p["likes"] = _safe_int(p.get("likes"))
        p["comments"] = _safe_int(p.get("comments"))
        if p["id"] in engagement:
            p["likes"] = _safe_int(engagement[p["id"]].get("likes"))
            p["comments"] = _safe_int(engagement[p["id"]].get("comments"))
        p["source"] = "json"
        p["db_id"] = None
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
            "id": post["id"] + DB_POST_OFFSET,
            "db_id": post["id"],
            "author_id": post["author_id"],
            "content": post["content"],
            "likes": _safe_int(post.get("likes")),
            "comments": _safe_int(post.get("comments")),
            "shares": _safe_int(post.get("shares")),
            "timestamp": post["timestamp"],
            "tags": ["Career Update"],
            "source": "db",
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
        "source": "session",
        "db_id": None,
    }
    session_posts.insert(0, post)
    return post


def get_all_posts():
    return session_posts + _json_posts() + _mysql_posts()


def get_comments_for_post(post_id):
    comments = []

    if post_id >= DB_POST_OFFSET:
        db_id = post_id - DB_POST_OFFSET
        conn = get_connection()
        if conn is None:
            return comments

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """SELECT pc.content, pc.user_id, pc.created_at, u.username
                   FROM post_comments pc
                   LEFT JOIN users u ON u.id = pc.user_id
                   WHERE pc.post_id = %s
                   ORDER BY pc.created_at ASC""",
                (db_id,),
            )
            for row in cursor.fetchall():
                author = users.get(row["user_id"])
                comments.append({
                    "author_name": author["name"] if author else row.get("username", "Member"),
                    "content": row["content"],
                    "created_at": row["created_at"].strftime("%b %d, %Y %I:%M %p")
                    if hasattr(row["created_at"], "strftime")
                    else str(row["created_at"]),
                })
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"DB comments read error: {e}")
    else:
        for entry in raw.get("post_comments", []):
            if entry.get("post_id") != post_id:
                continue
            author = users.get(entry.get("user_id"))
            comments.append({
                "author_name": entry.get("author_name") or (author["name"] if author else "Member"),
                "content": entry["content"],
                "created_at": entry.get("created_at", ""),
            })

    return comments


def load_mysql_users():
    conn = get_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username FROM users")
        db_users = cursor.fetchall()
        cursor.close()
        conn.close()

        for u in db_users:
            if u["id"] not in users:
                users[u["id"]] = {
                    "id": u["id"],
                    "name": u["username"],
                    "headline": "LinkGraph Member",
                    "avatar": f"https://ui-avatars.com/api/?name={u['username']}",
                    "company": "",
                    "skills": [],
                    "connections": [],
                }
                adjacency[u["id"]] = []
    except Exception as e:
        print(f"DB users error: {e}")


ensure_engagement_tables()
load_mysql_users()

posts = get_all_posts()


def update_post_engagement(post_id, likes_delta=0, comments_delta=0):
    global posts
    posts = get_all_posts()

    target = None
    for post in posts:
        if post["id"] == post_id:
            target = post
            break

    if not target:
        return None

    if likes_delta:
        target["likes"] = max(0, _safe_int(target.get("likes")) + likes_delta)
    if comments_delta:
        target["comments"] = max(0, _safe_int(target.get("comments")) + comments_delta)

    if target.get("source") == "db":
        db_id = post_id - DB_POST_OFFSET
        conn = get_connection()
        if conn is None:
            return None

        try:
            cursor = conn.cursor()
            if likes_delta:
                cursor.execute(
                    "UPDATE posts SET likes = %s WHERE id = %s",
                    (target["likes"], db_id),
                )
            if comments_delta:
                cursor.execute(
                    "UPDATE posts SET comments = %s WHERE id = %s",
                    (target["comments"], db_id),
                )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"DB engagement update error: {e}")
            return None
    else:
        conn = get_connection()
        if conn is None:
            for post in raw["posts"]:
                if post["id"] == post_id:
                    if likes_delta:
                        post["likes"] = target["likes"]
                    if comments_delta:
                        post["comments"] = target["comments"]
                    break
            _persist_json()
            return target

        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO post_engagement (post_id, likes, comments)
                   VALUES (%s, %s, %s)
                   ON DUPLICATE KEY UPDATE
                   likes = VALUES(likes),
                   comments = VALUES(comments)""",
                (post_id, target["likes"], target["comments"]),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"post_engagement update error: {e}")
            return None

    return target


def toggle_post_like(post_id, user_id):
    global posts
    posts = get_all_posts()

    target = None
    for post in posts:
        if post["id"] == post_id:
            target = post
            break

    if not target:
        return None

    conn = get_connection()
    if conn is None:
        return None

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id FROM post_likes WHERE post_id = %s AND user_id = %s",
            (post_id, user_id),
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                "DELETE FROM post_likes WHERE post_id = %s AND user_id = %s",
                (post_id, user_id),
            )
            likes_delta = -1
            liked = False
        else:
            cursor.execute(
                "INSERT INTO post_likes (post_id, user_id) VALUES (%s, %s)",
                (post_id, user_id),
            )
            likes_delta = 1
            liked = True

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"post_likes toggle error: {e}")
        return None

    updated = update_post_engagement(post_id, likes_delta=likes_delta)
    if not updated:
        return None

    return {**updated, "liked": liked}


def add_post_comment(post_id, user_id, content):
    author = users.get(user_id)
    author_name = author["name"] if author else "Member"
    created_at = datetime.now().strftime("%b %d, %Y %I:%M %p")

    updated = update_post_engagement(post_id, comments_delta=1)
    if not updated:
        return None

    if post_id >= DB_POST_OFFSET:
        db_id = post_id - DB_POST_OFFSET
        conn = get_connection()
        if conn is None:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO post_comments (post_id, user_id, content) VALUES (%s, %s, %s)",
                (db_id, user_id, content),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"DB comment insert error: {e}")
            return None
    else:
        raw.setdefault("post_comments", []).append({
            "post_id": post_id,
            "user_id": user_id,
            "author_name": author_name,
            "content": content,
            "created_at": created_at,
        })
        _persist_json()

    return {
        "comments": updated["comments"],
        "comment": {
            "author_name": author_name,
            "content": content,
            "created_at": created_at,
        },
    }


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
            "author_avatar": author["avatar"],
            "recent_comments": get_comments_for_post(post["id"]),
        })
    return enriched
