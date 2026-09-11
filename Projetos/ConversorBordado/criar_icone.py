#!/usr/bin/env python3
"""Cria ícone para o Conversor de Bordado."""

from PIL import Image, ImageDraw

def criar_icone():
    """Cria um ícone de agulha de bordado."""
    # Criar imagem 64x64 com fundo transparente
    size = 64
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Fundo azul arredondado
    draw.rounded_rectangle([(2, 2), (62, 62)], radius=10, fill=(41, 98, 255))
    
    # Agulha prateada
    draw.line([(20, 45), (44, 21)], fill=(192, 192, 192), width=4)
    draw.line([(44, 21), (48, 25)], fill=(192, 192, 192), width=4)
    
    # Fio vermelho
    draw.line([(20, 45), (15, 55)], fill=(220, 50, 50), width=2)
    draw.line([(15, 55), (25, 50)], fill=(220, 50, 50), width=2)
    draw.line([(25, 50), (20, 45)], fill=(220, 50, 50), width=2)
    
    # Ponta da agulha
    draw.ellipse([(42, 19), (50, 27)], fill=(220, 220, 220))
    
    img.save('icon.ico', format='ICO', sizes=[(64, 64)])
    print("Ícone criado: icon.ico")

if __name__ == "__main__":
    criar_icone()