from .he import MESSAGES as HE
from .en import MESSAGES as EN

LOCALES = {
    "he": HE,
    "en": EN,
}

def get_locale(language: str):
    return LOCALES.get(language, EN)


def translate(language: str, key: str) -> str:
    locale = get_locale(language)
    return locale.get(key, EN.get(key, key))
