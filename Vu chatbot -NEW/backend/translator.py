from deep_translator import GoogleTranslator

# =========================
# 🇮🇳 22 OFFICIAL LANGUAGES
# =========================
INDIAN_LANGS = {
    "as": "Assamese",
    "bn": "Bengali",
    "brx": "Bodo",
    "doi": "Dogri",
    "gu": "Gujarati",
    "hi": "Hindi",
    "kn": "Kannada",
    "ks": "Kashmiri",
    "gom": "Konkani",
    "mai": "Maithili",
    "ml": "Malayalam",
    "mni": "Manipuri",
    "mr": "Marathi",
    "ne": "Nepali",
    "or": "Odia",
    "pa": "Punjabi",
    "sa": "Sanskrit",
    "sat": "Santali",
    "sd": "Sindhi",
    "ta": "Tamil",
    "te": "Telugu",
    "ur": "Urdu"
}

def get_language_name(code):
    return INDIAN_LANGS.get(code, "English" if code == "en" else code)


# =========================
# 🌍 DETECT LANGUAGE
# =========================
def detect_language(text):
    try:
        from engine import detect_language_ai
        return detect_language_ai(text)
    except:
        return "en"



# =========================
# 🌍 TRANSLATE TO ENGLISH
# =========================
def to_english(text):
    try:
        translated = GoogleTranslator(
            source='auto',
            target='en'
        ).translate(text)

        return translated if translated else text

    except:
        return text


# =========================
# 🌍 TRANSLATE FROM ENGLISH
# =========================
def from_english(text, target_lang):
    try:
        # skip if already English
        if target_lang == "en":
            return text

        # 🔥 Skip if the text already contains non-ASCII characters
        # (meaning the AI already responded in the native script)
        if any(ord(c) > 127 for c in text):
            return text

        translated = GoogleTranslator(
            source='en',
            target=target_lang
        ).translate(text)

        if not translated:
            return text

        return translated

    except:
        return text


# =========================
# 🔥 FULL PIPELINE (UPDATED)
# =========================
def translate_pipeline(user_text):
    """
    Full pipeline:
    1. Detect language
    2. Convert to English (for RAG)
    3. Return original language for response
    """

    lang = detect_language(user_text)

    # ✅ skip translation if already English
    if lang == "en":
        return user_text, "en"

    english_text = to_english(user_text)

    # 🔥 fallback safety
    if not english_text:
        return user_text, lang

    return english_text, lang