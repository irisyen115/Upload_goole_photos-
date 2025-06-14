# session_utils.py
import os
import json

def load_session(user_id):
    path = f"sessions/{user_id}.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_session(user_id, data):
    path = f"sessions/{user_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
