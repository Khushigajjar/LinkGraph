import mysql.connector
from flask import session

def get_connection():
    return mysql.connector.connect(
        host     = "localhost",
        user     = "root",        
        password = "",            
        database = "linkgraph"
    )


def verify_login(username, password):
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id FROM users WHERE username = %s AND password = %s",
        (username, password)
    )

    user = cursor.fetchone()
    cursor.close()
    conn.close()

    return user["id"] if user else None


def get_current_user_id():
    return session.get("user_id")