import mysql.connector

conn = mysql.connector.connect(
    host="localhost", user="root", password="", database="linkgraph"
)
cursor = conn.cursor()

cursor.execute(""" CREATE TABLE IF NOT EXISTS posts (
        id  INT AUTO_INCREMENT PRIMARY KEY,
        author_id  INT NOT NULL,
        content TEXT NOT NULL,
        likes INT DEFAULT 0,
        comments INT DEFAULT 0,
        shares INT DEFAULT 0,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    ) """)

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
print("posts table created")