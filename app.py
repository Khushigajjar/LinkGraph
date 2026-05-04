from flask import Flask, jsonify, render_template, request
from feed_ranking import get_ranked_feed, StoryList
from graph import users, adjacency, posts, enrich_posts
from content_recommendation import get_recommendations, get_trending_posts, find_similar_users
from datetime import datetime
from community_detection import get_communities, find_influence_hubs, find_skill_clusters
from connection_finding import get_all_suggestions, get_mutual_friends, jaccard_similarity


app = Flask(__name__)


# ──────────────────────────────────────────────────────────
# ROUTE 1: Home page
#
# Just renders the HTML template.
# The browser hits this first when you open the app.
# ──────────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")


# ──────────────────────────────────────────────────────────
# ROUTE 2: Get ranked feed
#
# Returns all posts sorted by engagement score.
# This is the core of Module 4 (Feed Ranking).
#
# URL: GET /feed
#
# Example response:
# [
#   { "id": 107, "score": 312.4, "author_name": "Thomas Bernard", ... },
#   { "id": 105, "score": 298.1, "author_name": "Bob Leclerc", ... },
#   ...
# ]
# ──────────────────────────────────────────────────────────

@app.route("/feed-page")
def feed_page(): 
    return render_template("feed.html") 



# ──────────────────────────────────────────────────────────
# ROUTE 3: Get suggested connections (Module 1 — BFS)
#
# Given a user_id, find people they are NOT connected to
# but share mutual connections with.
#
# URL: GET /connections/<user_id>
#
# Algorithm: BFS up to 2 degrees of separation
#   - Degree 1 = direct connections (skip these)
#   - Degree 2 = connections of connections (suggest these)
#
# Example: Khushi (id=1) is connected to Rahul (2) and Zijie (3)
#   Rahul is connected to Alice (4) → suggest Alice to Khushi
#   Zijie is connected to Bob (5)   → suggest Bob to Khushi
# ──────────────────────────────────────────────────────────

@app.route("/connections/<int:user_id>")
def suggested_connections(user_id):
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404

    # BFS setup
    visited    = set()       # users we have already explored
    queue      = [user_id]   # start from the given user
    direct     = set(adjacency[user_id])  # degree-1 connections
    suggestions = []         # degree-2 connections to suggest

    visited.add(user_id)

    # Level 1: visit direct connections
    for neighbor in adjacency[user_id]:
        visited.add(neighbor)

    # Level 2: visit connections-of-connections
    for neighbor in adjacency[user_id]:
        for second_degree in adjacency.get(neighbor, []):
            if (
                second_degree not in visited and
                second_degree != user_id and
                second_degree not in direct
            ):
                visited.add(second_degree)
                user = users[second_degree]
                suggestions.append({
                    "id":       user["id"],
                    "name":     user["name"],
                    "headline": user["headline"],
                    "avatar":   user["avatar"],
                    "company":  user["company"]
                })

    return jsonify(suggestions)


# ──────────────────────────────────────────────────────────
# ROUTE 4: Get all users
#
# Used by the UI to populate the sidebar / user switcher.
# URL: GET /users
# ──────────────────────────────────────────────────────────

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
            "skills":   user["skills"]
        })
    return jsonify(user_list)


# ──────────────────────────────────────────────────────────
# ROUTE 5: Get single user profile
#
# URL: GET /users/<user_id>
# Returns full profile info for one user.
# ──────────────────────────────────────────────────────────

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


# ──────────────────────────────────────────────────────────
# ROUTE 6: Stories navigation (doubly linked list)
#
# Builds a story list from recent posts and returns
# next/previous navigation.
#
# URL: GET /stories              → returns first story
# URL: GET /stories?index=2      → returns story at position 2
# ──────────────────────────────────────────────────────────

@app.route("/stories")
def stories():
    # Build the doubly linked list from all posts
    story_list = StoryList()
    enriched   = enrich_posts(posts)

    for post in enriched:
        story_list.add_story(post)

    
    index = request.args.get("index", 0, type=int)

    # Navigate to the requested position
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


@app.route("/recommendations/<int:user_id>")
def recommendations(user_id):
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404
    return jsonify(get_recommendations(user_id))


@app.route("/similar/<int:user_id>")
def similar_users(user_id):
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404
    return jsonify(find_similar_users(user_id))


@app.route("/communities")
def communities():
    return jsonify(get_communities())

@app.route("/hubs")
def hubs():
    return jsonify(find_influence_hubs())

@app.route("/clusters")
def clusters():
    return jsonify(find_skill_clusters())



@app.route("/suggestions/<int:user_id>")
def all_suggestions(user_id):
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404
    return jsonify(get_all_suggestions(user_id))

@app.route("/mutual/<int:user_id_a>/<int:user_id_b>")
def mutual(user_id_a, user_id_b):
    return jsonify(get_mutual_friends(user_id_a, user_id_b))


@app.route("/feed")
def feed():
    user_id = request.args.get("user_id", 1, type=int)
    ranked  = get_ranked_feed(user_id=user_id)

    for post in ranked:
        post["timestamp"] = post["timestamp"].strftime("%B %d, %Y")

    return jsonify(ranked)

@app.route("/recommendations-page")
def recommendations_page():
    return render_template("recommendations.html")

@app.route("/connections-page")
def connections_page():
    return render_template("connections.html")

@app.route("/communities-page")
def communities_page():
    return render_template("communities.html")  


if __name__ == "__main__":
    app.run(debug=True)