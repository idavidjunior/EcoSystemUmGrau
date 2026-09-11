#!/usr/bin/env python3
"""Teste de conversão de imagem para bordado."""

import sys
sys.path.append('Projetos/ConversorBordado')

from PIL import Image
import pyembroidery
from conversor import ConversorBordado

def test_auto_convert():
    """Testa conversão automática."""
    # Criar imagem de teste
    img = Image.new('L', (100, 100), 255)  # Fundo branco
    pixels = img.load()
    
    # Desenhar quadrado preto
    for x in range(20, 80):
        for y in range(20, 80):
            pixels[x, y] = 0  # Preto
    
    # Criar padrão de bordado
    pattern = pyembroidery.EmbPattern()
    
    # Criar instância do conversor (sem interface)
    class FakeRoot:
        def __init__(self):
            pass
        def title(self, t): pass
        def geometry(self, g): pass
        def columnconfigure(self, c, **kwargs): pass
        def rowconfigure(self, r, **kwargs): pass
        def mainloop(self): pass
        def update(self): pass
    
    root = FakeRoot()
    conversor = ConversorBordado(root)
    
    # Chamar auto_convert
    conversor.auto_convert(img, pattern)
    
    # Verificar se padrão tem pontos
    print(f"Pontos no padrão: {len(pattern.stitches)}")
    assert len(pattern.stitches) > 0, "Nenhum ponto gerado"
    
    # Salvar em formato DST
    pyembroidery.write_dst(pattern, 'teste_auto.dst')
    print("✓ Conversão automática funcionou")
    
    return True

def test_manual_convert():
    """Testa conversão manual."""
    # Criar imagem de teste
    img = Image.new('L', (100, 100), 255)
    pixels = img.load()
    
    # Desenhar círculo preto
    for x in range(50):
        for y in range(50):
            if (x-25)**2 + (y-25)**2 < 20**2:
                pixels[x, y] = 0
    
    # Criar padrão de bordado
    pattern = pyembroidery.EmbPattern()
    
    # Criar instância do conversor
    class FakeRoot:
        def __init__(self):
            pass
        def title(self, t): pass
        def geometry(self, g): pass
        def columnconfigure(self, c, **kwargs): pass
        def rowconfigure(self, r, **kwargs): pass
        def mainloop(self): pass
        def update(self): pass
    
    root = FakeRoot()
    conversor = ConversorBordado(root)
    
    # Configurar variáveis manuais
    conversor.density_var.set(0.5)
    conversor.stitch_var.set("fill")
    conversor.width_var.set(50.0)
    
    # Chamar manual_convert
    conversor.manual_convert(img, pattern)
    
    # Verificar se padrão tem pontos
    print(f"Pontos no padrão (manual): {len(pattern.stitches)}")
    assert len(pattern.stitches) > 0, "Nenhum ponto gerado no modo manual"
    
    # Salvar em formato PES
    pyembroidery.write_pes(pattern, 'teste_manual.pes')
    print("✓ Conversão manual funcionou")
    
    return True

if __name__ == "__main__":
    print("Testes de conversão:")
    print("1. Teste automático...")
    test_auto_convert()
    
    print("\n2. Teste manual...")
    test_manual_convert()
    
    print("\n✓ Todos os testes passaram!")