import json

from decouple import config


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
    try:
        admins = config('ADMINS').split(',')

        return str(user_id) in admins
    except:
        pass
    return False