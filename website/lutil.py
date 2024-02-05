def normalize_email(email: str) -> str:
    return email.strip().lower()


def rekey_dict(dictionary: dict, keys: list[tuple[str, str]]):
    for key_from, key_to in keys:
        dictionary[key_to] = dictionary.pop(key_from)
