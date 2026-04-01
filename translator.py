from deep_translator import GoogleTranslator

# =========================
# 🌍 DETECT LANGUAGE
# =========================
def detect_language(text):
    try:
        return GoogleTranslator().detect(text)
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

        translated = GoogleTranslator(
            source='en',
            target=target_lang
        ).translate(text)

        # 🔥 important fix: avoid empty/short translations
        if not translated or len(translated.strip()) < 5:
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