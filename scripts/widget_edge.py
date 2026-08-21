#!/usr/bin/env python3
"""widget_edge.py - Widget flutuante Edge do EcoSystemUmGrau"""

import sys
import os
import json
import time
import threading
from pathlib import Path

# Add scripts to path
sys.path.insert(0, r"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts")

# Constants
EDGE_TITLE = "Edge - EcoSystemUmGrau"
BG = "#1e1e2e"
S_B = "#313244"
IN = "#181825"
TX = "#cdd6f4"
TX2 = "#a6adc8"
TX3 = "#6c7086"
ON = "#a6e3a1"
OFF = "#f38ba8"
ACC = "#89b4fa"

print("Widget Edge inicializado")
print("EDGE_TITLE: " + EDGE_TITLE)
path_checked = os.path.exists(r"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts")
print("PATH verificado: " + str(path_checked))