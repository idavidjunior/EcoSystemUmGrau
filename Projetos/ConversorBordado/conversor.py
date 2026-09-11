#!/usr/bin/env python3
"""
Conversor de Imagem para Bordado
Interface desktop para converter imagens em arquivos de bordado.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import pyembroidery
import os
from pathlib import Path


class ConversorBordado:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor de Imagem para Bordado")
        self.root.geometry("800x600")
        
        # Variáveis
        self.image_path = None
        self.image_preview = None
        self.current_image = None
        
        # Formatos suportados
        self.formatos = {
            "DST": "Tajima",
            "PES": "Brother",
            "JEF": "Janome",
            "EXP": "Melco",
            "XXX": "UFAC"
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
        
        # Preview da imagem
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
        
        # Frame de exportação
        export_frame = ttk.LabelFrame(config_frame, text="Exportação", padding="10")
        export_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(export_frame, text="Formato de Saída:").pack(anchor=tk.W)
        self.format_var = tk.StringVar(value="DST")
        format_combo = ttk.Combobox(export_frame, textvariable=self.format_var,
                                   values=list(self.formatos.keys()), state="readonly")
        format_combo.pack(fill=tk.X, pady=2)
        
        # Botão de conversão
        convert_btn = ttk.Button(export_frame, text="Converter e Salvar", 
                                command=self.convert_image)
        convert_btn.pack(pady=10, fill=tk.X)
        
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
            self.current_image = Image.open(path)
            
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
                # Modo automático: usar configurações padrão
                self.auto_convert(original_image, pattern)
            else:
                # Modo manual: usar configurações do usuário
                self.manual_convert(original_image, pattern)
            
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
                                   f"Arquivo: {os.path.basename(output_path)}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na conversão: {str(e)}")
            self.status_var.set("Erro na conversão")
    
    def auto_convert(self, image, pattern):
        """Conversão automática usando configurações padrão."""
        # Converter imagem para pontos de bordado simples
        width, height = image.size
        pixels = image.load()
        
        # Escala para mm (assumindo 72 DPI para simplificação)
        scale = 25.4 / 72.0
        
        # Criar pontos de bordado baseados nos pixels escuros
        step = 3  # Pular pixels para simplificar
        
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
        
        # Adicionar finalização
        pattern.add_command(pyembroidery.COMMAND_STOP)


def main():
    root = tk.Tk()
    app = ConversorBordado(root)
    root.mainloop()


if __name__ == "__main__":
    main()