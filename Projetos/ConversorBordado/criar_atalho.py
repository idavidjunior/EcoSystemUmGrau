#!/usr/bin/env python3
"""Cria atalho na área de trabalho para o Conversor de Bordado."""

import os
import winshell
from win32com.client import Dispatch

def criar_atalho():
    """Cria atalho na área de desktop."""
    desktop = winshell.desktop()
    caminho_atalho = os.path.join(desktop, "Conversor de Bordado.lnk")
    
    caminho_script = os.path.abspath("conversor.py")
    caminho_python = r"C:\Users\David Jr\AppData\Local\Programs\Python\Python312\python.exe"
    caminho_icone = os.path.abspath("icon.ico")
    
    shell = Dispatch('WScript.Shell')
    atalho = shell.CreateShortCut(caminho_atalho)
    atalho.Targetpath = caminho_python
    atalho.Arguments = f'"{caminho_script}"'
    atalho.WorkingDirectory = os.path.dirname(caminho_script)
    atalho.IconLocation = f"{caminho_icone},0"
    atalho.Description = "Conversor de Imagem para Bordado"
    atalho.save()
    
    print(f"Atalho criado: {caminho_atalho}")

if __name__ == "__main__":
    criar_atalho()