#!/usr/bin/env python3
"""
Editor de Bordado - Ferramentas de edição profissional
Similar ao PE-Design e Wilcom
"""

import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import pyembroidery
import numpy as np
from skimage import measure, feature
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum


class StitchType(Enum):
    FILL = "fill"
    SATIN = "satin"
    RUNNING = "running"
    STEP = "step"


@dataclass
class StitchRegion:
    """Região de bordado com suas propriedades."""
    id: int
    color: Tuple[int, int, int]
    stitch_type: StitchType
    density: float  # 0.1 a 1.0
    angle: float  # graus
    mask: np.ndarray
    bounds: Tuple[int, int, int, int]  # minr, minc, maxr, maxc
    points: List[Tuple[float, float]]
    visible: bool = True
    locked: bool = False
    name: str = ""


@dataclass
class Thread:
    """Cor de fio disponível."""
    name: str
    code: str
    color: Tuple[int, int, int]


# Paleta de fios comuns
THREAD_PALETTE = [
    Thread("Branco", "#01", (255, 255, 255)),
    Thread("Preto", "#02", (0, 0, 0)),
    Thread("Vermelho Escuro", "#10", (139, 0, 0)),
    Thread("Vermelho", "#11", (220, 20, 60)),
    Thread("Rosa", "#12", (255, 105, 180)),
    Thread("Azul Marinho", "#20", (0, 0, 128)),
    Thread("Azul", "#21", (0, 112, 196)),
    Thread("Azul Claro", "#22", (100, 149, 237)),
    Thread("Verde Escuro", "#30", (0, 100, 0)),
    Thread("Verde", "#31", (34, 139, 34)),
    Thread("Verde Claro", "#32", (144, 238, 144)),
    Thread("Amarelo", "#41", (255, 215, 0)),
    Thread("Laranja", "#51", (255, 140, 0)),
    Thread("Roxo", "#61", (128, 0, 128)),
    Thread("Marrom", "#71", (139, 69, 19)),
    Thread("Cinza", "#81", (128, 128, 128)),
    Thread("Cinza Claro", "#82", (192, 192, 192)),
]


class EmbroideryEditor:
    """Editor profissional de bordado."""
    
    def __init__(self, root, image: Image.Image, regions: List[StitchRegion] = None):
        self.root = root
        self.root.title("Editor de Bordado")
        self.root.geometry("1200x800")
        
        # Dados do bordado
        self.original_image = image
        self.regions = regions if regions else []
        self.selected_region_id = None
        self.current_tool = "select"
        self.zoom = 1.0
        self.pan_offset = [0, 0]
        self.is_panning = False
        self.pan_start = [0, 0]
        
        # Undo/Redo
        self.undo_stack = []
        self.redo_stack = []
        
        # Cor selecionada
        self.selected_thread = THREAD_PALETTE[2]  # Vermelho escuro padrão
        
        self.setup_ui()
        self.load_image_to_canvas()
    
    def setup_ui(self):
        """Configura a interface do editor."""
        # Menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Salvar DST", command=lambda: self.save("DST"))
        file_menu.add_command(label="Salvar PES", command=lambda: self.save("PES"))
        file_menu.add_command(label="Salvar JEF", command=lambda: self.save("JEF"))
        file_menu.add_command(label="Exportar Imagem", command=self.export_image)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.destroy)
        
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Editar", menu=edit_menu)
        edit_menu.add_command(label="Desfazer", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Refazer", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Selecionar Tudo", command=self.select_all)
        edit_menu.add_command(label="Desselecionar", command=self.deselect_all)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Visualizar", menu=view_menu)
        view_menu.add_command(label="Zoom In", command=lambda: self.adjust_zoom(0.25))
        view_menu.add_command(label="Zoom Out", command=lambda: self.adjust_zoom(-0.25))
        view_menu.add_command(label="Zoom 100%", command=lambda: self.set_zoom(1.0))
        view_menu.add_command(label="Ajustar à Janela", command=self.fit_to_window)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ferramentas", menu=tools_menu)
        tools_menu.add_command(label="Combinar Regiões Selecionadas", command=self.merge_selected)
        tools_menu.add_command(label="Separar por Cor", command=self.separate_by_color)
        tools_menu.add_command(label="Inverter Seleção", command=self.invert_selection)
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Painel esquerdo - Ferramentas
        tools_frame = ttk.LabelFrame(main_frame, text="Ferramentas", padding=5)
        tools_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        tools = [
            ("Selecionar", "select"),
            ("Mover", "move"),
            ("Redimensionar", "resize"),
            ("Rotacionar", "rotate"),
            ("Editar Pontos", "edit_points"),
            ("Pan", "pan"),
        ]
        
        for text, tool in tools:
            btn = ttk.Radiobutton(tools_frame, text=text, variable=self.current_tool, 
                                 value=tool, command=self.on_tool_change)
            btn.pack(fill=tk.X, pady=2)
        
        # Separador
        ttk.Separator(tools_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Propriedades da região
        props_frame = ttk.LabelFrame(tools_frame, text="Propriedades", padding=5)
        props_frame.pack(fill=tk.X)
        
        ttk.Label(props_frame, text="Tipo de Costura:").pack(anchor=tk.W)
        self.stitch_type_var = tk.StringVar(value="fill")
        stitch_combo = ttk.Combobox(props_frame, textvariable=self.stitch_type_var,
                                   values=["fill", "satin", "running", "step"], state="readonly")
        stitch_combo.pack(fill=tk.X, pady=2)
        stitch_combo.bind("<<ComboboxSelected>>", self.on_property_change)
        
        ttk.Label(props_frame, text="Densidade:").pack(anchor=tk.W)
        self.density_var = tk.DoubleVar(value=0.5)
        density_scale = ttk.Scale(props_frame, from_=0.1, to=1.0, 
                                 variable=self.density_var, orient=tk.HORIZONTAL)
        density_scale.pack(fill=tk.X, pady=2)
        density_scale.bind("<ButtonRelease-1>", self.on_property_change)
        
        ttk.Label(props_frame, text="Ângulo (°):").pack(anchor=tk.W)
        self.angle_var = tk.DoubleVar(value=0)
        angle_spin = ttk.Spinbox(props_frame, from_=0, to=360, 
                                textvariable=self.angle_var, increment=15)
        angle_spin.pack(fill=tk.X, pady=2)
        angle_spin.bind("<Return>", self.on_property_change)
        
        # Paleta de cores
        palette_frame = ttk.LabelFrame(tools_frame, text="Paleta de Fios", padding=5)
        palette_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.thread_canvas = tk.Canvas(palette_frame, height=120)
        self.thread_canvas.pack(fill=tk.X)
        self.draw_thread_palette()
        
        # Painel central - Canvas
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg='#2d2d2d')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Vincular eventos do mouse
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<B1-Motion>", self.on_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_release)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", lambda e: self.adjust_zoom(0.1))
        self.canvas.bind("<Button-5>", lambda e: self.adjust_zoom(-0.1))
        self.canvas.bind("<Motion>", self.on_mouse_move)
        
        # Atalhos de teclado
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Delete>", lambda e: self.delete_selected())
        self.root.bind("<Escape>", lambda e: self.deselect_all())
        self.root.bind("<plus>", lambda e: self.adjust_zoom(0.25))
        self.root.bind("<minus>", lambda e: self.adjust_zoom(-0.25))
        
        # Painel direito - Lista de Camadas
        layers_frame = ttk.LabelFrame(main_frame, text="Camadas", padding=5)
        layers_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        self.layers_listbox = tk.Listbox(layers_frame, width=25, height=20)
        self.layers_listbox.pack(fill=tk.BOTH, expand=True)
        self.layers_listbox.bind("<<ListboxSelect>>", self.on_layer_select)
        
        # Botões de camada
        layer_btns = ttk.Frame(layers_frame)
        layer_btns.pack(fill=tk.X, pady=5)
        
        ttk.Button(layer_btns, text="↑", width=3, command=self.move_layer_up).pack(side=tk.LEFT)
        ttk.Button(layer_btns, text="↓", width=3, command=self.move_layer_down).pack(side=tk.LEFT)
        ttk.Button(layer_btns, text="🗑", width=3, command=self.delete_selected).pack(side=tk.LEFT)
        ttk.Button(layer_btns, text="Visível", width=6, command=self.toggle_visibility).pack(side=tk.LEFT)
        
        # Barra de status
        self.status_var = tk.StringVar(value="Pronto")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Barra de zoom
        zoom_frame = ttk.Frame(self.root)
        zoom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Label(zoom_frame, text="Zoom:").pack(side=tk.LEFT, padx=5)
        ttk.Button(zoom_frame, text="-", width=3, command=lambda: self.adjust_zoom(-0.25)).pack(side=tk.LEFT)
        self.zoom_label = ttk.Label(zoom_frame, text="100%", width=6)
        self.zoom_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(zoom_frame, text="+", width=3, command=lambda: self.adjust_zoom(0.25)).pack(side=tk.LEFT)
        ttk.Button(zoom_frame, text="Ajustar", command=self.fit_to_window).pack(side=tk.LEFT, padx=10)
        
        self.update_layers_list()
    
    def draw_thread_palette(self):
        """Desenha a paleta de cores de fios."""
        self.thread_canvas.delete("all")
        
        cols = 6
        cell_size = 20
        padding = 2
        
        for i, thread in enumerate(THREAD_PALETTE):
            row = i // cols
            col = i % cols
            
            x = col * (cell_size + padding) + 5
            y = row * (cell_size + padding) + 5
            
            # Desenhar quadrado de cor
            self.thread_canvas.create_rectangle(x, y, x + cell_size, y + cell_size,
                                               fill=f'#{thread.color[0]:02x}{thread.color[1]:02x}{thread.color[2]:02x}',
                                               outline='gray', width=1,
                                               tags=f'thread_{i}')
            
            # Vincular clique
            self.thread_canvas.tag_bind(f'thread_{i}', '<Button-1>', 
                                       lambda e, t=thread: self.select_thread(t))
    
    def select_thread(self, thread: Thread):
        """Seleciona uma cor de fio."""
        self.selected_thread = thread
        self.status_var.set(f"Fio selecionado: {thread.name}")
        
        # Atualizar região selecionada
        if self.selected_region_id is not None:
            self.save_state()
            for region in self.regions:
                if region.id == self.selected_region_id:
                    region.color = thread.color
                    break
            self.refresh_canvas()
    
    def load_image_to_canvas(self):
        """Carrega a imagem no canvas."""
        self.refresh_canvas()
    
    def refresh_canvas(self):
        """Redesenha o canvas."""
        self.canvas.delete("all")
        
        # Calcular área visível
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
        
        # Centro da imagem
        img_center_x = self.original_image.width / 2
        img_center_y = self.original_image.height / 2
        
        # Offset do pan
        center_x = canvas_width / 2 + self.pan_offset[0]
        center_y = canvas_height / 2 + self.pan_offset[1]
        
        # Desenhar fundo xadrez
        self.draw_checkerboard(center_x, center_y)
        
        # Desenhar regiões
        for region in self.regions:
            if not region.visible:
                continue
            
            self.draw_region(region, center_x, center_y)
        
        # Desenhar seleção
        if self.selected_region_id is not None:
            for region in self.regions:
                if region.id == self.selected_region_id:
                    self.draw_selection_box(region, center_x, center_y)
                    break
    
    def draw_checkerboard(self, center_x, center_y):
        """Desenha fundo xadrez transparente."""
        size = 10
        img_w = self.original_image.width
        img_h = self.original_image.height
        
        start_x = center_x - (img_w * self.zoom) / 2
        start_y = center_y - (img_h * self.zoom) / 2
        
        for y in range(0, int(img_h * self.zoom), size):
            for x in range(0, int(img_w * self.zoom), size):
                px = start_x + x
                py = start_y + y
                
                if (x // size + y // size) % 2 == 0:
                    color = '#ffffff'
                else:
                    color = '#e0e0e0'
                
                self.canvas.create_rectangle(px, py, px + size, py + size,
                                           fill=color, outline='')
    
    def draw_region(self, region: StitchRegion, center_x, center_y):
        """Desenha uma região de bordado."""
        if region.mask is None:
            return
        
        # Converter máscara para pontos
        minr, minc, maxr, maxc = region.bounds
        
        # Calcular posição no canvas
        img_w = self.original_image.width
        img_h = self.original_image.height
        
        start_x = center_x - (img_w * self.zoom) / 2
        start_y = center_y - (img_h * self.zoom) / 2
        
        # Desenhar pontos de bordado
        step = max(1, int(4 / region.density))
        
        for y in range(minr, maxr, step):
            for x in range(minc, maxc, step):
                if region.mask[y - minr, x - minc]:
                    # Converter coordenada
                    px = start_x + x * self.zoom
                    py = start_y + y * self.zoom
                    
                    # Tamanho do ponto baseado no tipo
                    if region.stitch_type == StitchType.SATIN:
                        size = 2
                    elif region.stitch_type == StitchType.RUNNING:
                        size = 1
                    else:
                        size = 1.5
                    
                    # Desenhar ponto
                    color = f'#{region.color[0]:02x}{region.color[1]:02x}{region.color[2]:02x}'
                    self.canvas.create_oval(px - size, py - size, px + size, py + size,
                                          fill=color, outline='')
        
        # Desenhar contorno se selecionado
        if region.id == self.selected_region_id:
            self.draw_region_contour(region, center_x, center_y)
    
    def draw_region_contour(self, region: StitchRegion, center_x, center_y):
        """Desenha o contorno de uma região."""
        minr, minc, maxr, maxc = region.bounds
        img_w = self.original_image.width
        img_h = self.original_image.height
        
        start_x = center_x - (img_w * self.zoom) / 2
        start_y = center_y - (img_h * self.zoom) / 2
        
        # Encontrar contornos
        contours = measure.find_contours(region.mask.astype(float), 0.5)
        
        for contour in contours:
            points = []
            for y, x in contour:
                px = start_x + (x + minc) * self.zoom
                py = start_y + (y + minr) * self.zoom
                points.extend([px, py])
            
            if len(points) >= 4:
                self.canvas.create_line(points, fill='#00ff00', width=2, dash=(5, 3))
    
    def draw_selection_box(self, region: StitchRegion, center_x, center_y):
        """Desenha caixa de seleção ao redor da região."""
        minr, minc, maxr, maxc = region.bounds
        img_w = self.original_image.width
        img_h = self.original_image.height
        
        start_x = center_x - (img_w * self.zoom) / 2
        start_y = center_y - (img_h * self.zoom) / 2
        
        x1 = start_x + minc * self.zoom
        y1 = start_y + minr * self.zoom
        x2 = start_x + maxc * self.zoom
        y2 = start_y + maxr * self.zoom
        
        # Caixa de seleção
        self.canvas.create_rectangle(x1 - 5, y1 - 5, x2 + 5, y2 + 5,
                                    outline='#00ff00', width=2, dash=(5, 3))
        
        # Alças de resize
        handle_size = 6
        handles = [
            (x1 - 5, y1 - 5), (x2 + 5, y1 - 5),  # Topo
            (x1 - 5, y2 + 5), (x2 + 5, y2 + 5),  # Base
            ((x1 + x2) / 2, y1 - 5),  # Topo centro
            ((x1 + x2) / 2, y2 + 5),  # Base centro
            (x1 - 5, (y1 + y2) / 2),  # Esquerda centro
            (x2 + 5, (y1 + y2) / 2),  # Direita centro
        ]
        
        for hx, hy in handles:
            self.canvas.create_rectangle(hx - handle_size/2, hy - handle_size/2,
                                        hx + handle_size/2, hy + handle_size/2,
                                        fill='#00ff00', outline='white')
    
    def on_tool_change(self):
        """Lida com mudança de ferramenta."""
        self.current_tool = self.current_tool.get() if hasattr(self.current_tool, 'get') else self.current_tool
        self.status_var.set(f"Ferramenta: {self.current_tool}")
    
    def on_left_click(self, event):
        """Lida com clique esquerdo."""
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        center_x = canvas_width / 2 + self.pan_offset[0]
        center_y = canvas_height / 2 + self.pan_offset[1]
        
        img_w = self.original_image.width
        img_h = self.original_image.height
        
        start_x = center_x - (img_w * self.zoom) / 2
        start_y = center_y - (img_h * self.zoom) / 2
        
        # Converter coordenada do canvas para imagem
        img_x = (event.x - start_x) / self.zoom
        img_y = (event.y - start_y) / self.zoom
        
        if self.current_tool.get() == "select" if hasattr(self.current_tool, 'get') else self.current_tool == "select":
            # Encontrar região sob o cursor
            clicked_region = None
            for region in reversed(self.regions):  # Inverter para priorizar camadas superiores
                if not region.visible:
                    continue
                minr, minc, maxr, maxc = region.bounds
                if minr <= img_y <= maxr and minc <= img_x <= maxc:
                    local_y = int(img_y) - minr
                    local_x = int(img_x) - minc
                    if 0 <= local_y < region.mask.shape[0] and 0 <= local_x < region.mask.shape[1]:
                        if region.mask[local_y, local_x]:
                            clicked_region = region
                            break
            
            if clicked_region:
                self.selected_region_id = clicked_region.id
                self.update_properties_from_region(clicked_region)
                self.status_var.set(f"Região selecionada: {clicked_region.name or f'Região {clicked_region.id}'}")
            else:
                self.selected_region_id = None
                self.status_var.set("Nenhuma região selecionada")
            
            self.update_layers_list()
            self.refresh_canvas()
        
        elif self.current_tool.get() == "pan" if hasattr(self.current_tool, 'get') else self.current_tool == "pan":
            self.is_panning = True
            self.pan_start = [event.x, event.y]
    
    def on_left_drag(self, event):
        """Lida com arrasto do botão esquerdo."""
        tool = self.current_tool.get() if hasattr(self.current_tool, 'get') else self.current_tool
        
        if tool == "pan" and self.is_panning:
            dx = event.x - self.pan_start[0]
            dy = event.y - self.pan_start[1]
            self.pan_offset[0] += dx
            self.pan_offset[1] += dy
            self.pan_start = [event.x, event.y]
            self.refresh_canvas()
        
        elif tool == "move" and self.selected_region_id is not None:
            # Mover região
            pass  # Implementar movimentação
        
        elif tool == "resize" and self.selected_region_id is not None:
            # Redimensionar região
            pass  # Implementar redimensionamento
    
    def on_left_release(self, event):
        """Lida com soltar botão esquerdo."""
        self.is_panning = False
    
    def on_right_click(self, event):
        """Lida com clique direito - menu de contexto."""
        # TODO: Implementar menu de contexto
        pass
    
    def on_mouse_wheel(self, event):
        """Lida com scroll do mouse para zoom."""
        if event.delta > 0:
            self.adjust_zoom(0.1)
        else:
            self.adjust_zoom(-0.1)
    
    def on_mouse_move(self, event):
        """Lida com movimento do mouse."""
        # Atualizar coordenadas na barra de status
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        center_x = canvas_width / 2 + self.pan_offset[0]
        center_y = canvas_height / 2 + self.pan_offset[1]
        
        img_w = self.original_image.width
        img_h = self.original_image.height
        
        start_x = center_x - (img_w * self.zoom) / 2
        start_y = center_y - (img_h * self.zoom) / 2
        
        img_x = (event.x - start_x) / self.zoom
        img_y = (event.y - start_y) / self.zoom
        
        if 0 <= img_x < img_w and 0 <= img_y < img_h:
            self.status_var.set(f"Coordenadas: ({img_x:.0f}, {img_y:.0f}) | Zoom: {self.zoom*100:.0f}%")
    
    def on_layer_select(self, event):
        """Lida com seleção na lista de camadas."""
        selection = self.layers_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.regions):
                self.selected_region_id = self.regions[index].id
                self.update_properties_from_region(self.regions[index])
                self.refresh_canvas()
    
    def on_property_change(self, event=None):
        """Lida com mudança de propriedades."""
        if self.selected_region_id is not None:
            self.save_state()
            
            for region in self.regions:
                if region.id == self.selected_region_id:
                    # Atualizar propriedades
                    stitch_type_map = {
                        "fill": StitchType.FILL,
                        "satin": StitchType.SATIN,
                        "running": StitchType.RUNNING,
                        "step": StitchType.STEP
                    }
                    region.stitch_type = stitch_type_map.get(self.stitch_type_var.get(), StitchType.FILL)
                    region.density = self.density_var.get()
                    region.angle = self.angle_var.get()
                    
                    # Regenerar pontos
                    self.regenerate_region_points(region)
                    break
            
            self.refresh_canvas()
    
    def regenerate_region_points(self, region: StitchRegion):
        """Regenera os pontos de bordado de uma região."""
        minr, minc, maxr, maxc = region.bounds
        new_points = []
        
        step = max(1, int(4 / region.density))
        
        for y in range(minr, maxr, step):
            for x in range(minc, maxc, step):
                if region.mask[y - minr, x - minc]:
                    # Aplicar rotação se necessário
                    if region.angle != 0:
                        cx = (minc + maxc) / 2
                        cy = (minr + maxr) / 2
                        rad = math.radians(region.angle)
                        cos_a = math.cos(rad)
                        sin_a = math.sin(rad)
                        
                        dx = x - cx
                        dy = y - cy
                        
                        new_x = cx + dx * cos_a - dy * sin_a
                        new_y = cy + dx * sin_a + dy * cos_a
                        
                        new_points.append((new_x, new_y))
                    else:
                        new_points.append((x, y))
        
        region.points = new_points
    
    def update_properties_from_region(self, region: StitchRegion):
        """Atualiza os controles de propriedades baseado na região."""
        stitch_type_reverse = {
            StitchType.FILL: "fill",
            StitchType.SATIN: "satin",
            StitchType.RUNNING: "running",
            StitchType.STEP: "step"
        }
        
        self.stitch_type_var.set(stitch_type_reverse.get(region.stitch_type, "fill"))
        self.density_var.set(region.density)
        self.angle_var.set(region.angle)
    
    def update_layers_list(self):
        """Atualiza a lista de camadas."""
        self.layers_listbox.delete(0, tk.END)
        
        for region in reversed(self.regions):  # Ordem inversa (camada superior primeiro)
            status = "👁" if region.visible else "  "
            lock = "🔒" if region.locked else "  "
            name = region.name or f"Região {region.id}"
            self.layers_listbox.insert(tk.END, f"{status}{lock} {name}")
            
            # Destacar selecionada
            if region.id == self.selected_region_id:
                self.layers_listbox.selection_set(len(self.regions) - 1 - self.regions.index(region))
    
    def adjust_zoom(self, delta):
        """Ajusta o zoom."""
        self.zoom = max(0.1, min(10.0, self.zoom + delta))
        self.zoom_label.config(text=f"{self.zoom*100:.0f}%")
        self.refresh_canvas()
    
    def set_zoom(self, level):
        """Define zoom específico."""
        self.zoom = level
        self.zoom_label.config(text=f"{self.zoom*100:.0f}%")
        self.refresh_canvas()
    
    def fit_to_window(self):
        """Ajusta a imagem à janela."""
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
        
        img_w = self.original_image.width
        img_h = self.original_image.height
        
        zoom_x = canvas_width / img_w
        zoom_y = canvas_height / img_h
        
        self.zoom = min(zoom_x, zoom_y) * 0.9
        self.pan_offset = [0, 0]
        
        self.zoom_label.config(text=f"{self.zoom*100:.0f}%")
        self.refresh_canvas()
    
    def save_state(self):
        """Salva estado para undo."""
        # TODO: Implementar undo/redo completo
        pass
    
    def undo(self):
        """Desfaz última ação."""
        # TODO: Implementar
        pass
    
    def redo(self):
        """Refaz última ação."""
        # TODO: Implementar
        pass
    
    def select_all(self):
        """Seleciona todas as regiões."""
        # TODO: Implementar
        pass
    
    def deselect_all(self):
        """Desseleciona tudo."""
        self.selected_region_id = None
        self.update_layers_list()
        self.refresh_canvas()
    
    def delete_selected(self):
        """Deleta região selecionada."""
        if self.selected_region_id is not None:
            self.save_state()
            self.regions = [r for r in self.regions if r.id != self.selected_region_id]
            self.selected_region_id = None
            self.update_layers_list()
            self.refresh_canvas()
    
    def move_layer_up(self):
        """Move camada para cima."""
        if self.selected_region_id is not None:
            for i, region in enumerate(self.regions):
                if region.id == self.selected_region_id and i > 0:
                    self.regions[i], self.regions[i-1] = self.regions[i-1], self.regions[i]
                    self.update_layers_list()
                    self.refresh_canvas()
                    break
    
    def move_layer_down(self):
        """Move camada para baixo."""
        if self.selected_region_id is not None:
            for i, region in enumerate(self.regions):
                if region.id == self.selected_region_id and i < len(self.regions) - 1:
                    self.regions[i], self.regions[i+1] = self.regions[i+1], self.regions[i]
                    self.update_layers_list()
                    self.refresh_canvas()
                    break
    
    def toggle_visibility(self):
        """Alterna visibilidade da região selecionada."""
        if self.selected_region_id is not None:
            for region in self.regions:
                if region.id == self.selected_region_id:
                    region.visible = not region.visible
                    self.update_layers_list()
                    self.refresh_canvas()
                    break
    
    def merge_selected(self):
        """Combina regiões selecionadas."""
        # TODO: Implementar
        pass
    
    def separate_by_color(self):
        """Separa regiões por cor."""
        # TODO: Implementar
        pass
    
    def invert_selection(self):
        """Inverte seleção."""
        # TODO: Implementar
        pass
    
    def save(self, formato: str):
        """Salva o bordado no formato especificado."""
        pattern = pyembroidery.EmbPattern()
        
        for region in self.regions:
            if not region.visible:
                continue
            
            # Adicionar cor
            pattern.add_stitch_absolute(pyembroidery.COLOR_CHANGE, 0, 0)
            
            # Adicionar pontos
            for x, y in region.points:
                pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
        
        # Salvar
        filetypes = [(f"Arquivo {formato}", f"*.{formato.lower()}")]
        output_path = filedialog.asksaveasfilename(
            title=f"Salvar como {formato}",
            defaultextension=f".{formato.lower()}",
            filetypes=filetypes
        )
        
        if output_path:
            write_func = getattr(pyembroidery, f"write_{formato.lower()}")
            write_func(pattern, output_path)
            self.status_var.set(f"Salvo: {output_path}")
            messagebox.showinfo("Sucesso", f"Arquivo {formato} salvo com sucesso!")
    
    def export_image(self):
        """Exporta como imagem."""
        filetypes = [
            ("PNG", "*.png"),
            ("JPEG", "*.jpg"),
            ("BMP", "*.bmp")
        ]
        
        output_path = filedialog.asksaveasfilename(
            title="Exportar como imagem",
            defaultextension=".png",
            filetypes=filetypes
        )
        
        if output_path:
            # Criar imagem do bordado
            img = Image.new('RGB', (self.original_image.width, self.original_image.height), (255, 255, 255))
            draw = ImageDraw.Draw(img)
            
            for region in self.regions:
                if not region.visible:
                    continue
                
                minr, minc, maxr, maxc = region.bounds
                step = max(1, int(4 / region.density))
                
                for y in range(minr, maxr, step):
                    for x in range(minc, maxc, step):
                        if region.mask[y - minr, x - minc]:
                            draw.point((x, y), fill=region.color)
            
            img.save(output_path)
            self.status_var.set(f"Imagem exportada: {output_path}")


def create_editor_from_image(image_path: str) -> EmbroideryEditor:
    """Cria editor a partir de uma imagem."""
    # Carregar imagem
    img = Image.open(image_path)
    
    # Converter para escala de cinza para detecção
    if img.mode != 'L':
        gray = img.convert('L')
    else:
        gray = img
    
    # Detectar regiões
    img_array = np.array(gray)
    
    # Quantizar cores
    if img.mode != 'RGB':
        img_rgb = img.convert('RGB')
    else:
        img_rgb = img
    
    img_quantized = img_rgb.quantize(colors=6, method=Image.Quantize.MEDIANCUT)
    img_quantized_array = np.array(img_quantized)
    
    # Criar regiões para cada cor
    regions = []
    region_id = 0
    
    colors = np.unique(img_quantized_array)
    palette = img_quantized.getpalette()
    
    for color_idx in colors:
        mask = (img_quantized_array == color_idx)
        labeled = measure.label(mask)
        region_props = measure.regionprops(labeled)
        
        # Obter cor RGB
        r = palette[color_idx * 3]
        g = palette[color_idx * 3 + 1]
        b = palette[color_idx * 3 + 2]
        
        for prop in region_props:
            minr, minc, maxr, maxc = prop.bbox
            
            # Ignorar regiões muito pequenas
            if (maxr - minr) < 5 or (maxc - minc) < 5:
                continue
            
            region_mask = mask[minr:maxr, minc:maxc].copy()
            
            # Criar lista de pontos
            points = []
            for y in range(minr, maxr, 4):
                for x in range(minc, maxc, 4):
                    if region_mask[y - minr, x - minc]:
                        points.append((x, y))
            
            region = StitchRegion(
                id=region_id,
                color=(r, g, b),
                stitch_type=StitchType.FILL,
                density=0.5,
                angle=0,
                mask=region_mask,
                bounds=(minr, minc, maxr, maxc),
                points=points,
                name=f"Cor {color_idx}"
            )
            
            regions.append(region)
            region_id += 1
    
    # Criar editor
    root = tk.Tk()
    editor = EmbroideryEditor(root, img, regions)
    
    return editor


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # Pedir para selecionar arquivo
        root = tk.Tk()
        root.withdraw()
        image_path = filedialog.askopenfilename(
            title="Selecionar imagem",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp")]
        )
        root.destroy()
    
    if image_path:
        editor = create_editor_from_image(image_path)
        editor.root.mainloop()