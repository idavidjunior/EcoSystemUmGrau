#!/usr/bin/env python3
"""Teste básico do conversor de bordado."""

import pyembroidery
from PIL import Image
import numpy as np

def test_basic_conversion():
    """Testa conversão básica de imagem para bordado."""
    # Criar imagem de teste simples (quadrado preto)
    img = Image.new('L', (100, 100), 255)  # Fundo branco
    pixels = img.load()
    
    # Desenhar quadrado preto
    for x in range(20, 80):
        for y in range(20, 80):
            pixels[x, y] = 0  # Preto
    
    # Salvar imagem de teste
    img.save('teste_imagem.png')
    
    # Criar padrão de bordado
    pattern = pyembroidery.EmbPattern()
    
    # Converter imagem para pontos
    width, height = img.size
    pixels = img.load()
    
    for y in range(0, height, 3):
        for x in range(0, width, 3):
            pixel = pixels[x, y]
            if pixel < 128:
                pattern.add_stitch_absolute(pyembroidery.STITCH, x * 0.5, y * 0.5)
    
    # Finalizar padrão (sem comando de parada específico)
    
    # Salvar em diferentes formatos
    for formato in ['DST', 'PES', 'JEF']:
        try:
            filename = f'teste.{formato.lower()}'
            write_func = getattr(pyembroidery, f'write_{formato.lower()}')
            write_func(pattern, filename)
            print(f'✓ {formato} criado com sucesso: {filename}')
        except Exception as e:
            print(f'✗ Erro ao criar {formato}: {e}')

if __name__ == "__main__":
    test_basic_conversion()