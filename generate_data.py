import random
import json

names = [
    "Alex Morgan", "Emma Johnson", "Liam Smith", "Noah Williams", "Olivia Brown",
    "Ava Jones", "Sophia Miller", "Mason Davis", "Isabella Garcia", "Lucas Martinez",
    "Mia Rodriguez", "Ethan Wilson", "Amelia Anderson", "Harper Thomas", "Evelyn Taylor",
    "James Moore", "Benjamin Jackson", "Charlotte White", "Henry Harris", "Jack Martin",
    "William Thompson", "Elijah Lee", "Daniel Perez", "Matthew Clark", "Sebastian Lewis",
    "Leo Walker", "Grace Hall", "Hannah Allen", "Zoe Young", "Aria King",
    "Rohan Sharma", "Priya Patel", "Aarav Mehta", "Ishaan Verma", "Meera Iyer",
    "Ananya Nair", "Karan Malhotra", "Neha Gupta", "Aditya Rao", "Sara Khan",
    "Lina Kim", "David Scott", "Sophie Turner", "John Carter", "Michael Adams",
    "Chris Evans", "Tom Baker", "Anna Schmidt", "Julia Rossi", "Emma Clark"
]

skills_pool = [
    "Python", "Java", "C++", "SQL", "Machine Learning", "Data Science",
    "Deep Learning", "NLP", "Computer Vision", "Flask", "React",
    "Node.js", "Docker", "Kubernetes", "AWS", "Azure", "Algorithms",
    "Graphs", "Statistics", "Power BI"
]

def generate_users(n=50):
    users = []
    for i in range(n):
        name = names[i % len(names)] + f" {i}"
        skills = random.sample(skills_pool, k=random.randint(3, 6))
        connections = random.sample(
            [j for j in range(1, n+1) if j != i+1],
            k=random.randint(2, 4)
        )
        users.append({
            "id": i + 1,
            "name": name,
            "headline": f"{random.choice(skills)} Engineer",
            "company": random.choice(["Google", "Amazon", "Meta", "Microsoft", "Capgemini"]),
            "avatar": f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}",
            "skills": skills,
            "connections": connections
        })
    return users


def apply_followback(users, followback_rate=0.5):

    edges = set()
    for user in users:
        for neighbor_id in user["connections"]:
            edges.add((user["id"], neighbor_id))


    new_edges = set(edges)
    for (a, b) in edges:
        if (b, a) not in edges:
            if random.random() < followback_rate:
                new_edges.add((b, a))


    adjacency = {user["id"]: [] for user in users}
    for (a, b) in new_edges:
        adjacency[a].append(b)

    for user in users:
        user["connections"] = sorted(adjacency[user["id"]])

    return users


def generate_posts(users):
    posts = []
    for i in range(1, 51):
        user = random.choice(users)
        posts.append({
            "id": 100 + i,
            "author_id": user["id"],
            "content": f"Working on {random.choice(skills_pool)} project using AI + cloud systems.",
            "likes": random.randint(10, 500),
            "comments": random.randint(5, 120),
            "shares": random.randint(1, 80),
            "timestamp": "2026-04-28T10:00:00"
        })
    return posts


random.seed(42)
users = generate_users(50)
users = apply_followback(users, followback_rate=0.5)  
posts = generate_posts(users)

dataset = {"users": users, "posts": posts}

with open("dataset.json", "w") as f:
    json.dump(dataset, f, indent=2)

print("Dataset generated!")


total_follows = sum(len(u["connections"]) for u in users)
mutual = sum(
    1 for u in users for c in u["connections"]
    if u["id"] in next(x for x in users if x["id"] == c)["connections"]
)
print(f"Total follows: {total_follows}")
print(f"Mutual connections: {mutual // 2}")