import json
import os

DATA_PATH = "data.json"

def load_data():
    if not os.path.exists(DATA_PATH):
        return {"managers": []}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_manager(manager_id, name):
    data = load_data()
    # Проверка на дубликат
    for m in data["managers"]:
        if m["id"] == manager_id:
            return False  # уже существует
    data["managers"].append({
        "id": manager_id,
        "name": name,
        "cards": []
    })
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return True


def find_manager_by_user_id(user_id):
    data = load_data()
    for manager in data["managers"]:
        if manager["id"] == user_id:
            return manager
    return None


def add_card_to_manager(user_id, card_number):
    data = load_data()
    user_id_str = user_id

    for manager in data["managers"]:
        if manager["id"] == user_id_str:
            # Проверка на дубликаты
            for c in manager["cards"]:
                if c["card"] == card_number:
                    return False  # карта уже существует
            manager["cards"].append({
                "card": card_number,
                "money": 0
            })
            with open(DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
    return None  # менеджер не найден


def get_cards_for_manager(user_id):
    manager = find_manager_by_user_id(user_id)
    if manager:
        return manager["cards"]
    return None


def find_manager_by_card_number(card_number):
    data = load_data()
    for manager in data["managers"]:
        for card in manager["cards"]:
            if card["card"] in card_number:
                return manager
    return None


def add_money_to_card(card_number, amount):
    data = load_data()
    for manager in data["managers"]:
        for card in manager["cards"]:
            if card["card"] == card_number:
                card["money"] += amount
                with open(DATA_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                return True
    return False


def delete_card_for_manager(user_id, card_number):
    data = load_data()

    for manager in data["managers"]:
        if manager["id"] == user_id:
            for card in manager["cards"]:
                if card["card"] == card_number:
                    manager["cards"].remove(card)
                    with open(DATA_PATH, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    return True
    return False


