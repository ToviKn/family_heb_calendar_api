from .he import MESSAGES as HE
from .en import MESSAGES as EN

LOCALES = {
    "he": HE,
    "en": EN,
}

def get_locale(language: str):
    return LOCALES.get(language, EN)