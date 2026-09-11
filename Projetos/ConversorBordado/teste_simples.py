#!/usr/bin/env python3
"""Teste simples de conversão de imagem para bordado."""

import pyembroidery
from PIL import Image

def converter_imagem_para_bordado(image_path, output_path, formato="DST", modo="auto"):
    """
    Converte imagem para arquivo de bordado.
    
    Args:
        image_path: Caminho da imagem de entrada
        output_path: Caminho do arquivo de saída
        formato: Formato de saída (DST, PES, JEF, etc.)
        modo: "auto" para automático, "manual" para manual
    """
    # Carregar imagem
    img = Image.open(image_path)
    
    # Converter para escala de cinza
    if img.mode != 'L':
        img = img.convert('L')
    
    # Criar padrão de bordado
    pattern = pyembroidery.EmbPattern()
    
    # Obter dimensões
    width, height = img.size
    pixels = img.load()
    
    # Configurações baseadas no modo
    if modo == "auto":
        density = 0.4
        scale = 0.5  # Escala para mm
        threshold = 128
    else:
        density = 0.5
        scale = 50.0 / width  # Ajustar para 50mm de largura
        threshold = 100
    
    # Criar pontos de bordado
    step = max(1, int(3 / density))
    
    for y in range(0, height, step):
        for x in range(0, width, step):
            pixel = pixels[x, y]
            if pixel < threshold:
                # Converter coordenadas para mm
                px = x * scale
                py = y * scale
                pattern.add_stitch_absolute(pyembroidery.STITCH, px, py)
    
    # Salvar arquivo
    write_func = getattr(pyembroidery, f"write_{formato.lower()}")
    write_func(pattern, output_path)
    
    print(f"✓ Conversão concluída: {output_path}")
    print(f"  Formato: {formato}")
    print(f"  Modo: {modo}")
    print(f"  Pontos: {len(pattern.stitches)}")
    
    return output_path

def main():
    """Teste principal."""
    # Criar imagem de teste
    img = Image.new('L', (200, 200), 255)  # Fundo branco
    pixels = img.load()
    
    # Desenhar um "X" preto
    for i in range(200):
        pixels[i, i] = 0  # Diagonal principal
        pixels[i, 199-i] = 0  # Diagonal secundária
    
    # Salvar imagem de teste
    img.save('imagem_teste.png')
    print("Imagem de teste criada: imagem_teste.png")
    
    # Testar conversão automática
    print("\n1. Teste automático (DST):")
    converter_imagem_para_bordado('imagem_teste.png', 'teste_auto.dst', 'DST', 'auto')
    
    # Testar conversão manual
    print("\n2. Teste manual (PES):")
    converter_imagem_para_bordado('imagem_teste.png', 'teste_manual.pes', 'PES', 'manual')
    
    # Testar outros formatos
    print("\n3. Teste JEF:")
    converter_imagem_para_bordado('imagem_teste.png', 'teste.jef', 'JEF', 'auto')
    
    print("\n✓ Todos os testes concluídos!")

if __name__ == "__main__":
    main()