#!/usr/bin/env python3
"""Launch the Edge widget"""

import sys
import os

# Add paths
sys_path = r"C:\Users\David Jr\AppData\Local\Programs\Python\Python312\Lib\site-packages"
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

# Try to import pywebview
try:
    import pywebview
    print("pywebview importado com sucesso")
    print("Versão:", pywebview.__version__)
    
    # Import our widget
    sys.path.insert(0, r"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts")
    import widget_edge
    
    # Launch the widget
    print("Lançando widget Edge...")
    view = pywebview.create_window(
        widget_edge.EDGE_TITLE,
        url="file:///C:/Users/David Jr/Documents/Default Project/EcoSystemUmGrau/www/index.html",
        width=400,
        height=600,
        resizable=True,
        frameless=True,
        easy_drag=True,
        focus=False,
        on_top=True,
        background_color="#1e1e2e"
    )
    
    print("Widget Edge lançado com sucesso!")
    print("Feche a janela para terminar.")
    
    # Start the event loop
    pywebview.start()
    
except ModuleNotFoundError as e:
    print("Módulo pywebview não disponível neste ambiente")
    print("Erro: " + str(e))
    print()
    print("Arquivos do widget criado:")
    print("  - scripts/widget_edge.py")
    print("  - www/index.html")
    print("  - www/style.css")
    print("  - www/app.js")
    print()
    print("Para executar, instale pywebview: pip install pywebview")
    print("ou execute manualmente o HTML em um navegador.")
    
except Exception as e:
    print("Erro inesperado: " + str(e))
    print()
    print("Arquivos do widget criado:")
    print("  - scripts/widget_edge.py")
    print("  - www/index.html")
    print("  - www/style.css")
    print("  - www/app.js")
"