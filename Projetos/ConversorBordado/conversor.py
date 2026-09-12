#!/usr/bin/env python3
"""
Conversor de Imagem para Bordado
Interface desktop para converter imagens em arquivos de bordado.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import pyembroidery
import numpy as np
from skimage import measure, morphology
import os
from pathlib import Path
import math
from editor_bordado import EmbroideryEditor, StitchRegion, StitchType
from embroidery_visualizer import EmbroideryVisualizer, StitchSimulator


class ConversorBordado:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor de Imagem para Bordado")
        self.root.geometry("1000x700")
        
        # Tentar definir ícone
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        # Variáveis
        self.image_path = None
        self.image_preview = None
        self.current_image = None
        self.original_image = None
        
        # Formatos suportados
        self.formatos = {
            "DST": "Tajima",
            "PES": "Brother",
            "JEF": "Janome",
            "EXP": "Melco",
            "XXX": "UFAC"
        }
        
        # Configurações de qualidade
        self.qualidades = {
            "Normal": {"density": 0.3, "step": 4, "thickness": 1},
            "Média": {"density": 0.5, "step": 3, "thickness": 2},
            "Super Alta": {"density": 0.8, "step": 2, "thickness": 3}
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura a interface do usuário."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="Conversor de Imagem para Bordado", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Frame de upload
        upload_frame = ttk.LabelFrame(main_frame, text="Upload da Imagem", padding="10")
        upload_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Botão de upload
        upload_btn = ttk.Button(upload_frame, text="Selecionar Imagem", 
                               command=self.upload_image)
        upload_btn.pack(pady=10)
        
        # Label para caminho da imagem
        self.path_label = ttk.Label(upload_frame, text="Nenhuma imagem selecionada", 
                                   wraplength=200)
        self.path_label.pack(pady=5)
        
        # Preview da imagem original
        self.preview_label = ttk.Label(upload_frame, text="Preview da imagem")
        self.preview_label.pack(pady=10, expand=True, fill=tk.BOTH)
        
        # Frame de configurações
        config_frame = ttk.LabelFrame(main_frame, text="Configurações", padding="10")
        config_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Modo de operação
        mode_frame = ttk.Frame(config_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(mode_frame, text="Modo:").pack(side=tk.LEFT)
        self.mode_var = tk.StringVar(value="auto")
        auto_radio = ttk.Radiobutton(mode_frame, text="Automático", 
                                     variable=self.mode_var, value="auto",
                                     command=self.update_mode)
        auto_radio.pack(side=tk.LEFT, padx=5)
        manual_radio = ttk.Radiobutton(mode_frame, text="Manual", 
                                       variable=self.mode_var, value="manual",
                                       command=self.update_mode)
        manual_radio.pack(side=tk.LEFT, padx=5)
        
        # Frame de ajustes manuais (inicialmente oculto)
        self.manual_frame = ttk.Frame(config_frame)
        
        # Configurações manuais
        ttk.Label(self.manual_frame, text="Densidade de Pontos:").pack(anchor=tk.W)
        self.density_var = tk.DoubleVar(value=0.4)
        density_scale = ttk.Scale(self.manual_frame, from_=0.1, to=1.0, 
                                 variable=self.density_var, orient=tk.HORIZONTAL)
        density_scale.pack(fill=tk.X, pady=2)
        
        ttk.Label(self.manual_frame, text="Tipo de Costura:").pack(anchor=tk.W)
        self.stitch_var = tk.StringVar(value="fill")
        stitch_combo = ttk.Combobox(self.manual_frame, textvariable=self.stitch_var,
                                   values=["fill", "satin", "running"], state="readonly")
        stitch_combo.pack(fill=tk.X, pady=2)
        
        ttk.Label(self.manual_frame, text="Largura (mm):").pack(anchor=tk.W)
        self.width_var = tk.DoubleVar(value=100.0)
        width_spin = ttk.Spinbox(self.manual_frame, from_=10.0, to=200.0, 
                                textvariable=self.width_var, increment=5.0)
        width_spin.pack(fill=tk.X, pady=2)
        
        # Frame de qualidade
        quality_frame = ttk.LabelFrame(config_frame, text="Qualidade", padding="10")
        quality_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(quality_frame, text="Nível de Qualidade:").pack(anchor=tk.W)
        self.quality_var = tk.StringVar(value="Normal")
        quality_combo = ttk.Combobox(quality_frame, textvariable=self.quality_var,
                                    values=list(self.qualidades.keys()), state="readonly")
        quality_combo.pack(fill=tk.X, pady=2)
        
        # Frame de precisão
        precision_frame = ttk.LabelFrame(config_frame, text="Precisão", padding="10")
        precision_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(precision_frame, text="Precisão da Conversão:").pack(anchor=tk.W)
        self.precision_var = tk.StringVar(value="Normal")
        precision_combo = ttk.Combobox(precision_frame, textvariable=self.precision_var,
                                      values=["Baixa", "Normal", "Alta", "Muito Alta"], 
                                      state="readonly")
        precision_combo.pack(fill=tk.X, pady=2)
        
        # Frame de reforço
        reinforcement_frame = ttk.LabelFrame(config_frame, text="Reforço do Bordado", padding="10")
        reinforcement_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Opção de reforço
        self.reinforcement_var = tk.BooleanVar(value=False)
        reinforcement_check = ttk.Checkbutton(reinforcement_frame, 
                                             text="Ativar reforço (bordado cheio e relevo grosso)",
                                             variable=self.reinforcement_var)
        reinforcement_check.pack(anchor=tk.W, pady=2)
        
        # Tipo de reforço
        ttk.Label(reinforcement_frame, text="Tipo de Reforço:").pack(anchor=tk.W)
        self.reinforcement_type_var = tk.StringVar(value="Satin Denso")
        reinforcement_type_combo = ttk.Combobox(reinforcement_frame, 
                                               textvariable=self.reinforcement_type_var,
                                               values=["Satin Denso", "Fill Triplo", "Cadeia Grossa"],
                                               state="readonly")
        reinforcement_type_combo.pack(fill=tk.X, pady=2)
        
        # Espessura do reforço
        ttk.Label(reinforcement_frame, text="Espessura do Reforço:").pack(anchor=tk.W)
        self.thickness_var = tk.DoubleVar(value=2.0)
        thickness_scale = ttk.Scale(reinforcement_frame, from_=1.0, to=5.0, 
                                   variable=self.thickness_var, orient=tk.HORIZONTAL)
        thickness_scale.pack(fill=tk.X, pady=2)
        
        # Frame de exportação
        export_frame = ttk.LabelFrame(config_frame, text="Exportação", padding="10")
        export_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(export_frame, text="Formato de Saída:").pack(anchor=tk.W)
        self.format_var = tk.StringVar(value="DST")
        format_combo = ttk.Combobox(export_frame, textvariable=self.format_var,
                                   values=list(self.formatos.keys()), state="readonly")
        format_combo.pack(fill=tk.X, pady=2)
        
        # Botões de ação
        button_frame = ttk.Frame(export_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Botão de prévia
        preview_btn = ttk.Button(button_frame, text="Gerar Prévia", 
                                command=self.generate_preview)
        preview_btn.pack(side=tk.LEFT, padx=(0, 5), expand=True, fill=tk.X)
        
        # Botão de conversão
        convert_btn = ttk.Button(button_frame, text="Converter e Salvar", 
                                command=self.convert_image)
        convert_btn.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        # Barra de status
        self.status_var = tk.StringVar(value="Pronto")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def upload_image(self):
        """Abre diálogo para selecionar imagem."""
        filetypes = [
            ("Imagens", "*.png *.jpg *.jpeg *.gif *.bmp"),
            ("Todos os arquivos", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Selecionar Imagem",
            filetypes=filetypes
        )
        
        if filename:
            self.image_path = filename
            self.path_label.config(text=os.path.basename(filename))
            self.load_image_preview(filename)
            self.status_var.set(f"Imagem carregada: {os.path.basename(filename)}")
    
    def load_image_preview(self, path):
        """Carrega preview da imagem."""
        try:
            # Carregar imagem com Pillow
            self.original_image = Image.open(path)
            self.current_image = self.original_image.copy()
            
            # Redimensionar para preview
            preview_size = (200, 200)
            self.current_image.thumbnail(preview_size, Image.Resampling.LANCZOS)
            
            # Converter para PhotoImage
            self.image_preview = ImageTk.PhotoImage(self.current_image)
            
            # Atualizar label
            self.preview_label.config(image=self.image_preview, text="")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar imagem: {str(e)}")
    
    def update_mode(self):
        """Atualiza interface baseado no modo selecionado."""
        if self.mode_var.get() == "manual":
            self.manual_frame.pack(fill=tk.X, pady=5)
        else:
            self.manual_frame.pack_forget()
    
    def generate_preview(self):
        """Gera prévia automática do bordado com as configurações escolhidas."""
        if not self.image_path:
            messagebox.showwarning("Aviso", "Selecione uma imagem primeiro!")
            return
        
        try:
            self.status_var.set("Gerando prévia...")
            self.root.update()
            
            # Carregar imagem original
            original_image = Image.open(self.image_path)
            
            # Converter para RGB se necessário
            if original_image.mode != 'RGB':
                original_image = original_image.convert('RGB')
            
            # Criar regiões a partir da imagem
            self.current_regions = self.extract_regions_from_image(original_image)
            self.current_preview_image = original_image
            
            # Criar visualizador
            self.visualizer = EmbroideryVisualizer()
            
            # Criar janela de prévia
            preview_window = tk.Toplevel(self.root)
            preview_window.title("Prévia do Bordado")
            preview_window.geometry("1000x750")
            
            # Frame principal
            preview_frame = ttk.Frame(preview_window, padding="10")
            preview_frame.pack(fill=tk.BOTH, expand=True)
            
            # Título
            title_frame = ttk.Frame(preview_frame)
            title_frame.pack(fill=tk.X, pady=(0, 10))
            
            ttk.Label(title_frame, text="Prévia do Bordado", 
                     font=("Arial", 14, "bold")).pack(side=tk.LEFT)
            
            # Info de pontos
            total_points = sum(len(r.points) for r in self.current_regions)
            self.stitch_info_var = tk.StringVar(value=f"Regiões: {len(self.current_regions)} | Total de pontos: {total_points}")
            ttk.Label(title_frame, textvariable=self.stitch_info_var, 
                     font=("Arial", 10)).pack(side=tk.RIGHT, padx=10)
            
            # Frame de zoom
            zoom_frame = ttk.Frame(preview_frame)
            zoom_frame.pack(fill=tk.X, pady=(0, 10))
            
            ttk.Label(zoom_frame, text="Zoom:").pack(side=tk.LEFT, padx=5)
            ttk.Button(zoom_frame, text="-", width=3, 
                      command=lambda: self.adjust_preview_zoom(-0.25)).pack(side=tk.LEFT)
            
            self.zoom_var = tk.StringVar(value="100%")
            ttk.Label(zoom_frame, textvariable=self.zoom_var, width=6).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(zoom_frame, text="+", width=3, 
                      command=lambda: self.adjust_preview_zoom(0.25)).pack(side=tk.LEFT)
            ttk.Button(zoom_frame, text="Ajustar", 
                      command=lambda: self.set_preview_zoom(1.0)).pack(side=tk.LEFT, padx=10)
            
            # Modos de visualização
            view_frame = ttk.Frame(preview_frame)
            view_frame.pack(fill=tk.X, pady=(0, 5))
            
            ttk.Label(view_frame, text="Modo:").pack(side=tk.LEFT, padx=5)
            
            self.preview_type_var = tk.StringVar(value="realistic")
            
            modes = [
                ("Realista", "realistic"),
                ("Pontos", "stitch"),
                ("Sólido", "solid"),
                ("Original", "original")
            ]
            
            for text, value in modes:
                ttk.Radiobutton(view_frame, text=text, variable=self.preview_type_var, 
                              value=value, command=self.update_preview_display).pack(side=tk.LEFT, padx=5)
            
            # Separador
            ttk.Separator(view_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
            
            # Grade
            self.show_grid_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(view_frame, text="Grade", variable=self.show_grid_var,
                           command=self.update_preview_display).pack(side=tk.LEFT, padx=5)
            
            # Canvas para prévia com fundo branco
            self.preview_canvas = tk.Canvas(preview_window, bg='white', width=900, height=550)
            self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Variáveis
            self.preview_zoom_level = 1.0
            self.current_preview_images = {}
            
            # Gerar prévias com tamanho fixo
            self.generate_all_previews()
            self.update_preview_display()
            
            # Botões de ação
            btn_frame = ttk.Frame(preview_frame)
            btn_frame.pack(fill=tk.X, pady=(10, 0))
            
            ttk.Button(btn_frame, text="Editar Bordado", 
                      command=lambda: self.open_editor(preview_window)).pack(side=tk.LEFT, padx=(0, 10))
            
            ttk.Button(btn_frame, text="Salvar", 
                      command=lambda: self.save_from_preview()).pack(side=tk.LEFT, padx=(0, 10))
            
            # Simulador
            self.simulator = StitchSimulator(self.current_regions, original_image)
            ttk.Label(btn_frame, text="Simulador:").pack(side=tk.LEFT, padx=(20, 5))
            
            ttk.Button(btn_frame, text="<<", width=3,
                      command=lambda: self.simulate_stitch(-10)).pack(side=tk.LEFT)
            ttk.Button(btn_frame, text=">", width=3,
                      command=lambda: self.simulate_stitch(1)).pack(side=tk.LEFT)
            ttk.Button(btn_frame, text=">>", width=3,
                      command=lambda: self.simulate_stitch(10)).pack(side=tk.LEFT)
            
            self.sim_stitch_var = tk.StringVar(value=f"0/{self.simulator.get_total_stitches()}")
            ttk.Label(btn_frame, textvariable=self.sim_stitch_var).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(btn_frame, text="Fechar", 
                      command=preview_window.destroy).pack(side=tk.RIGHT)
            
            self.status_var.set("Prévia gerada com sucesso")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar prévia: {str(e)}")
            self.status_var.set("Erro ao gerar prévia")
    
    def toggle_stitch_order_panel(self):
        """Mostra/esconde painel de ordem de costura."""
        if self.show_stitch_order_var.get():
            self._show_stitch_order_panel()
        else:
            self._hide_stitch_order_panel()
    
    def _show_stitch_order_panel(self):
        """Mostra painel de ordem de costura."""
        if hasattr(self, 'stitch_order_frame') and self.stitch_order_frame.winfo_exists():
            self.stitch_order_frame.pack(side=tk.RIGHT, fill=tk.Y, before=self.preview_canvas)
            
            # Limpar e preencher
            for widget in self.stitch_order_frame.winfo_children():
                widget.destroy()
            
            ttk.Label(self.stitch_order_frame, text="Ordem de Costura", 
                     font=("Arial", 10, "bold")).pack(pady=5)
            
            # Lista de regiões na ordem de costura
            listbox = tk.Listbox(self.stitch_order_frame, width=25)
            listbox.pack(fill=tk.BOTH, expand=True, padx=5)
            
            for i, region in enumerate(self.current_regions):
                color_hex = f'#{region.color[0]:02x}{region.color[1]:02x}{region.color[2]:02x}'
                listbox.insert(tk.END, f"{i+1}. {region.name or f'Região {region.id}'}")
                listbox.itemconfig(i, fg=color_hex)
    
    def _hide_stitch_order_panel(self):
        """Esconde painel de ordem de costura."""
        if hasattr(self, 'stitch_order_frame') and self.stitch_order_frame.winfo_exists():
            self.stitch_order_frame.pack_forget()
    
    def simulate_stitch(self, delta):
        """Avança/retrocede na simulação de costura."""
        if not hasattr(self, 'simulator'):
            return
        
        new_idx = self.simulator.current_stitch + delta
        new_idx = max(0, min(new_idx, self.simulator.get_total_stitches()))
        self.simulator.current_stitch = new_idx
        
        # Gerar frame da simulação
        canvas_w = self.preview_canvas.winfo_width() or 800
        canvas_h = self.preview_canvas.winfo_height() or 600
        
        frame = self.simulator.get_frame(new_idx, canvas_w, canvas_h)
        
        # Aplicar zoom
        new_size = (int(frame.width * self.preview_zoom_level), 
                   int(frame.height * self.preview_zoom_level))
        frame_zoomed = frame.resize(new_size, Image.Resampling.LANCZOS)
        
        # Mostrar
        photo = ImageTk.PhotoImage(frame_zoomed)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(10, 10, anchor=tk.NW, image=photo)
        self.preview_canvas.image = photo
        
        self.sim_stitch_var.set(f"{new_idx}/{self.simulator.get_total_stitches()}")
    
    def open_editor(self, preview_window):
        """Abre o editor com as regiões geradas automaticamente."""
        try:
            # Fechar janela de prévia
            preview_window.destroy()
            
            # Abrir editor
            editor_window = tk.Toplevel(self.root)
            editor = EmbroideryEditor(editor_window, self.current_preview_image, self.current_regions)
            
            self.status_var.set("Editor aberto - Edite o bordado conforme necessário")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir editor: {str(e)}")
            self.status_var.set("Erro ao abrir editor")
    
    def save_from_preview(self):
        """Salva o bordado diretamente da prévia."""
        formato = self.format_var.get()
        
        pattern = pyembroidery.EmbPattern()
        
        for region in self.current_regions:
            # Adicionar cor
            pattern.add_stitch_absolute(pyembroidery.COLOR_CHANGE, 0, 0)
            
            # Adicionar pontos
            for x, y in region.points:
                pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)
        
        # Solicitar arquivo de saída
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
    
    def adjust_preview_zoom(self, delta):
        """Ajusta o zoom da prévia."""
        self.preview_zoom_level = max(0.25, min(4.0, self.preview_zoom_level + delta))
        self.zoom_var.set(f"{int(self.preview_zoom_level * 100)}%")
        self.update_preview_display()
    
    def set_preview_zoom(self, level):
        """Define zoom específico da prévia."""
        self.preview_zoom_level = level
        self.zoom_var.set(f"{int(self.preview_zoom_level * 100)}%")
        self.update_preview_display()
    
    def on_preview_mouse_wheel(self, event):
        """Lida com scroll do mouse para zoom na prévia."""
        if event.delta > 0:
            self.adjust_preview_zoom(0.1)
        else:
            self.adjust_preview_zoom(-0.1)
    
    def generate_all_previews(self):
        """Gera todos os tipos de prévia."""
        # Usar tamanho fixo para garantir que funcione
        w, h = 900, 550
        
        self.current_preview_images = {
            "realistic": self.visualizer.render_realistic(
                self.current_regions, self.current_preview_image, w, h),
            "stitch": self.visualizer.render_stitch_view(
                self.current_regions, self.current_preview_image, w, h),
            "solid": self.visualizer.render_solid_view(
                self.current_regions, self.current_preview_image, w, h),
            "original": self.current_preview_image.copy()
        }
    
    def update_preview_display(self):
        """Atualiza a exibição da prévia no canvas."""
        # Limpar canvas
        self.preview_canvas.delete("all")
        
        # Obter tipo selecionado
        preview_type = self.preview_type_var.get()
        
        # Regenerar se necessário
        if preview_type not in self.current_preview_images:
            self.generate_all_previews()
        
        if preview_type in self.current_preview_images:
            img = self.current_preview_images[preview_type]
            
            # Aplicar zoom
            new_size = (int(img.width * self.preview_zoom_level), 
                       int(img.height * self.preview_zoom_level))
            img_zoomed = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Converter para PhotoImage
            photo = ImageTk.PhotoImage(img_zoomed)
            
            # Centralizar no canvas
            canvas_width = max(self.preview_canvas.winfo_width(), 900)
            canvas_height = max(self.preview_canvas.winfo_height(), 550)
            
            x = max(0, (canvas_width - new_size[0]) // 2)
            y = max(0, (canvas_height - new_size[1]) // 2)
            
            # Desenhar imagem
            self.preview_canvas.create_image(x, y, anchor=tk.NW, image=photo, tags="preview")
            self.preview_canvas.image = photo  # Manter referência
            
            # Desenhar grade se ativada
            if self.show_grid_var.get():
                self._draw_preview_grid()
    
    def _draw_preview_grid(self):
        """Desenha grade de referência."""
        canvas_width = max(self.preview_canvas.winfo_width(), 900)
        canvas_height = max(self.preview_canvas.winfo_height(), 550)
        
        spacing = 30
        
        for x in range(0, canvas_width, spacing):
            self.preview_canvas.create_line([(x, 0), (x, canvas_height)], 
                                          fill='#cccccc', width=1, tags="grid")
        
        for y in range(0, canvas_height, spacing):
            self.preview_canvas.create_line([(0, y), (canvas_width, y)], 
                                          fill='#cccccc', width=1, tags="grid")
    
    def generate_contours_preview(self):
        """Gera prévia mostrando contornos detectados."""
        width, height = self.current_preview_image.size
        preview_size = (400, 400)
        
        # Criar imagem branca
        preview = Image.new('RGB', preview_size, (255, 255, 255))
        draw = ImageDraw.Draw(preview)
        
        # Converter para escala de cinza
        if self.current_preview_image.mode != 'L':
            gray_img = self.current_preview_image.convert('L')
        else:
            gray_img = self.current_preview_image.copy()
        
        gray_img.thumbnail(preview_size, Image.Resampling.LANCZOS)
        img_array = np.array(gray_img)
        
        # Detectar bordas usando gradiente
        from skimage import feature
        edges = feature.canny(img_array, sigma=2)
        
        # Converter coordenadas
        scale_x = preview_size[0] / gray_img.width
        scale_y = preview_size[1] / gray_img.height
        
        # Desenhar contornos
        for y in range(edges.shape[0]):
            for x in range(edges.shape[1]):
                if edges[y, x]:
                    px = int(x * scale_x)
                    py = int(y * scale_y)
                    draw.point((px, py), fill=(0, 100, 200))
        
        # Adicionar legenda
        draw.text((10, 10), "Azul: Contornos detectados", fill=(0, 100, 200))
        
        return preview
    
    def generate_quantized_preview(self):
        """Gera prévia com cores quantizadas."""
        width, height = self.current_preview_image.size
        preview_size = (400, 400)
        
        # Criar imagem
        preview = Image.new('RGB', preview_size, (255, 255, 255))
        
        # Copiar e redimensionar imagem
        img = self.current_preview_image.copy()
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        img.thumbnail(preview_size, Image.Resampling.LANCZOS)
        
        # Quantizar cores
        img_quantized = img.quantize(colors=6, method=Image.Quantize.MEDIANCUT)
        img_quantized_rgb = img_quantized.convert('RGB')
        
        # Colocar no centro da preview
        position = ((preview_size[0] - img_quantized_rgb.width) // 2,
                   (preview_size[1] - img_quantized_rgb.height) // 2)
        
        preview.paste(img_quantized_rgb, position)
        
        # Adicionar legenda
        draw = ImageDraw.Draw(preview)
        draw.text((10, 10), "6 cores (quantização median cut)", fill=(0, 0, 0))
        
        return preview
    
    def extract_regions_from_image(self, image: Image.Image):
        """Extrai regiões de bordado usando o motor profissional do EmbroideryEngine."""
        if not self.image_path:
            return []

        try:
            from motor_bordado import digitizar
            regioes = digitizar(
                self.image_path,
                max_colors=6,
                density=self.density_var.get() if hasattr(self, 'density_var') else 0.4,
            )
            return regioes
        except Exception as e:
            print(f"[motor_bordado] erro ao digitalizar: {e}")
            # Fallback para o método antigo em caso de falha
            return self._extract_regions_legacy(image)

    def _extract_regions_legacy(self, image: Image.Image):
        """Método antigo de extração de regiões (fallback)."""
        from skimage import measure
        import numpy as np

        # Quantizar cores
        img_quantized = image.quantize(colors=6, method=Image.Quantize.MEDIANCUT)
        img_quantized_array = np.array(img_quantized)
        palette = img_quantized.getpalette()

        regions = []
        region_id = 0

        colors = np.unique(img_quantized_array)

        for color_idx in colors:
            # Criar máscara para esta cor
            mask = (img_quantized_array == color_idx)

            # Detectar componentes conectados
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

        return regions
    
    def generate_realistic_preview(self):
        """Gera prévia realista simulando bordado em tecido com cores."""
        # Criar imagem de tecido
        width, height = self.current_image.size
        fabric_size = (400, 400)
        
        # Criar tecido com textura
        fabric = Image.new('RGB', fabric_size, (240, 230, 220))  # Cor de tecido
        draw = ImageDraw.Draw(fabric)
        
        # Adicionar textura ao tecido
        for i in range(0, fabric_size[0], 4):
            for j in range(0, fabric_size[1], 4):
                if (i + j) % 8 == 0:
                    draw.point((i, j), fill=(235, 225, 215))
        
        # Redimensionar imagem original
        embroidered_size = (min(300, width), min(300, height))
        embroidered_img = self.current_image.copy()
        embroidered_img.thumbnail(embroidered_size, Image.Resampling.LANCZOS)
        
        # Converter para RGB se necessário
        if embroidered_img.mode != 'RGB':
            embroidered_img = embroidered_img.convert('RGB')
        
        # Quantizar cores para simular bordado com fios
        img_quantized = embroidered_img.quantize(colors=6, method=Image.Quantize.MEDIANCUT)
        img_quantized_rgb = img_quantized.convert('RGB')
        
        # Criar máscara de transparência (fundo branco = transparente)
        img_array = np.array(img_quantized_rgb)
        luminance = 0.299 * img_array[:,:,0] + 0.587 * img_array[:,:,1] + 0.114 * img_array[:,:,2]
        mask = (luminance > 240)  # Fundo branco
        
        # Criar imagem com transparência
        embroidered_rgba = img_quantized_rgb.copy()
        embroidered_array = np.array(embroidered_rgba)
        embroidered_array[mask] = [240, 230, 220]  # Cor do tecido onde transparente
        
        # Converter de volta para PIL
        embroidered_final = Image.fromarray(embroidered_array)
        
        # Colocar o bordado no tecido
        position = ((fabric_size[0] - embroidered_size[0]) // 2,
                   (fabric_size[1] - embroidered_size[1]) // 2)
        
        # Criar imagem final
        result = fabric.copy()
        result.paste(embroidered_final, position)
        
        # Adicionar sombra para efeito 3D
        shadow = result.copy()
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=3))
        
        # Combinar com sombra
        final = Image.blend(result, shadow, 0.3)
        
        return final
    
    def generate_wireframe_preview(self):
        """Gera prévia wireframe mostrando caminhos dos pontos."""
        # Criar imagem branca
        width, height = self.current_image.size
        wireframe_size = (400, 400)
        
        # Criar imagem branca
        wireframe = Image.new('RGB', wireframe_size, (255, 255, 255))
        draw = ImageDraw.Draw(wireframe)
        
        # Converter imagem original para escala de cinza
        if self.current_image.mode != 'L':
            gray_img = self.current_image.convert('L')
        else:
            gray_img = self.current_image.copy()
        
        # Redimensionar
        gray_img.thumbnail((300, 300), Image.Resampling.LANCZOS)
        pixels = gray_img.load()
        
        # Configurações baseadas na qualidade
        quality_settings = self.qualidades[self.quality_var.get()]
        step = quality_settings["step"]
        
        # Desenhar caminhos dos pontos
        points = []
        for y in range(0, gray_img.height, step):
            for x in range(0, gray_img.width, step):
                pixel = pixels[x, y]
                if pixel < 128:  # Pixel escuro = ponto de bordado
                    # Converter coordenadas para o tamanho da prévia
                    px = int(x * wireframe_size[0] / gray_img.width)
                    py = int(y * wireframe_size[1] / gray_img.height)
                    points.append((px, py))
        
        # Desenhar linhas conectando os pontos
        if len(points) > 1:
            # Conectar pontos adjacentes
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                
                # Calcular distância
                dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                
                # Só conectar se estiverem próximos
                if dist < 20:
                    draw.line([(x1, y1), (x2, y2)], fill=(0, 0, 255), width=1)
            
            # Desenhar pontos
            for px, py in points:
                draw.ellipse([(px-2, py-2), (px+2, py+2)], fill=(255, 0, 0))
        
        # Adicionar legendas
        draw.text((10, 10), "Vermelho: Pontos de bordado", fill=(255, 0, 0))
        draw.text((10, 30), "Azul: Caminhos de costura", fill=(0, 0, 255))
        
        return wireframe
    
    def convert_image(self):
        """Converte imagem para arquivo de bordado."""
        if not self.image_path:
            messagebox.showwarning("Aviso", "Selecione uma imagem primeiro!")
            return
        
        try:
            self.status_var.set("Convertendo...")
            self.root.update()
            
            # Carregar imagem original para conversão
            original_image = Image.open(self.image_path)
            
            # Converter para escala de cinza para simplificar
            if original_image.mode != 'L':
                original_image = original_image.convert('L')
            
            # Criar padrão de bordado
            pattern = pyembroidery.EmbPattern()
            
            # Configurar baseado no modo
            if self.mode_var.get() == "auto":
                # Modo automático: usar o motor profissional do EmbroideryEngine
                self.auto_convert_profissional(pattern)
            else:
                # Modo manual: usar configurações do usuário
                self.manual_convert(original_image, pattern)
            
            # Aplicar reforço se ativado
            if self.reinforcement_var.get():
                self.apply_reinforcement(pattern)
            
            # Solicitar arquivo de saída
            formato = self.format_var.get()
            filetypes = [(f"Arquivo de bordado (*.{formato.lower()})", f"*.{formato.lower()}")]
            
            output_path = filedialog.asksaveasfilename(
                title="Salvar Arquivo de Bordado",
                defaultextension=f".{formato.lower()}",
                filetypes=filetypes
            )
            
            if output_path:
                # Salvar arquivo
                write_func = getattr(pyembroidery, f"write_{formato.lower()}")
                write_func(pattern, output_path)
                
                self.status_var.set(f"Arquivo salvo: {os.path.basename(output_path)}")
                messagebox.showinfo("Sucesso", 
                                   f"Arquivo de bordado salvo com sucesso!\n\n"
                                   f"Formato: {formato}\n"
                                   f"Arquivo: {os.path.basename(output_path)}\n"
                                   f"Qualidade: {self.quality_var.get()}\n"
                                   f"Reforço: {'Sim' if self.reinforcement_var.get() else 'Não'}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na conversão: {str(e)}")
            self.status_var.set("Erro na conversão")
    
    def auto_convert_profissional(self, pattern):
        """Conversão automática usando o motor profissional do EmbroideryEngine."""
        from motor_bordado import digitizar

        regioes = digitizar(
            self.image_path,
            max_colors=6,
            density=self.density_var.get() if hasattr(self, 'density_var') else 0.4,
        )

        for region in regioes:
            # Mudança de cor
            pattern.add_stitch_absolute(pyembroidery.COLOR_CHANGE, 0, 0)
            # Pontos reais otimizados
            for x, y in region.points:
                pattern.add_stitch_absolute(pyembroidery.STITCH, x, y)

    def auto_convert(self, image, pattern):
        """Conversão automática usando quantização de cores e componentes conectados."""
        # Converter imagem para RGB se necessário
        if image.mode != 'RGB':
            img_rgb = image.convert('RGB')
        else:
            img_rgb = image.copy()
        
        # Obter configurações de qualidade
        quality_settings = self.qualidades[self.quality_var.get()]
        step = quality_settings["step"]
        
        # Configurar precisão
        precision_settings = {
            "Baixa": 0.5,
            "Normal": 1.0,
            "Alta": 1.5,
            "Muito Alta": 2.0
        }
        precision = precision_settings[self.precision_var.get()]
        
        # Escala para mm (assumindo 72 DPI)
        scale = (25.4 / 72.0) * precision
        
        # 1. Quantização de cores: reduzir paleta para 6 cores
        img_quantized = img_rgb.quantize(colors=6, method=Image.Quantize.MEDIANCUT)
        
        # Converter para array numpy
        img_array = np.array(img_quantized)
        
        # Obter paleta de cores
        palette = img_quantized.getpalette()
        
        # 2. Para cada cor, criar regiões e gerar fill stitches
        for color_idx in range(6):
            # Criar máscara para esta cor
            mask = (img_array == color_idx)
            
            # 3. Detectar componentes conectados
            labeled = measure.label(mask)
            regions = measure.regionprops(labeled)
            
            # 4. Para cada região, gerar preenchimento
            for region in regions:
                # Obter bounding box
                minr, minc, maxr, maxc = region.bbox
                
                # Ignorar regiões muito pequenas
                if (maxr - minr) < 2 or (maxc - minc) < 2:
                    continue
                
                # Gerar preenchimento horizontal
                self.generate_fill_stitch(pattern, mask, minr, minc, maxr, maxc, 
                                        scale, step, color_idx, palette)
    
    def generate_fill_stitch(self, pattern, mask, minr, minc, maxr, maxc, scale, step, color_idx, palette):
        """Gera preenchimento horizontal para uma região."""
        # Converter cor RGB da paleta
        r = palette[color_idx * 3]
        g = palette[color_idx * 3 + 1]
        b = palette[color_idx * 3 + 2]
        
        # Adicionar mudança de cor
        pattern.add_stitch_absolute(pyembroidery.COLOR_CHANGE, 0, 0)
        
        # Gerar linhas horizontais de preenchimento
        for y in range(minr, maxr, step):
            # Encontrar início e fim da linha nesta regiõ
            x_start = minc
            x_end = maxc
            
            # Ajustar para pixels da cor atual
            while x_start < x_end and not mask[y, x_start]:
                x_start += 1
            while x_end > x_start and not mask[y, x_end - 1]:
                x_end -= 1
            
            if x_start < x_end:
                # Converter coordenadas para mm
                px_start = x_start * scale
                px_end = (x_end - 1) * scale
                py = y * scale
                
                # Adicionar ponto inicial
                pattern.add_stitch_absolute(pyembroidery.STITCH, px_start, py)
                
                # Adicionar pontos intermediários
                num_stitches = max(1, int((px_end - px_start) / scale))
                for i in range(1, num_stitches):
                    px = px_start + (px_end - px_start) * i / num_stitches
                    pattern.add_stitch_absolute(pyembroidery.STITCH, px, py)
    
    def manual_convert(self, image, pattern):
        """Conversão manual usando configurações do usuário."""
        width, height = image.size
        pixels = image.load()
        
        # Obter configurações do usuário
        density = self.density_var.get()
        stitch_type = self.stitch_var.get()
        target_width = self.width_var.get()
        
        # Calcular escala
        scale = target_width / width
        
        # Determinar tipo de ponto
        stitch_cmd = pyembroidery.STITCH
        if stitch_type == "satin":
            stitch_cmd = pyembroidery.STITCH
        elif stitch_type == "running":
            stitch_cmd = pyembroidery.STITCH
        
        # Criar pontos de bordado
        step = max(1, int(3 / density))
        
        for y in range(0, height, step):
            for x in range(0, width, step):
                pixel = pixels[x, y]
                # Ajustar threshold baseado na densidade
                threshold = 128 * (1 - density * 0.5)
                if pixel < threshold:
                    # Converter coordenadas
                    px = x * scale
                    py = y * scale
                    pattern.add_stitch_absolute(stitch_cmd, px, py)
        
        # Finalizar padrão
    
    def apply_reinforcement(self, pattern):
        """Aplica reforço ao bordado para torná-lo mais cheio e com relevo grosso."""
        if not self.reinforcement_var.get():
            return
        
        # Obter configurações de reforço
        reinforcement_type = self.reinforcement_type_var.get()
        thickness = self.thickness_var.get()
        
        # Aplicar reforço baseado no tipo
        if reinforcement_type == "Satin Denso":
            # Adicionar pontos extras para preencher áreas
            self.apply_satin_reinforcement(pattern, thickness)
        elif reinforcement_type == "Fill Triplo":
            # Triplicar pontos em áreas existentes
            self.apply_triple_fill(pattern, thickness)
        elif reinforcement_type == "Cadeia Grossa":
            # Adicionar pontos de cadeia grossa
            self.apply_chain_reinforcement(pattern, thickness)
    
    def apply_satin_reinforcement(self, pattern, thickness):
        """Aplica reforço satin denso."""
        # Criar pontos extras ao redor dos pontos existentes
        new_stitches = []
        
        for stitch in pattern.stitches:
            x, y, cmd = stitch
            if cmd == pyembroidery.STITCH:
                # Adicionar pontos ao redor
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        if dx != 0 or dy != 0:
                            new_x = x + dx * thickness * 0.5
                            new_y = y + dy * thickness * 0.5
                            new_stitches.append((new_x, new_y, cmd))
        
        # Adicionar novos pontos ao padrão
        for stitch in new_stitches:
            pattern.add_stitch_absolute(stitch[2], stitch[0], stitch[1])
    
    def apply_triple_fill(self, pattern, thickness):
        """Aplica reforço fill triplo."""
        # Triplicar cada ponto com deslocamento
        new_stitches = []
        
        for stitch in pattern.stitches:
            x, y, cmd = stitch
            if cmd == pyembroidery.STITCH:
                # Original
                new_stitches.append((x, y, cmd))
                
                # Cópia 1 com deslocamento
                new_stitches.append((x + thickness * 0.3, y, cmd))
                
                # Cópia 2 com deslocamento
                new_stitches.append((x, y + thickness * 0.3, cmd))
        
        # Limpar padrão original e adicionar novos pontos
        pattern.stitches = []
        for stitch in new_stitches:
            pattern.add_stitch_absolute(stitch[2], stitch[0], stitch[1])
    
    def apply_chain_reinforcement(self, pattern, thickness):
        """Aplica reforço de cadeia grossa."""
        # Adicionar pontos de cadeia entre os pontos existentes
        new_stitches = []
        
        for i, stitch in enumerate(pattern.stitches):
            x, y, cmd = stitch
            if cmd == pyembroidery.STITCH:
                new_stitches.append((x, y, cmd))
                
                # Adicionar ponto intermediário se não for o último
                if i < len(pattern.stitches) - 1:
                    next_x, next_y, _ = pattern.stitches[i + 1]
                    mid_x = (x + next_x) / 2
                    mid_y = (y + next_y) / 2
                    new_stitches.append((mid_x, mid_y, cmd))
        
        # Limpar padrão original e adicionar novos pontos
        pattern.stitches = []
        for stitch in new_stitches:
            pattern.add_stitch_absolute(stitch[2], stitch[0], stitch[1])


def main():
    root = tk.Tk()
    app = ConversorBordado(root)
    root.mainloop()


if __name__ == "__main__":
    main()