import requests

def get_uuid(username: str) -> str | None:
    url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()["id"]
    return None