#!/usr/bin/env python3
"""
Visualizador de Bordado - Versão simplificada e funcional.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from typing import List, Tuple
import math


class EmbroideryVisualizer:
    """Visualizador de bordado."""
    
    def __init__(self):
        self.thread_width = 2
    
    def render_realistic(self, regions, original_image: Image.Image, 
                        canvas_width: int = 800, canvas_height: int = 800) -> Image.Image:
        """Renderiza bordado realista com textura de fios."""
        img_w = original_image.width
        img_h = original_image.height
        
        # Calcular escala
        scale = min(canvas_width / img_w, canvas_height / img_h) * 0.85
        render_w = int(img_w * scale)
        render_h = int(img_h * scale)
        
        # Criar fundo de tecido
        fabric = Image.new('RGB', (render_w, render_h), (240, 235, 225))
        draw = ImageDraw.Draw(fabric)
        
        # Adicionar textura de tecido
        for y in range(0, render_h, 3):
            for x in range(0, render_w, 3):
                if (x + y) % 6 == 0:
                    draw.point((x, y), fill=(235, 230, 220))
        
        # Renderizar cada região
        for region in regions:
            if not region.visible:
                continue
            self._render_region_realistic(draw, region, scale)
        
        # Efeitos
        enhancer = ImageEnhance.Contrast(fabric)
        fabric = enhancer.enhance(1.1)
        enhancer = ImageEnhance.Sharpness(fabric)
        fabric = enhancer.enhance(1.2)
        
        return fabric
    
    def _render_region_realistic(self, draw: ImageDraw.Draw, region, scale: float):
        """Renderiza uma região com efeito de fio."""
        minr, minc, maxr, maxc = region.bounds
        mask = region.mask
        
        color = region.color
        highlight = tuple(min(255, c + 50) for c in color)
        shadow = tuple(max(0, c - 40) for c in color)
        
        spacing = max(2, int(4 / region.density))
        angle_rad = math.radians(region.angle)
        stitch_len = max(2, int(6 * scale))
        
        for y in range(0, maxr - minr, spacing):
            for x in range(0, maxc - minc, spacing):
                if mask[y, x]:
                    px = int((x + minc) * scale)
                    py = int((y + minr) * scale)
                    
                    # Direção do fio
                    dx = math.cos(angle_rad) * stitch_len
                    dy = math.sin(angle_rad) * stitch_len
                    
                    x1, y1 = int(px - dx/2), int(py - dy/2)
                    x2, y2 = int(px + dx/2), int(py + dy/2)
                    
                    # Sombra
                    draw.line([(x1, y1+1), (x2, y2+1)], fill=shadow, width=2)
                    # Fio principal
                    draw.line([(x1, y1), (x2, y2)], fill=color, width=2)
                    # Brilho
                    if stitch_len > 4:
                        draw.line([(x1, y1), (x2, y2)], fill=highlight, width=1)
    
    def render_stitch_view(self, regions, original_image: Image.Image,
                          canvas_width: int = 800, canvas_height: int = 800) -> Image.Image:
        """Renderiza visualização de pontos (vetorial)."""
        img_w = original_image.width
        img_h = original_image.height
        
        scale = min(canvas_width / img_w, canvas_height / img_h) * 0.85
        render_w = int(img_w * scale)
        render_h = int(img_h * scale)
        
        # Fundo branco
        stitch_img = Image.new('RGB', (render_w, render_h), (255, 255, 255))
        draw = ImageDraw.Draw(stitch_img)
        
        # Grade leve
        for x in range(0, render_w, 25):
            draw.line([(x, 0), (x, render_h)], fill=(230, 230, 230), width=1)
        for y in range(0, render_h, 25):
            draw.line([(0, y), (render_w, y)], fill=(230, 230, 230), width=1)
        
        # Renderizar pontos
        for region in regions:
            if not region.visible:
                continue
            self._render_region_stitch(draw, region, scale)
        
        return stitch_img
    
    def _render_region_stitch(self, draw: ImageDraw.Draw, region, scale: float):
        """Renderiza região no modo stitch."""
        minr, minc, maxr, maxc = region.bounds
        mask = region.mask
        
        color = region.color
        spacing = max(3, int(6 / region.density))
        angle_rad = math.radians(region.angle)
        stitch_len = max(4, int(10 * scale))
        
        for y in range(0, maxr - minr, spacing):
            for x in range(0, maxc - minc, spacing):
                if mask[y, x]:
                    px = int((x + minc) * scale)
                    py = int((y + minr) * scale)
                    
                    dx = math.cos(angle_rad) * stitch_len
                    dy = math.sin(angle_rad) * stitch_len
                    
                    x1, y1 = int(px - dx/2), int(py - dy/2)
                    x2, y2 = int(px + dx/2), int(py + dy/2)
                    
                    # Linha de costura
                    draw.line([(x1, y1), (x2, y2)], fill=color, width=2)
                    
                    # Pontos nas pontas
                    r = 2
                    draw.ellipse([(x1-r, y1-r), (x1+r, y1+r)], fill=color)
                    draw.ellipse([(x2-r, y2-r), (x2+r, y2+r)], fill=color)
    
    def render_solid_view(self, regions, original_image: Image.Image,
                         canvas_width: int = 800, canvas_height: int = 800) -> Image.Image:
        """Renderiza visualização sólida (blocos de cor)."""
        img_w = original_image.width
        img_h = original_image.height
        
        scale = min(canvas_width / img_w, canvas_height / img_h) * 0.85
        render_w = int(img_w * scale)
        render_h = int(img_h * scale)
        
        # Fundo branco
        solid_img = Image.new('RGB', (render_w, render_h), (255, 255, 255))
        draw = ImageDraw.Draw(solid_img)
        
        # Para cada região, preencher área
        for region in regions:
            if not region.visible:
                continue
            self._render_region_solid(draw, region, scale)
        
        return solid_img
    
    def _render_region_solid(self, draw: ImageDraw.Draw, region, scale: float):
        """Renderiza região no modo sólido."""
        minr, minc, maxr, maxc = region.bounds
        mask = region.mask
        
        color = region.color
        
        # Preencher pixels da máscara
        for y in range(maxr - minr):
            for x in range(maxc - minc):
                if mask[y, x]:
                    px = int((x + minc) * scale)
                    py = int((y + minr) * scale)
                    draw.rectangle([(px, py), (px+2, py+2)], fill=color)


class StitchSimulator:
    """Simulador de costura."""
    
    def __init__(self, regions, original_image: Image.Image):
        self.regions = regions
        self.original_image = original_image
        self.current_stitch = 0
        self.total_stitches = sum(len(r.points) for r in regions)
    
    def get_frame(self, stitch_index: int, width: int = 800, height: int = 800) -> Image.Image:
        """Retorna frame da animação."""
        img_w = self.original_image.width
        img_h = self.original_image.height
        
        scale = min(width / img_w, height / img_h) * 0.85
        render_w = int(img_w * scale)
        render_h = int(img_h * scale)
        
        # Fundo de tecido
        fabric = Image.new('RGB', (render_w, render_h), (240, 235, 225))
        draw = ImageDraw.Draw(fabric)
        
        # Desenhar pontos até o índice
        count = 0
        for region in self.regions:
            if not region.visible:
                continue
            
            color = region.color
            angle_rad = math.radians(region.angle)
            
            for x, y in region.points:
                if count >= stitch_index:
                    return fabric
                
                px = int(x * scale)
                py = int(y * scale)
                
                dx = math.cos(angle_rad) * 4
                dy = math.sin(angle_rad) * 4
                
                draw.line([(int(px-dx), int(py-dy)), (int(px+dx), int(py+dy))], 
                         fill=color, width=2)
                
                count += 1
        
        return fabric
    
    def get_total_stitches(self) -> int:
        return self.total_stitches