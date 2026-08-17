import sys
import json
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
from tts import SpeechPipeline

# Load pronuncias.json
json_path = r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\pronuncias.json'
with open(json_path, 'r', encoding='utf-8') as f:
    json_prons = json.load(f)

pipeline = SpeechPipeline()
engine_prons = pipeline.get_pronunciations()

print("=== SINCRONIZANDO PRONÚNCIAS ===\n")

# Check each entry in JSON
for palavra, data in json_prons.items():
    fala = data.get('fala')
    if not fala:
        continue
    
    # Check if in engine
    if palavra in engine_prons:
        current = engine_prons[palavra].get('fala')
        if current == fala:
            print(f"[OK] {palavra} -> {fala} (já sincronizado)")
        else:
            print(f"[DIFF] {palavra}: engine={current} vs json={fala} -> ATUALIZANDO")
            pipeline.add_pronunciation(palavra, fala)
    else:
        print(f"[NOVO] {palavra} -> {fala} -> ADICIONANDO")
        pipeline.add_pronunciation(palavra, fala)

print("\n=== VERIFICAÇÃO FINAL ===")
final_prons = pipeline.get_pronunciations()
for k, v in final_prons.items():
    print(f"  {k} -> {v.get('fala', 'N/A')}")

print(f"\nTotal: {len(final_prons)} pronúncias registradas")