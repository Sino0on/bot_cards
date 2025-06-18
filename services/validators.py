import json

from decouple import config

from services.json_writer import load_data


def check_manager(user_id: int):
    print(user_id)
    try:
        with open("data.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        # print([user['id'] for user in data.get("managers", [])])
        # print()
        user = user_id in [user['id'] for user in data.get("managers", [])]
        # print(user)
        return user
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return False


def check_admin(user_id: int):
    data = load_data()  # ← загружаем из db.json
    admins = data.get("admins", [])
    return int(user_id) in admins
