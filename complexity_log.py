"""Print algorithm time/space complexity to the terminal when each runs."""

ALGORITHMS = {
    "merge_sort_feed": {
        "name": "Merge Sort - Feed Ranking",
        "time": "O(n log n)",
        "space": "O(n)",
    },
    "doubly_linked_list": {
        "name": "Doubly Linked List - Stories",
        "time": "O(n) build, O(k) navigate",
        "space": "O(n)",
    },
    "cosine_similarity": {
        "name": "Cosine Similarity + Insertion Sort - Similar Users",
        "time": "O(U * V + U^2)",
        "space": "O(U * V)",
    },
    "collaborative_filter": {
        "name": "Collaborative Filtering - Recommendations",
        "time": "O(U * V + U^2 + P)",
        "space": "O(P)",
    },
    "divide_conquer_trending": {
        "name": "Divide & Conquer - Trending Posts",
        "time": "O(k * P log P)",
        "space": "O(P)",
    },
    "bfs_connections": {
        "name": "BFS - Connection Suggestions",
        "time": "O(V + E)",
        "space": "O(V)",
    },
    "jaccard": {
        "name": "Jaccard Similarity - Network Overlap",
        "time": "O(d)",
        "space": "O(d)",
    },
    "skill_suggestions": {
        "name": "Set Intersection - Skill-Based Suggestions",
        "time": "O(U * S)",
        "space": "O(S)",
    },
    "mutual_friends": {
        "name": "Set Intersection - Mutual Friends",
        "time": "O(d_a + d_b)",
        "space": "O(d)",
    },
    "dfs_components": {
        "name": "DFS - Connected Components",
        "time": "O(V + E)",
        "space": "O(V)",
    },
    "skill_clusters": {
        "name": "Greedy Clustering + Cosine - Skill Clusters",
        "time": "O(U^2 * V)",
        "space": "O(U * V)",
    },
    "influence_hubs": {
        "name": "Adjacency Matrix - Influence Hubs",
        "time": "O(V^2 + E)",
        "space": "O(V^2)",
    },
}


def log_complexity(key, **metrics):
    info = ALGORITHMS.get(key)
    if not info:
        return

    line = "-" * 52
    print(f"\n{line}", flush=True)
    print(f"{info['name']}", flush=True)
    print(f"  Time:  {info['time']}", flush=True)
    print(f"  Space: {info['space']}", flush=True)
    if metrics:
        parts = "  ".join(f"{k}={v}" for k, v in metrics.items())
        print(f"  {parts}", flush=True)
    print(line, flush=True)
