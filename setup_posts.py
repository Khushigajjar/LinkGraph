import mysql.connector

conn = mysql.connector.connect(
    host="localhost", user="root", password="", database="linkgraph"
)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id         INT AUTO_INCREMENT PRIMARY KEY,
        author_id  INT NOT NULL,
        content    TEXT NOT NULL,
        likes      INT DEFAULT 0,
        comments   INT DEFAULT 0,
        shares     INT DEFAULT 0,
        timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

conn.commit()
cursor.close()
conn.close()
print("posts table created")