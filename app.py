from flask import Flask, jsonify, render_template, request, session, redirect, url_for
from flask import send_from_directory
from feed_ranking import get_ranked_feed, StoryList
from graph import (
    users, adjacency, posts, enrich_posts, add_session_post,
    update_post_engagement, add_post_comment, toggle_post_like,
    user_liked_post, DB_POST_OFFSET,
)
from content_recommendation import get_recommendations, get_trending_posts, find_similar_users
from community_detection import get_communities, find_influence_hubs, find_skill_clusters
from connection_finding import get_all_suggestions, get_mutual_friends, jaccard_similarity
from db import verify_login, get_current_user_id, get_connection
from graph import users as graph_users
from complexity_log import log_complexity, ALGORITHMS
import math

app = Flask(__name__)
app.secret_key = "linkgraph_secret_2026"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/templates/CSS/<path:filename>")
def template_css(filename):
    return send_from_directory("templates/CSS", filename)


@app.route("/me")
def me():
    user_id = session.get("user_id", 1)
    user = users[user_id]
    return jsonify({
        "id":               user["id"],
        "name":             user["name"],
        "avatar":           user["avatar"],
        "headline":         user["headline"],
        "company":          user["company"],
        "skills":           user["skills"],
        "connections_list": user["connections"]
    })


@app.route("/feed-page")
def feed_page():
    redir = require_login()
    if redir:
        return redir
    user = graph_users.get(session["user_id"])
    return render_template("feed.html", current_user=user)


@app.route("/connections/<int:user_id>")
def suggested_connections(user_id):
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404

    suggestions = [
        suggestion
        for suggestion in get_all_suggestions(user_id)
        if suggestion["source"] == "network"
    ]
    log_complexity("bfs_connections", user_id=user_id, suggestions=len(suggestions))
    return jsonify(suggestions)


@app.route("/users")
def get_users():
    user_list = []
    for user in users.values():
        user_list.append({
            "id":       user["id"],
            "name":     user["name"],
            "headline": user["headline"],
            "avatar":   user["avatar"],
            "company":  user["company"],
            "skills":   user["skills"],
            "connections": len(user["connections"])
        })
    return jsonify(user_list)


@app.route("/users/<int:user_id>")
def get_user(user_id):
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404

    user = users[user_id]
    return jsonify({
        "id":         user["id"],
        "name":       user["name"],
        "headline":   user["headline"],
        "avatar":     user["avatar"],
        "company":    user["company"],
        "skills":     user["skills"],
        "connections": len(user["connections"])
    })


@app.route("/stories")
def stories():
    story_list = StoryList()
    enriched   = enrich_posts(posts)

    for post in enriched:
        story_list.add_story(post)

    log_complexity("doubly_linked_list", n=len(enriched), index=request.args.get("index", 0, type=int))

    index = request.args.get("index", 0, type=int)
    story_list.current = story_list.head
    for _ in range(index):
        if story_list.current.next:
            story_list.current = story_list.current.next

    current = story_list.get_current()
    if not current:
        return jsonify({"error": "No stories"}), 404

    has_next = story_list.current.next is not None
    has_prev = story_list.current.prev is not None

    return jsonify({
        "index":    index,
        "has_next": has_next,
        "has_prev": has_prev,
        "post": {
            **current,
            "timestamp": current["timestamp"].strftime("%B %d, %Y")
        }
    })


@app.route("/recommendations")
def recommendations():
    user_id = session.get("user_id", 1)
    result = get_recommendations(user_id)
    log_complexity("collaborative_filter", user_id=user_id, results=len(result))
    log_complexity("divide_conquer_trending")
    return jsonify(result)


@app.route("/similar")
def similar_users_route():
    user_id = session.get("user_id", 1)
    result = find_similar_users(user_id)
    log_complexity("cosine_similarity", user_id=user_id, similar_users=len(result))
    return jsonify(result)


@app.route("/communities")
def communities():
    result = get_communities()
    log_complexity("dfs_components", components=len(result["connected_components"]))
    log_complexity("skill_clusters", clusters=len(result["skill_clusters"]))
    log_complexity("influence_hubs", hubs=len(result["influence_hubs"]))
    return jsonify(result)


@app.route("/hubs")
def hubs():
    result = find_influence_hubs()
    log_complexity("influence_hubs", hubs=len(result))
    return jsonify(result)


@app.route("/clusters")
def clusters():
    result = find_skill_clusters()
    log_complexity("skill_clusters", clusters=len(result))
    return jsonify(result)


@app.route("/suggestions")
def all_suggestions():
    user_id = session.get("user_id", 1)
    result = get_all_suggestions(user_id)
    network = sum(1 for s in result if s.get("source") == "network")
    skills = sum(1 for s in result if s.get("source") == "skills")
    log_complexity("bfs_connections", user_id=user_id, suggestions=network)
    log_complexity("skill_suggestions", suggestions=skills)
    return jsonify(result)


@app.route("/mutual/<int:user_id_a>/<int:user_id_b>")
def mutual(user_id_a, user_id_b):
    result = get_mutual_friends(user_id_a, user_id_b)
    log_complexity("mutual_friends", mutual=len(result))
    return jsonify(result)


@app.route("/feed")
def feed():
    user_id = session.get("user_id", 1)

    from graph import get_all_posts
    fresh_posts = get_all_posts()

    ranked, comparisons, elapsed = get_ranked_feed(
        user_id=user_id,
        post_list=fresh_posts
    )

    n           = len(ranked)
    theoretical = round(n * math.log2(n), 1) if n > 1 else 0

    for post in ranked:
        if hasattr(post["timestamp"], "strftime"):
            post["timestamp"] = post["timestamp"].strftime("%B %d, %Y")
        post["liked"] = user_liked_post(post["id"], session.get("user_id"))

    log_complexity(
        "merge_sort_feed",
        n=n,
        comparisons=comparisons,
        elapsed_ms=elapsed,
    )

    return jsonify({
        "posts": ranked,
        "stats": {
            "n":           n,
            "comparisons": comparisons,
            "theoretical": theoretical,
            "elapsed_ms":  elapsed,
            "algorithm":   "Merge Sort",
            "complexity":  "O(n log n)",
            "formula":     "engagement + network boost + shared-skill boost - recency penalty",
            "context":     "LinkedIn-style professional feed ranking"
        }
    })


@app.route("/post", methods=["POST"])
def create_post():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    content = request.json.get("content", "").strip()
    if not content:
        return jsonify({"error": "Content required"}), 400
    if len(content) > 1000:
        return jsonify({"error": "Too long"}), 400

    conn = get_connection()
    if conn is None:
        post = add_session_post(user_id, content)
        return jsonify({"success": True, "id": post["id"], "source": "session"})

    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO posts (author_id, content) VALUES (%s, %s)",
            (user_id, content)
        )
        conn.commit()
        new_id = cursor.lastrowid
    finally:
        cursor.close()
        conn.close()

    return jsonify({"success": True, "id": new_id + DB_POST_OFFSET, "db_id": new_id})


@app.route("/post/<int:post_id>/like", methods=["POST"])
def like_post(post_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    updated = toggle_post_like(post_id, user_id)
    if not updated:
        return jsonify({"error": "Post not found"}), 404

    return jsonify({
        "likes": updated["likes"],
        "liked": updated["liked"],
        "db_id": updated.get("db_id"),
        "source": updated.get("source"),
    })


@app.route("/post/<int:post_id>/comment", methods=["POST"])
def comment_post(post_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    content = (request.json or {}).get("content", "").strip()
    if not content:
        return jsonify({"error": "Comment required"}), 400
    if len(content) > 500:
        return jsonify({"error": "Comment too long"}), 400

    result = add_post_comment(post_id, user_id, content)
    if not result:
        return jsonify({"error": "Post not found"}), 404

    return jsonify({
        "comments": result["comments"],
        "comment": result["comment"],
        "success": True,
        "db_id": post_id - DB_POST_OFFSET if post_id >= DB_POST_OFFSET else None,
        "source": "db" if post_id >= DB_POST_OFFSET else "json",
    })


@app.route("/recommendations-page")
def recommendations_page():
    redir = require_login()
    if redir:
        return redir
    return render_template("recommendations.html")


@app.route("/connections-page")
def connections_page():
    redir = require_login()
    if redir:
        return redir
    return render_template("connections.html")


@app.route("/communities-page")
def communities_page():
    redir = require_login()
    if redir:
        return redir
    return render_template("communities.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "").strip()
        user_id  = verify_login(username, password)

        if user_id:
            session["user_id"] = user_id
            return redirect(url_for("feed_page"))
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def require_login():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return None


pending = set()


@app.route('/connect/send', methods=['POST'])
def send_request():
    data    = request.json
    from_id = data['from_id']
    to_id   = data['to_id']

    if (from_id, to_id) in pending:
        return jsonify({"status": "already_sent"})

    pending.add((from_id, to_id))
    return jsonify({"status": "sent"})


@app.route('/connect/accept', methods=['POST'])
def accept_request():
    data    = request.json
    from_id = data['from_id']
    to_id   = data['to_id']

    if (from_id, to_id) not in pending:
        return jsonify({"status": "no_request"})

    pending.discard((from_id, to_id))

    if to_id not in adjacency[from_id]:
        adjacency[from_id].append(to_id)
    if from_id not in adjacency[to_id]:
        adjacency[to_id].append(from_id)

    if to_id not in users[from_id]['connections']:
        users[from_id]['connections'].append(to_id)
    if from_id not in users[to_id]['connections']:
        users[to_id]['connections'].append(from_id)

    return jsonify({"status": "accepted"})


@app.route('/connect/pending/<int:user_id>')
def get_pending(user_id):
    incoming = [
        {"from_id": f, "name": users[f]['name'], "headline": users[f]['headline']}
        for (f, t) in pending if t == user_id
    ]
    return jsonify({"requests": incoming})


@app.route('/connect/reject', methods=['POST'])
def reject_request():
    data    = request.json
    from_id = data['from_id']
    to_id   = data['to_id']
    pending.discard((from_id, to_id))
    return jsonify({"status": "rejected"})


def _print_startup_complexity():
    print("\n" + "=" * 52, flush=True)
    print("  LinkGraph - Algorithm Complexity (terminal log)", flush=True)
    print("=" * 52, flush=True)
    for info in ALGORITHMS.values():
        print(f"  * {info['name']}", flush=True)
        print(f"      Time:  {info['time']}   Space: {info['space']}", flush=True)
    print("=" * 52 + "\n", flush=True)


if __name__ == "__main__":
    _print_startup_complexity()
    app.run(debug=True, use_reloader=False, port=5001)
