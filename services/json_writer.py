import json
import os

DATA_PATH = "data.json"

def load_data():
    if not os.path.exists(DATA_PATH):
        return {"managers": []}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data: dict):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_manager(manager_id, name):
    data = load_data()
    # Проверка на дубликат
    for m in data["managers"]:
        if m["id"] == manager_id:
            return False  # уже существует
    data["managers"].append({
        "id": manager_id,
        "name": name,
        "status": True,
        "balance": 0.0,
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


def check_card_to_manager(user_id, card_number):
    data = load_data()
    user_id_str = user_id

    for manager in data["managers"]:
        if manager["id"] == user_id_str:
            # Проверка на дубликаты
            for c in manager["cards"]:
                if c["card"] == card_number:
                    return False  # карта уже существует
            return True
    return None  # менеджер не найден

def add_card_to_manager(user_id, card_number, fio):
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
                "full_name": fio,
                "active": True,
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


def add_money_to_card(user_id, card_number, amount):
    data = load_data()

    for manager in data["managers"]:
        if manager["id"] == user_id:
            for card in manager["cards"]:
                if card["card"] == card_number:
                    card["money"] += amount
                    with open(DATA_PATH, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    return True
    return False  # если не найдено


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


def delete_manager_by_id(manager_id):
    data = load_data()
    updated = [m for m in data["managers"] if m["id"] != manager_id]

    if len(updated) == len(data["managers"]):
        return False  # не найден

    data["managers"] = updated
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return True

def edit_card_number(user_id, old_card_number, new_card_number):
    data = load_data()
    user_id = str(user_id)

    for manager in data["managers"]:
        if manager["id"] == user_id:
            for card in manager["cards"]:
                if card["card"] == old_card_number:
                    card["card"] = new_card_number
                    with open(DATA_PATH, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    return True
    return False


def assign_operators_to_chat(chat_id, operator_ids):
    data = load_data()
    for chat in data.get("chats", []):
        if chat["id"] == chat_id:
            current = set(chat.get("managers", []))
            chat["managers"] = list(current.union(set(operator_ids)))
            with open(DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
    return False


def add_chat(chat_id, title):
    data = load_data()
    existing = next((c for c in data.get("chats", []) if c["id"] == chat_id), None)
    if existing:
        return False  # уже есть

    data.setdefault("chats", []).append({
        "id": chat_id,
        "name": title,
        "status": True,
        "managers": [],
        "transactions": []
    })
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return True


def get_all_chats():
    data = load_data()
    return data.get("chats", [])


def toggle_chat_status(chat_id):
    data = load_data()
    for chat in data.get("chats", []):
        if chat["id"] == chat_id:
            chat["status"] = not chat.get("status", True)
            with open(DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return chat["status"]
    return None


def delete_chat(chat_id):
    data = load_data()
    before = len(data.get("chats", []))
    data["chats"] = [c for c in data["chats"] if c["id"] != chat_id]
    after = len(data["chats"])
    if before == after:
        return False
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return True


def get_chat_status(chat_id):
    data = load_data()
    for chat in data.get("chats", []):
        if chat["id"] == chat_id:
            return chat.get("status", True)  # по умолчанию считаем, что включён
    return None  # если чат не найден

def get_operators_balances():
    data = load_data()
    results = []
    for manager in data["managers"]:
        total = sum(card["money"] for card in manager.get("cards", []))
        results.append({
            "id": manager["id"],
            "name": manager["name"],
            "balance": total
        })
    return results


def get_chats_balances():
    data = load_data()
    results = []
    for chat in data.get("chats", []):
        total = sum(tx["money"] for tx in chat.get("transactions", []))
        results.append({
            "id": chat["id"],
            "name": chat["name"],
            "balance": total
        })
    return results



from datetime import datetime


def add_transaction(chat_id, msg_id, operator_id, card_number, money):
    data = load_data()
    for chat in data.get("chats", []):
        print(chat["id"], chat_id)
        if chat["id"] == chat_id:
            chat.setdefault("transactions", []).append({
                "msg_id": msg_id,
                "operator": operator_id,
                "card": card_number,
                "money": money,
                "timestamp": datetime.now().isoformat()
            })
            with open(DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
    return False


from datetime import datetime, timedelta

def get_transactions_by_operator(operator_id, days=None):
    data = load_data()
    operator_id = int(operator_id)
    result = []

    now = datetime.now()
    for chat in data.get("chats", []):
        for tx in chat.get("transactions", []):
            if tx["operator"] != operator_id:
                continue

            # Если нужно фильтровать по дате
            if days is not None:
                tx_time = datetime.fromisoformat(tx["timestamp"])
                if tx_time < now - timedelta(days=days):
                    continue

            result.append({
                "chat_name": chat["name"],
                "msg_id": tx["msg_id"],
                "card": tx.get("card", "-"),
                "amount": tx["money"],
                "timestamp": tx["timestamp"]
            })
    return result

# from utils.json_utils import load_data

def get_active_chat_ids() -> list[int]:
    data = load_data()
    chats = data.get("chats", [])
    return [chat["id"] for chat in chats if chat.get("status") is True]


def get_settings() -> dict:
    data = load_data()
    return data.get("settings", {})


def update_address(new_address: str):
    data = load_data()
    data.setdefault("settings", {})["address"] = new_address
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def update_address_set(new_address: str):
    data = load_data()
    data.setdefault("settings", {})["address_set"] = new_address
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def update_limit(new_limit: float):
    data = load_data()
    data.setdefault("settings", {})["limit"] = new_limit
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def update_procent(new_limit: float):
    data = load_data()
    data.setdefault("settings", {})["procent"] = new_limit
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def update_procent_bonus(new_limit: float):
    data = load_data()
    data.setdefault("settings", {})["procent_bonus"] = new_limit
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_usdt_rate() -> float:
    data = load_data()
    return data.get("settings", {}).get("usdt_rate", 89.0)


def update_usdt_rate(rate: float):
    data = load_data()
    data.setdefault("settings", {})["usdt_rate"] = rate
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def set_manager_status(manager_id: int, status: bool):
    data = load_data()
    for manager in data.get("managers", []):
        if str(manager["id"]) == str(manager_id):
            manager["status"] = status
            break
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_manager_status(manager_id: int) -> bool:
    data = load_data()
    for manager in data.get("managers", []):
        if str(manager["id"]) == str(manager_id):
            return manager.get("status", True)
    return False


def get_manager_cards(manager_id: int):
    data = load_data()
    for manager in data["managers"]:
        if str(manager["id"]) == str(manager_id):
            return manager.get("cards", [])
    return []


def create_round_request(operator_id, usd, ltc, address, deadline):
    data = load_data()
    req_id = len(data.get("round_requests", [])) + 1
    new_req = {
        "id": req_id,
        "operator_id": operator_id,
        "usd": usd,
        "ltc": ltc,
        "address": address,
        "deadline": deadline.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pending"
    }
    data.setdefault("round_requests", []).append(new_req)

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return req_id


def clear_cards_balance(operator_id):
    data = load_data()

    for manager in data.get("managers", []):
        if manager["id"] == operator_id:
            for card in manager.get("cards", []):
                card["money"] = 0

    save_data(data)


def get_request_by_id(request_id: int):
    data = load_data()
    for req in data.get("round_requests", []):
        if req["id"] == request_id:
            return req
    return None

def update_request_status(request_id: int, status: str):
    data = load_data()
    for req in data.get("requests", []):
        if req["id"] == request_id:
            req["status"] = status
            save_data(data)
            return True
    return False

def credit_operator_bonus(operator_id: int, bonus: float):
    data = load_data()
    for manager in data.get("managers", []):
        if manager["id"] == operator_id:
            manager["balance"] = manager.get("balance", 0) + bonus
            save_data(data)
            return True
    return False


def set_operator_active(operator_id: int, active: bool):
    data = load_data()
    for manager in data.get("managers", []):
        if manager["id"] == operator_id:
            manager["active"] = active
            save_data(data)
            return True
    return False


def get_operator_bonus_balance(user_id: int) -> float:
    data = load_data()
    for manager in data.get("managers", []):
        if manager["id"] == user_id:
            return round(manager.get("balance", 0), 2)
    return 0.0


def get_chat_by_id(chat_id: int):
    data = load_data()
    if str(chat_id)[:4] == '-100':
        chat_id = abs(int(str(chat_id)[4:]))
    for chat in data.get("chats", []):
        if chat["id"] == abs(chat_id):
            return chat
    return None


def update_chat(chat_id: int, updated_chat: dict):
    data = load_data()
    for i, chat in enumerate(data.get("chats", [])):
        if chat["id"] == abs(chat_id):
            data["chats"][i] = updated_chat
            save_data(data)
            return True
    return False


from datetime import datetime

def add_group_withdraw_request(chat_id, chat_name, transactions, rate, company_cut, operator_bonuses, final_usd):
    data = load_data()

    for chat in data.get("chats", []):
        if chat["id"] == chat_id:
            # Сумма в USD (до комиссии)
            full_usd = round(sum(tx["money"] for tx in transactions) / rate, 2)

            # Добавляем к балансу
            chat["all_balance"] = round(chat.get("all_balance", 0) + full_usd, 2)
            chat["balance"] = round(chat.get("balance", 0) + final_usd, 2)
            break

    requests = data.setdefault("requests", [])
    request_id = len(requests) + 1

    total_kgs = sum(tx["money"] for tx in transactions)
    operator_list = []
    for op_id, (kgs, bonus) in operator_bonuses.items():
        manager = find_manager_by_user_id(op_id)
        name = manager.get("name") if manager else "unknown"
        operator_list.append({
            "id": op_id,
            "name": name,
            "kgs": kgs,
            "bonus_usd": bonus
        })

    new_request = {
        "id": request_id,
        "type": "group_withdraw",
        "chat_id": chat_id,
        "chat_name": chat_name,
        "amount_kgs": total_kgs,
        "amount_usd": round(total_kgs / rate, 2),
        "rate": rate,
        "company_cut": company_cut,
        "operator_bonus_total": round(company_cut / 2, 8),
        "final_amount_usd": final_usd,
        "timestamp": datetime.now().isoformat(),
        "status": "done",
        "operators": operator_list
    }

    requests.append(new_request)
    save_data(data)


def get_chats_with_names():
    data = load_data()
    return [{"id": chat["id"], "name": chat.get("name", "Без имени")} for chat in data.get("chats", [])]

def get_chat_by_name(name):
    for chat in load_data().get("chats", []):
        if chat.get("name") == name:
            return chat
    return None

def add_operator_to_chat(chat_id, operator_id):
    data = load_data()
    for chat in data["chats"]:
        if chat["id"] == chat_id:
            if operator_id not in chat["managers"]:
                chat["managers"].append(operator_id)
                save_data(data)
                return True
    return False


def remove_operator_from_chat(chat_id, operator_id):
    data = load_data()
    for chat in data["chats"]:
        if chat["id"] == chat_id and operator_id in chat["managers"]:
            chat["managers"].remove(operator_id)
            save_data(data)
            return True
    return False

def get_manager_name_by_id(user_id):
    for m in load_data().get("managers", []):
        if m["id"] == user_id:
            return m.get("name")
    return None


def get_all_managers():
    data = load_data()
    return data.get("managers", [])


def deduct_from_card(user_id, card_number, amount):
    data = load_data()
    for manager in data.get("managers", []):
        if manager["id"] == user_id:
            for card in manager.get("cards", []):
                if card["card"] == card_number:
                    card["money"] = max(card["money"] - amount, 0)
                    break
    save_data(data)


def get_formatted_cards(user_id: int):
    data = load_data()
    for manager in data.get("managers", []):
        if manager["id"] == user_id:
            cards = manager.get("cards", [])
            return [card['card'][-4:] for card in cards]
    return []


def get_user_by_id(user_id: int):
    data = load_data()
    for manager in data.get("managers", []):
        if manager["id"] == user_id:
            return manager
    return None


def get_cards(user_id: int):
    data = load_data()
    for manager in data.get("managers", []):
        if manager["id"] == user_id:
            cards = manager.get("cards", [])
            return [card['card'] for card in cards if card['active']]
    return []

def find_fullname_by_card(card_arg: str):
    data = load_data()
    for manager in data.get("managers", []):
        for card in manager['cards']:
            if card['card'] == card_arg:
                return card['full_name']
    return ''


def toggle_card_status(user_id, card_number):
    data = load_data()
    for manager in data.get("managers", []):
        if manager["id"] == user_id:
            for card in manager.get("cards", []):
                if card["card"] == card_number:
                    card["active"] = not card.get("active", True)
                    save_data(data)
                    return card["active"]
    return None


def update_chat_settings(chat_id, param, value):
    data = load_data()
    for chat in data.get("chats", []):
        if chat["id"] == chat_id:
            settings = chat.setdefault("settings", {})
            if param == "set_rate":
                settings["usdt_rate"] = value
            elif param == "set_procent":
                settings["procent"] = value
            elif param == "set_bonus":
                settings["procent_bonus"] = value
            elif param == "set_address":
                settings["address"] = value
            elif param == "set_address_set":
                settings["address_set"] = value
            break
    save_data(data)
