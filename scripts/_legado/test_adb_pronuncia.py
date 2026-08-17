import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
from tts import SpeechPipeline

pipeline = SpeechPipeline()
text = 'o adb auto connect ponto pai'
prepared, meta = pipeline.prepare(text)
print('Original:', text)
print('Preparado:', prepared)
print('Pronunciation applied:', meta['pronunciation_applied'])