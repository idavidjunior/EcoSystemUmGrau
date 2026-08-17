import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
from tts import SpeechPipeline

pipeline = SpeechPipeline()

test_cases = [
    "o adb auto connect ponto pai",
    "o david ligou",
    "o github tem muitos repos",
    "o jarvis ta online",
    "o json tem erro",
    "a nvidia lançou driver",
    "o widget ta bugado",
]

print("=== TESTE TODAS PRONÚNCIAS ===\n")
for text in test_cases:
    prepared, meta = pipeline.prepare(text)
    print(f"Original: {text}")
    print(f"Preparado: {prepared}")
    print(f"Pronunciation applied: {meta['pronunciation_applied']}")
    print()