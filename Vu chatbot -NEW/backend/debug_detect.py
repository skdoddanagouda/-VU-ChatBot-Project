from deep_translator import GoogleTranslator
import os

query = "வை?"
try:
    detect = GoogleTranslator().detect(query)
    print(f"Detected Language for '{query}': {detect}")
except Exception as e:
    print(f"Detection Error: {e}")

# Check if 'ta' is in supported languages
supported = GoogleTranslator().get_supported_languages(as_dict=True)
print(f"Tamil code in supported: {'ta' in supported.values()}")
print(f"Tamil key in supported: {'tamil' in supported.keys()}")
