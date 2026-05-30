import json
import mysql.connector
from flask import session

_mysql_warning_printed = False


def _print_mysql_fallback_once():
    global _mysql_warning_printed
    if not _mysql_warning_printed:
        print("MySQL not available, using JSON fallback.")
        _mysql_warning_printed = True


def get_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="linkgraph",
            connection_timeout=2
        )
    except mysql.connector.Error:
        _print_mysql_fallback_once()
        return None


def _verify_login_from_json(username, password):
    try:
        with open("dataset.json", "r") as f:
            data = json.load(f)
    except OSError:
        return None

    for user in data.get("users", []):
        expected_username = user["name"].split()[0].lower()
        expected_password = f"linkgraph{user['id']}"
        if username == expected_username and password == expected_password:
            return user["id"]

    return None


def verify_login(username, password):
    conn = get_connection()
    if conn is None:
        return _verify_login_from_json(username, password)

    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id FROM users WHERE username = %s AND password = %s",
        (username, password)
    )

    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        return user["id"]

    return _verify_login_from_json(username, password)


def get_current_user_id():
    return session.get("user_id")
