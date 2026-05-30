import mysql.connector
import json

conn = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = ""
)
cursor = conn.cursor()

cursor.execute("CREATE DATABASE IF NOT EXISTS linkgraph")
cursor.execute("USE linkgraph")

cursor.execute(""" CREATE TABLE IF NOT EXISTS users (
        id       INT PRIMARY KEY,
        username VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(100) NOT NULL
    ) """)

with open("dataset.json", "r") as f:
    data = json.load(f)



inserted = 0
for user in data["users"]:
    username= user["name"].split()[0].lower()  
    password = f"linkgraph{user['id']}"         
    user_id = user["id"]

    try:
        cursor.execute(
            "INSERT INTO users (id, username, password) VALUES (%s, %s, %s)",
            (user_id, username, password)
        )
        inserted += 1
        print(f" id={user_id}  username={username}  password={password}")
    except mysql.connector.errors.IntegrityError:
        print(f"  — already exists: {username}")

conn.commit()
cursor.close()
conn.close()

print(f"\nDone — {inserted} users inserted into linkgraph.users")
print("Test login: username=alex  password=linkgraph1")