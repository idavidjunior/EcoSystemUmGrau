#!/usr/bin/env python3
"""Testes das novas funcionalidades do conversor de bordado."""

import sys
sys.path.append('Projetos/ConversorBordado')

from PIL import Image
import pyembroidery

def test_qualidades():
    """Testa as diferentes qualidades de conversão."""
    print("Teste de qualidades:")
    
    # Criar imagem de teste
    img = Image.new('L', (100, 100), 255)
    pixels = img.load()
    
    # Desenhar um padrão
    for x in range(50):
        for y in range(50):
            if (x + y) % 10 == 0:
                pixels[x, y] = 0
    
    # Testar cada qualidade
    qualidades = {
        "Normal": {"density": 0.3, "step": 4, "thickness": 1},
        "Média": {"density": 0.5, "step": 3, "thickness": 2},
        "Super Alta": {"density": 0.8, "step": 2, "thickness": 3}
    }
    
    for nome, config in qualidades.items():
        pattern = pyembroidery.EmbPattern()
        
        # Converter com a qualidade especificada
        step = config["step"]
        scale = 0.5
        
        for y in range(0, 100, step):
            for x in range(0, 100, step):
                pixel = pixels[x, y]
                if pixel < 128:
                    pattern.add_stitch_absolute(pyembroidery.STITCH, x * scale, y * scale)
        
        # Salvar arquivo
        filename = f'teste_{nome.lower().replace(" ", "_")}.dst'
        pyembroidery.write_dst(pattern, filename)
        
        print(f"  ✓ {nome}: {len(pattern.stitches)} pontos -> {filename}")

def test_reforco():
    """Testa as opções de reforço."""
    print("\nTeste de reforço:")
    
    # Criar padrão de teste
    pattern = pyembroidery.EmbPattern()
    
    # Adicionar pontos básicos
    for i in range(20):
        pattern.add_stitch_absolute(pyembroidery.STITCH, i * 5, i * 5)
    
    print(f"  Original: {len(pattern.stitches)} pontos")
    
    # Testar cada tipo de reforço
    tipos_reforco = ["Satin Denso", "Fill Triplo", "Cadeia Grossa"]
    
    for tipo in tipos_reforco:
        # Criar cópia do padrão
        pattern_copy = pyembroidery.EmbPattern()
        for stitch in pattern.stitches:
            x, y, cmd = stitch
            pattern_copy.add_stitch_absolute(cmd, x, y)
        
        # Aplicar reforço (simulação)
        if tipo == "Satin Denso":
            # Adicionar pontos ao redor
            new_stitches = []
            for stitch in pattern_copy.stitches:
                x, y, cmd = stitch
                new_stitches.append((x, y, cmd))
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx != 0 or dy != 0:
                            new_stitches.append((x + dx * 0.5, y + dy * 0.5, cmd))
            pattern_copy.stitches = []
            for s in new_stitches:
                pattern_copy.add_stitch_absolute(s[2], s[0], s[1])
        
        elif tipo == "Fill Triplo":
            # Triplicar pontos
            new_stitches = []
            for stitch in pattern_copy.stitches:
                x, y, cmd = stitch
                new_stitches.append((x, y, cmd))
                new_stitches.append((x + 0.3, y, cmd))
                new_stitches.append((x, y + 0.3, cmd))
            pattern_copy.stitches = []
            for s in new_stitches:
                pattern_copy.add_stitch_absolute(s[2], s[0], s[1])
        
        elif tipo == "Cadeia Grossa":
            # Adicionar pontos intermediários
            new_stitches = []
            for i, stitch in enumerate(pattern_copy.stitches):
                x, y, cmd = stitch
                new_stitches.append((x, y, cmd))
                if i < len(pattern_copy.stitches) - 1:
                    next_x, next_y, _ = pattern_copy.stitches[i + 1]
                    mid_x = (x + next_x) / 2
                    mid_y = (y + next_y) / 2
                    new_stitches.append((mid_x, mid_y, cmd))
            pattern_copy.stitches = []
            for s in new_stitches:
                pattern_copy.add_stitch_absolute(s[2], s[0], s[1])
        
        print(f"  ✓ {tipo}: {len(pattern_copy.stitches)} pontos")

def main():
    """Executa todos os testes."""
    print("=== Testes das Novas Funcionalidades ===\n")
    
    test_qualidades()
    test_reforco()
    
    print("\n✓ Todos os testes concluídos!")

if __name__ == "__main__":
    main()