# src/utils/states.py
from collections import defaultdict


user_states = defaultdict(dict)          # state فعلی
user_history = defaultdict(list)        # تاریخچه stateها (stack)
# ساختار: user_states[user_id] = {'state': str, 'data': dict}
user_states = defaultdict(dict)

def set_state(user_id: int, state: str, data: dict = None):
    user_states[user_id]['state'] = state
    if data is not None:
        user_states[user_id]['data'] = data or {}
    elif 'data' in user_states[user_id]:
        user_states[user_id]['data'] = {}

def get_state(user_id: int) -> str | None:
    return user_states.get(user_id, {}).get('state')

def get_state_data(user_id: int, key: str = None):
    data = user_states.get(user_id, {}).get('data', {})
    return data.get(key) if key else data

def update_state_data(user_id: int, key: str, value):
    if user_id in user_states and 'data' in user_states[user_id]:
        user_states[user_id]['data'][key] = value

def append_to_state_list(user_id: int, key: str, item):
    data = get_state_data(user_id)
    lst = data.get(key, [])
    lst.append(item)
    update_state_data(user_id, key, lst)

def clear_state(user_id: int):
    user_states.pop(user_id, None)
    
    


def set_state(user_id: int, state: str, data: dict = None):
    # ذخیره state قبلی در history (اگر وجود داشت)
    current = user_states.get(user_id, {})
    if current.get('state'):
        user_history[user_id].append(current)

    # تنظیم state جدید
    user_states[user_id]['state'] = state
    user_states[user_id]['data'] = data or {}


def back_state(user_id: int):
    """برگشت به state قبلی"""
    if user_id in user_history and user_history[user_id]:
        previous = user_history[user_id].pop()  # آخرین state رو برمی‌گردونیم
        user_states[user_id] = previous
        return previous['state'], previous.get('data', {})
    return None, None


def clear_state(user_id: int):
    user_states.pop(user_id, None)
    user_history.pop(user_id, None)


def get_state(user_id: int) -> str | None:
    return user_states.get(user_id, {}).get('state')


def get_state_data(user_id: int, key: str = None):
    data = user_states.get(user_id, {}).get('data', {})
    return data.get(key) if key else data