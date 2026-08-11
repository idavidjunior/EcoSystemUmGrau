' scripts/controle.vbs — launcher invisible do widget Controle Jarvis.
' Roda python.exe sem janela de console (equivalente a CREATE_NO_WINDOW),
' evitando o pythonw.exe (broken neste ambiente) e o console preto.
Set sh = CreateObject("WScript.Shell")
cmd = "python.exe -u ""C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\widget_controle_jarvis.py"""
sh.Run cmd, 0, False  ' 0=SW_HIDE (janela invisivel), False=nao bloquear
