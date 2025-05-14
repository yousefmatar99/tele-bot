from pymongo import MongoClient

import random
import logging

client = MongoClient("mongodb://localhost:27017/")
db = client["not_a_db"]

users_collection = db["users"]
queues_collection = db["queues"]
states_collection = db["states"]

logging.basicConfig(
    format="[%(levelname)s %(asctime)s %(module)s:%(lineno)d] %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

###
#  USER FUNCTIONS
###


def create_user(user_id: int, chat_id: int, user_name: str, emoji: str) -> dict:
    new_user = {
        "user_id": user_id,
        "chat_id": chat_id,
        "user_name": user_name,
        "emoji": emoji,
        "score": {
            "Tic-Tac-Toe": 0,
            "4-In-A-Row": 0,
            "Trivia": 0,
            "rock-paper-scissors": 0,
        },
    }
    users_collection.insert_one(new_user)
    return new_user


def get_user_info(field_name: str, field_value) -> dict:
    query = {field_name: field_value}
    user = users_collection.find_one(query)
    if user:
        user.pop("_id", None)
    return user


def update_user_info(user_id: int, update_fields: dict) -> dict:
    query = {"user_id": user_id}
    new_values = {"$set": update_fields}
    result = users_collection.update_one(query, new_values)
    if result.matched_count == 0:
        return None
    updated_user = users_collection.find_one(query)
    updated_user.pop("_id", None)
    return updated_user


def delete_user(user_id: int) -> None:
    users_collection.delete_one({"user_id": user_id})


def inc_score(user_id: int, add: int, game_type: str) -> None:
    user = get_user_info("user_id", user_id)
    if not user:
        return
    orig = user["score"].get(game_type, 0)
    new_score = orig + add

    update_user_info(user_id, {f"score.{game_type}": new_score})


def getEmoji(user_id: int) -> str:
    user = get_user_info("user_id", user_id)
    return user["emoji"]


def get_top_scorers(game_type: str, top_n: int = 3) -> list:
    top_players = (
        users_collection.find(
            {f"score.{game_type}": {"$exists": True}},
            {"user_name": 1, f"score.{game_type}": 1, "_id": 0},
        )
        .sort(f"score.{game_type}", -1)
        .limit(top_n)
    )

    return [
        f"{player['user_name']} - {player['score'][game_type]}"
        for player in top_players
    ]


###
#  QUEUE FUNCTIONS
###


def create_queue(user_id, chat_id, game_type) -> dict:
    new_queue = {"user_id": user_id, "chat_id": chat_id, "game_type": game_type}
    queues_collection.insert_one(new_queue)
    return new_queue


def get_queue_info(field_name: str, field_value) -> dict:
    query = {field_name: field_value}
    queue = queues_collection.find_one(query)
    if queue:
        queue.pop("_id", None)
    return queue


def delete_queue(user_id) -> None:
    queues_collection.delete_one({"user_id": user_id})


###
#  STATE FUNCTIONS
###


def create_state(user1_id: int, user2_id: int, game_type: str, state: object) -> dict:
    user1 = get_user_info("user_id", user1_id)
    user2 = get_user_info("user_id", user2_id)
    new_state = {
        "user_id_arr": [user1["user_id"], user2["user_id"]],
        "game_type": game_type,
        "turn": random.choice([0, 1]),
        "state": state,
    }
    states_collection.insert_one(new_state)
    return new_state


def get_state_info_by_ID(user_id: int) -> dict:
    query = {"user_id_arr": {"$in": [user_id]}}
    state = states_collection.find_one(query)
    if state:
        state.pop("_id", None)
    return state


def update_state_info(user_id: int, update_fields: dict) -> dict:
    query = {"user_id_arr": {"$in": [user_id]}}
    new_values = {"$set": update_fields}
    result = states_collection.update_one(query, new_values)
    if result.matched_count == 0:
        return None
    updated_state = states_collection.find_one(query)
    updated_state.pop("_id", None)
    return updated_state


def delete_state(user_id: int) -> None:
    states_collection.delete_one({"user_id_arr": {"$in": [user_id]}})


def is_single(user_id: int) -> bool:
    query = {"user_id_arr": {"$in": [user_id]}}
    state = get_state_info_by_ID(query)
    return state["user_id_arr"][0] is None or state["user_id_arr"][1] is None
