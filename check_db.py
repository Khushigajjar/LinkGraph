import mysql.connector

conn = mysql.connector.connect(
    host="localhost", user="root", password="", database="linkgraph"
)
cursor = conn.cursor()
cursor.execute("SELECT id, username, password FROM users LIMIT 10")
rows = cursor.fetchall()

for row in rows:
    print(f"id={row[0]}  username={row[1]}  password={row[2]}")

cursor.close()
conn.close()