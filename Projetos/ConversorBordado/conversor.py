#!/usr/bin/env python3
"""
Conversor de Imagem para Bordado
Interface desktop para converter imagens em arquivos de bordado.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import pyembroidery
import os
from pathlib import Path
import math


class ConversorBordado:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor de Imagem para Bordado")
        self.root.geometry("1000x700")
        
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
        """Gera prévia do bordado antes de salvar."""
        if not self.image_path:
            messagebox.showwarning("Aviso", "Selecione uma imagem primeiro!")
            return
        
        try:
            self.status_var.set("Gerando prévia...")
            self.root.update()
            
            # Criar janela de prévia
            preview_window = tk.Toplevel(self.root)
            preview_window.title("Prévia do Bordado")
            preview_window.geometry("800x600")
            
            # Frame principal da prévia
            preview_frame = ttk.Frame(preview_window, padding="10")
            preview_frame.pack(fill=tk.BOTH, expand=True)
            
            # Título
            title = ttk.Label(preview_frame, text="Prévia do Bordado", 
                             font=("Arial", 14, "bold"))
            title.pack(pady=(0, 10))
            
            # Frame para as duas prévias
            previews_frame = ttk.Frame(preview_frame)
            previews_frame.pack(fill=tk.BOTH, expand=True)
            
            # Prévia 1: Realista (simulando tecido)
            realistic_frame = ttk.LabelFrame(previews_frame, text="Prévia Realista (Simulação de Tecido)", padding="5")
            realistic_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
            
            # Gerar prévia realista
            realistic_preview = self.generate_realistic_preview()
            realistic_photo = ImageTk.PhotoImage(realistic_preview)
            
            realistic_label = ttk.Label(realistic_frame, image=realistic_photo)
            realistic_label.image = realistic_photo  # Manter referência
            realistic_label.pack(fill=tk.BOTH, expand=True)
            
            # Prévia 2: Wireframe (caminhos dos pontos)
            wireframe_frame = ttk.LabelFrame(previews_frame, text="Prévia Wireframe (Caminhos dos Pontos)", padding="5")
            wireframe_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
            
            # Gerar prévia wireframe
            wireframe_preview = self.generate_wireframe_preview()
            wireframe_photo = ImageTk.PhotoImage(wireframe_preview)
            
            wireframe_label = ttk.Label(wireframe_frame, image=wireframe_photo)
            wireframe_label.image = wireframe_photo  # Manter referência
            wireframe_label.pack(fill=tk.BOTH, expand=True)
            
            # Botão de fechar
            close_btn = ttk.Button(preview_frame, text="Fechar", 
                                  command=preview_window.destroy)
            close_btn.pack(pady=(10, 0))
            
            self.status_var.set("Prévia gerada com sucesso")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar prévia: {str(e)}")
            self.status_var.set("Erro ao gerar prévia")
    
    def generate_realistic_preview(self):
        """Gera prévia realista simulando bordado em tecido."""
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
        
        # Redimensionar imagem original para o tamanho do bordado
        embroidered_size = (min(300, width), min(300, height))
        embroidered_img = self.current_image.copy()
        embroidered_img.thumbnail(embroidered_size, Image.Resampling.LANCZOS)
        
        # Converter para escala de cinza se necessário
        if embroidered_img.mode != 'L':
            embroidered_img = embroidered_img.convert('L')
        
        # Criar máscara do bordado
        mask = embroidered_img.point(lambda p: 255 if p < 128 else 0)
        
        # Aplicar efeito de bordado na imagem
        embroidered_rgb = Image.new('RGB', embroidered_img.size, (0, 100, 200))  # Cor do fio
        embroidered_rgb.putalpha(mask)
        
        # Colocar o bordado no tecido
        position = ((fabric_size[0] - embroidered_size[0]) // 2,
                   (fabric_size[1] - embroidered_size[1]) // 2)
        
        # Criar imagem final
        result = fabric.copy()
        result.paste(embroidered_rgb, position, embroidered_rgb)
        
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
                # Modo automático: usar configurações de qualidade
                self.auto_convert(original_image, pattern)
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
    
    def auto_convert(self, image, pattern):
        """Conversão automática usando configurações de qualidade."""
        width, height = image.size
        pixels = image.load()
        
        # Obter configurações de qualidade
        quality_settings = self.qualidades[self.quality_var.get()]
        density = quality_settings["density"]
        step = quality_settings["step"]
        
        # Configurar precisão
        precision_settings = {
            "Baixa": 0.5,
            "Normal": 1.0,
            "Alta": 1.5,
            "Muito Alta": 2.0
        }
        precision = precision_settings[self.precision_var.get()]
        
        # Escala para mm (assumindo 72 DPI para simplificação)
        scale = (25.4 / 72.0) * precision
        
        # Criar pontos de bordado baseados nos pixels escuros
        for y in range(0, height, step):
            for x in range(0, width, step):
                pixel = pixels[x, y]
                # Se pixel escuro, adicionar ponto
                if pixel < 128:
                    # Converter coordenadas para mm
                    px = x * scale
                    py = y * scale
                    pattern.add_stitch_absolute(pyembroidery.STITCH, px, py)
        
        # Finalizar padrão
    
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