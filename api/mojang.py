import requests

def get_uuid(username: str) -> str | None:
    url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()["id"]
        return None
    except Exception as e:
        print(f"Ошибка Mojang: {e}")
        return None