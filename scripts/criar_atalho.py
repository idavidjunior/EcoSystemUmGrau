#!/usr/bin/env python3
import os
import win32com.client

desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
shortcut_path = os.path.join(desktop, 'Jarvis Controle.lnk')
target = r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\widget_controle_jarvis.py'
work_dir = r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau'

# Create the shortcut
shell = win32com.client.Dispatch('WScript.Shell')
shortcut = shell.CreateShortcut(shortcut_path)
shortcut.Targetpath = target
shortcut.WorkingDirectory = work_dir
shortcut.WindowStyle = 7  # Normal window
shortcut.save()

print('Atalho criado em:', shortcut_path)